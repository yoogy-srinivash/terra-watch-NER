"""
TerraWatch NER - Temporal Fusion Transformer (TFT) Native PyTorch Model
Implements the canonical TFT architecture (Lim et al., 2021):
- Gated Linear Units (GLU)
- Gated Residual Networks (GRN) with optional static context
- Variable Selection Networks (VSN) for past and future covariates
- Temporal LSTM Sequence Encoder/Decoder
- Interpretable Multi-Head Self-Attention with shared value projections
- Multi-Quantile Prediction Heads (p10, p50, p90) for Soil Moisture & Pore Pressure
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class GatedLinearUnit(nn.Module):
    """Gated Linear Unit (GLU): GLU(x) = x_val * sigmoid(x_gate)"""
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.fc = nn.Linear(input_dim, output_dim * 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        val, gate = self.fc(x).chunk(2, dim=-1)
        return val * torch.sigmoid(gate)


class GatedResidualNetwork(nn.Module):
    """
    Gated Residual Network (GRN):
    Provides non-linear processing with gating and residual skip connection.
    Optionally conditioned on static context vector c.
    """
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        context_dim: Optional[int] = None,
        dropout: float = 0.1
    ):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.context_fc = nn.Linear(context_dim, hidden_dim, bias=False) if context_dim else None
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.glu = GatedLinearUnit(hidden_dim, output_dim)
        self.layer_norm = nn.LayerNorm(output_dim)
        self.skip_fc = nn.Linear(input_dim, output_dim) if input_dim != output_dim else None

    def forward(self, x: torch.Tensor, context: Optional[torch.Tensor] = None) -> torch.Tensor:
        residual = self.skip_fc(x) if self.skip_fc is not None else x
        
        h = self.fc1(x)
        if self.context_fc is not None and context is not None:
            # Expand context if dimensions differ (e.g. sequence length)
            if context.dim() == 2 and x.dim() == 3:
                context = context.unsqueeze(1).expand(-1, x.size(1), -1)
            h = h + self.context_fc(context)
        
        h = F.elu(h)
        h = self.fc2(h)
        h = self.dropout(h)
        gated = self.glu(h)
        return self.layer_norm(residual + gated)


class VariableSelectionNetwork(nn.Module):
    """
    Variable Selection Network (VSN):
    Computes feature-wise gating weights to isolate relevant variables dynamically.
    """
    def __init__(
        self,
        num_features: int,
        input_dim: int,
        hidden_dim: int,
        context_dim: Optional[int] = None,
        dropout: float = 0.1
    ):
        super().__init__()
        self.num_features = num_features
        # Individual single-variable feature encoders
        self.feature_grns = nn.ModuleList([
            GatedResidualNetwork(input_dim, hidden_dim, hidden_dim, context_dim=None, dropout=dropout)
            for _ in range(num_features)
        ])
        # Selection weight generator
        self.flattened_grn = GatedResidualNetwork(
            num_features * input_dim, hidden_dim, num_features, context_dim=context_dim, dropout=dropout
        )

    def forward(self, features: List[torch.Tensor], context: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            features: list of K tensors, each of shape (B, T, input_dim) or (B, input_dim)
            context: optional static context vector of shape (B, context_dim)
        Returns:
            weighted_features: (B, T, hidden_dim) or (B, hidden_dim)
            weights: (B, T, num_features) or (B, num_features)
        """
        # Concatenate across feature dimensions
        flat_input = torch.cat(features, dim=-1)
        weights = F.softmax(self.flattened_grn(flat_input, context), dim=-1)
        
        # Process each variable through its own GRN
        processed = [grn(feat) for grn, feat in zip(self.feature_grns, features)]
        stacked = torch.stack(processed, dim=-2)  # (B, [T], K, hidden_dim)
        
        # Weighted sum across features
        expanded_weights = weights.unsqueeze(-1)  # (B, [T], K, 1)
        weighted = (stacked * expanded_weights).sum(dim=-2)  # (B, [T], hidden_dim)
        return weighted, weights


class InterpretableMultiHeadAttention(nn.Module):
    """
    Interpretable Multi-Head Self-Attention:
    Shares the Value matrix V across heads to yield directly interpretable attention weights.
    """
    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads

        self.q_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        # Shared value projection across heads for interpretability
        self.v_linear = nn.Linear(d_model, self.d_head)
        self.out_linear = nn.Linear(self.d_head, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        batch_size, seq_len, _ = query.size()
        
        # Project queries and keys: (B, n_heads, seq_len, d_head)
        q = self.q_linear(query).view(batch_size, -1, self.n_heads, self.d_head).transpose(1, 2)
        k = self.k_linear(key).view(batch_size, -1, self.n_heads, self.d_head).transpose(1, 2)
        # Shared value: (B, seq_len, d_head)
        v = self.v_linear(value)
        
        # Scaled dot-product attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_head)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Average attention weights across heads for interpretability: (B, seq_len, seq_len)
        interp_attn = attn_weights.mean(dim=1)
        
        # Compute head outputs: (B, n_heads, seq_len, d_head) with shared v
        # We broadcast v across n_heads
        v_expanded = v.unsqueeze(1).expand(-1, self.n_heads, -1, -1)
        head_outputs = torch.matmul(attn_weights, v_expanded)  # (B, n_heads, seq_len, d_head)
        
        # Combine heads (average over heads): (B, seq_len, d_head)
        combined = head_outputs.mean(dim=1)
        output = self.out_linear(combined)
        return output, interp_attn


class TemporalFusionTransformer(nn.Module):
    """
    Complete Temporal Fusion Transformer for Multivariate Multi-Horizon Forecasting:
    - Forecasts Soil Moisture (%) and Pore Water Pressure (kPa)
    - Quantile predictions: [p10, p50, p90]
    """
    def __init__(
        self,
        static_cat_cardinalities: Dict[str, int],  # e.g. {'sensor_id': 32, 'state': 8}
        num_static_continuous: int = 2,            # elevation_m, slope_angle_deg
        num_past_continuous: int = 4,              # soil_moisture, pore_pressure, temp, vibration
        num_future_continuous: int = 2,            # hour_of_day, day_of_week
        hidden_dim: int = 32,
        num_heads: int = 2,
        lstm_layers: int = 1,
        dropout: float = 0.1,
        quantiles: List[float] = [0.1, 0.5, 0.9]
    ):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.quantiles = quantiles
        self.num_quantiles = len(quantiles)

        # 1. Static Feature Encoders
        self.static_cat_embeds = nn.ModuleDict({
            name: nn.Embedding(card, hidden_dim)
            for name, card in static_cat_cardinalities.items()
        })
        self.static_cont_fcs = nn.ModuleList([
            nn.Linear(1, hidden_dim) for _ in range(num_static_continuous)
        ])
        num_total_static = len(static_cat_cardinalities) + num_static_continuous
        self.static_vsn = VariableSelectionNetwork(
            num_features=num_total_static,
            input_dim=hidden_dim,
            hidden_dim=hidden_dim,
            dropout=dropout
        )
        self.static_context_grn = GatedResidualNetwork(hidden_dim, hidden_dim, hidden_dim, dropout=dropout)

        # 2. Past Observed Feature Encoders
        self.past_cont_fcs = nn.ModuleList([
            nn.Linear(1, hidden_dim) for _ in range(num_past_continuous)
        ])
        self.past_vsn = VariableSelectionNetwork(
            num_features=num_past_continuous,
            input_dim=hidden_dim,
            hidden_dim=hidden_dim,
            context_dim=hidden_dim,
            dropout=dropout
        )

        # 3. Future Known Feature Encoders
        self.future_cont_fcs = nn.ModuleList([
            nn.Linear(1, hidden_dim) for _ in range(num_future_continuous)
        ])
        self.future_vsn = VariableSelectionNetwork(
            num_features=num_future_continuous,
            input_dim=hidden_dim,
            hidden_dim=hidden_dim,
            context_dim=hidden_dim,
            dropout=dropout
        )

        # 4. LSTM Sequence Processing
        self.lstm_encoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout if lstm_layers > 1 else 0.0
        )
        self.lstm_decoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout if lstm_layers > 1 else 0.0
        )

        # Skip connection & gating for sequence layer
        self.seq_glu = GatedLinearUnit(hidden_dim, hidden_dim)
        self.seq_norm = nn.LayerNorm(hidden_dim)

        # 5. Static Enrichment
        self.enrichment_grn = GatedResidualNetwork(
            hidden_dim, hidden_dim, hidden_dim, context_dim=hidden_dim, dropout=dropout
        )

        # 6. Interpretable Multi-Head Self-Attention
        self.self_attn = InterpretableMultiHeadAttention(hidden_dim, num_heads, dropout=dropout)
        self.attn_norm = nn.LayerNorm(hidden_dim)
        self.post_attn_grn = GatedResidualNetwork(hidden_dim, hidden_dim, hidden_dim, dropout=dropout)

        # 7. Final Multi-Target Quantile Heads: Soil Moisture and Pore Pressure
        # Each outputs (num_quantiles)
        self.moisture_head = nn.Linear(hidden_dim, self.num_quantiles)
        self.pore_p_head = nn.Linear(hidden_dim, self.num_quantiles)

    def forward(
        self,
        static_cats: Dict[str, torch.Tensor],     # e.g. {'sensor_id': (B,), 'state': (B,)}
        static_conts: torch.Tensor,               # (B, num_static_cont)
        past_conts: torch.Tensor,                 # (B, T_past, num_past_cont)
        future_conts: torch.Tensor                # (B, T_future, num_future_cont)
    ) -> Dict[str, torch.Tensor]:
        batch_size = past_conts.size(0)
        t_past = past_conts.size(1)
        t_future = future_conts.size(1)

        # 1. Process Static Features
        static_features = []
        for name, emb_layer in self.static_cat_embeds.items():
            static_features.append(emb_layer(static_cats[name]))
        for i, fc in enumerate(self.static_cont_fcs):
            static_features.append(fc(static_conts[:, i:i+1]))

        # Static variable selection
        static_repr, static_weights = self.static_vsn(static_features)
        context = self.static_context_grn(static_repr)  # (B, hidden_dim)

        # 2. Process Past Observed Features
        past_feats = [
            fc(past_conts[:, :, i:i+1]) for i, fc in enumerate(self.past_cont_fcs)
        ]
        past_selected, past_weights = self.past_vsn(past_feats, context=context)

        # 3. Process Future Known Features
        future_feats = [
            fc(future_conts[:, :, i:i+1]) for i, fc in enumerate(self.future_cont_fcs)
        ]
        future_selected, future_weights = self.future_vsn(future_feats, context=context)

        # 4. Sequence Processing: LSTM Encoder & Decoder
        enc_out, (h_n, c_n) = self.lstm_encoder(past_selected)
        dec_out, _ = self.lstm_decoder(future_selected, (h_n, c_n))

        # Full temporal sequence
        full_seq = torch.cat([enc_out, dec_out], dim=1)  # (B, T_past + T_future, hidden_dim)
        full_inputs = torch.cat([past_selected, future_selected], dim=1)
        full_seq = self.seq_norm(full_inputs + self.seq_glu(full_seq))

        # 5. Static Enrichment
        enriched = self.enrichment_grn(full_seq, context=context)

        # 6. Interpretable Attention
        attn_out, attn_weights = self.self_attn(enriched, enriched, enriched)
        attn_out = self.attn_norm(enriched + attn_out)
        final_repr = self.post_attn_grn(attn_out)

        # Slice future steps only for multi-horizon forecast: (B, T_future, hidden_dim)
        future_repr = final_repr[:, t_past:, :]

        # 7. Predict Quantiles for each horizon step
        moisture_quantiles = self.moisture_head(future_repr)  # (B, T_future, 3)
        pore_p_quantiles = self.pore_p_head(future_repr)      # (B, T_future, 3)

        return {
            "moisture_quantiles": moisture_quantiles,
            "pore_pressure_quantiles": pore_p_quantiles,
            "attention_weights": attn_weights,
            "static_weights": static_weights,
            "past_weights": past_weights,
            "future_weights": future_weights
        }


def quantile_loss(y_pred: torch.Tensor, y_true: torch.Tensor, quantiles: List[float] = [0.1, 0.5, 0.9]) -> torch.Tensor:
    """
    Computes Pinball / Quantile loss across prediction quantiles.
    Args:
        y_pred: (B, T, num_quantiles)
        y_true: (B, T, 1) or (B, T)
    """
    if y_true.dim() == 2:
        y_true = y_true.unsqueeze(-1)
    
    losses = []
    for i, q in enumerate(quantiles):
        errors = y_true - y_pred[:, :, i:i+1]
        loss = torch.max((q - 1.0) * errors, q * errors)
        losses.append(loss)
    
    return torch.mean(torch.cat(losses, dim=-1))
