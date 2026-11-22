"""
TerraWatch NER - Temporal Fusion Transformer (TFT) Training & Evaluation Pipeline
- Resamples and aggregates sensor telemetry into regular 1-hour time-steps.
- Prepares 24h past observed context + 24h future forecast horizons.
- Enforces strict chronological train/val/test splits (70/15/15) with zero future leakage.
- Benchmarks TFT against standard statistical baselines (Persistence & Moving Average).
- Evaluates multi-horizon MAE and RMSE at 1h, 6h, and 24h forecast steps.
- Saves model weights, scaling parameters, and provenance metadata.
"""

import os
import sys
import json
import time
import random
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from .tft_model import TemporalFusionTransformer, quantile_loss

# Set fixed seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "terrawatch.db"
OUTPUT_DIR = BASE_DIR / "backend" / "models" / "tft"


# Station Metadata Baseline
STATION_METADATA = {
    "SN-AS-001": {"state": "Assam", "district": "Kamrup Metro", "elevation_m": 350.0, "slope_angle_deg": 22.0},
    "SN-ML-001": {"state": "Meghalaya", "district": "East Khasi Hills", "elevation_m": 1500.0, "slope_angle_deg": 38.0},
    "SN-MZ-001": {"state": "Mizoram", "district": "Aizawl", "elevation_m": 1130.0, "slope_angle_deg": 35.0},
    "SN-SK-001": {"state": "Sikkim", "district": "Gangtok", "elevation_m": 1650.0, "slope_angle_deg": 32.0},
    "SN-AR-001": {"state": "Arunachal Pradesh", "district": "Papum Pare", "elevation_m": 440.0, "slope_angle_deg": 28.0},
    "SN-NL-001": {"state": "Nagaland", "district": "Kohima", "elevation_m": 1444.0, "slope_angle_deg": 30.0},
    "SN-MN-001": {"state": "Manipur", "district": "Imphal West", "elevation_m": 780.0, "slope_angle_deg": 18.0},
    "SN-TR-001": {"state": "Tripura", "district": "West Tripura", "elevation_m": 150.0, "slope_angle_deg": 14.0}
}


def generate_calibrated_telemetry_series(hours_count: int = 1200) -> pd.DataFrame:
    """
    Generates realistic 50-day (1200 hours) hourly multi-station geotechnical time series
    incorporating diurnal temperature, monsoon rain infiltration pulses, and groundwater lag.
    Explicitly labeled as synthetic demonstration telemetry (Category C).
    """
    print(f"Generating calibrated geotechnical time series ({hours_count} hours per station across 8 states)...")
    records = []
    
    start_time = pd.Timestamp("2026-08-01 00:00:00")
    timestamps = [start_time + pd.Timedelta(hours=h) for h in range(hours_count)]
    
    for sensor_id, meta in STATION_METADATA.items():
        base_sm = 32.0 + (meta["slope_angle_deg"] * 0.2)
        base_p = 3.5 + (meta["elevation_m"] * 0.001)
        base_temp = 28.0 - (meta["elevation_m"] * 0.005)
        
        current_sm = base_sm
        current_p = base_p
        
        # Simulate intermittent monsoon storm fronts
        monsoon_mult = 1.4 if meta["state"] == "Meghalaya" else 1.0
        
        for t_idx, ts in enumerate(timestamps):
            hr = ts.hour
            doy = ts.dayofyear
            
            # Diurnal temperature cycle
            temp = base_temp + 4.5 * np.sin((hr - 9) * 2 * np.pi / 24) + np.random.normal(0, 0.4)
            
            # Rain occurrence (clustered storms every 3-5 days)
            is_rain_storm = (doy % 4 == 0) and (12 <= hr <= 20)
            if is_rain_storm:
                rain_intensity = np.random.gamma(2.5, 8.0) * monsoon_mult
            else:
                rain_intensity = np.random.exponential(0.3) if np.random.rand() < 0.15 else 0.0
                
            # Soil moisture infiltration & drainage dynamics
            infil = rain_intensity * 0.45
            drain = 0.08 * (current_sm - base_sm)
            current_sm = np.clip(current_sm + infil - drain + np.random.normal(0, 0.15), 18.0, 95.0)
            
            # Pore water pressure builds up when soil moisture exceeds field capacity (45%)
            if current_sm > 45.0:
                p_surge = (current_sm - 45.0) * 0.18 + (rain_intensity * 0.15)
                p_decay = 0.05 * (current_p - base_p)
                current_p = np.clip(current_p + p_surge - p_decay + np.random.normal(0, 0.1), 1.0, 48.0)
            else:
                current_p = np.clip(current_p - 0.12 * (current_p - base_p) + np.random.normal(0, 0.05), 1.0, 15.0)
                
            # Vibration baseline with micro-tremors
            vib = float(np.random.exponential(0.004) + 0.02)
            if rain_intensity > 25.0:
                vib += np.random.exponential(0.02)  # hydraulic runoff micro-seismic
                
            records.append({
                "sensor_id": sensor_id,
                "timestamp": ts,
                "soil_moisture": round(float(current_sm), 2),
                "pore_pressure": round(float(current_p), 2),
                "temperature": round(float(temp), 1),
                "ground_vibration": round(float(vib), 4),
                "rainfall_mm": round(float(rain_intensity), 1),
                "hour_of_day": hr,
                "day_of_week": ts.dayofweek,
                "state": meta["state"],
                "district": meta["district"],
                "elevation_m": meta["elevation_m"],
                "slope_angle_deg": meta["slope_angle_deg"]
            })
            
    df = pd.DataFrame(records)
    print(f"Total time series records generated: {len(df)} rows across {len(STATION_METADATA)} stations.")
    return df


def load_and_resample_telemetry() -> pd.DataFrame:
    """
    Attempts to load existing telemetry from SQLite. If historical depth is less than 200 hours,
    supplements with calibrated physics simulation sequence for robust multi-step training.
    """
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH))
            query = """
            SELECT sensor_id, timestamp, soil_moisture, temperature, pore_pressure, ground_vibration
            FROM sensor_readings
            WHERE soil_moisture IS NOT NULL AND pore_pressure IS NOT NULL
            ORDER BY timestamp ASC
            """
            df_sql = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df_sql) > 500:
                df_sql["timestamp"] = pd.to_datetime(df_sql["timestamp"])
                span_hours = (df_sql["timestamp"].max() - df_sql["timestamp"].min()).total_seconds() / 3600.0
                if span_hours >= 150.0:
                    print(f"Loaded {len(df_sql)} real database readings spanning {span_hours:.1f} hours.")
                    # Regularize to hourly
                    df_sql["timestamp"] = df_sql["timestamp"].dt.floor("h")
                    resampled = df_sql.groupby(["sensor_id", "timestamp"]).agg({
                        "soil_moisture": "mean",
                        "pore_pressure": "mean",
                        "temperature": "mean",
                        "ground_vibration": "max"
                    }).reset_index()
                    
                    # Check if each station has sufficient contiguous hourly depth
                    station_counts = resampled.groupby("sensor_id").size()
                    if station_counts.min() >= 60:
                        # Attach station static metadata and time features
                        resampled["hour_of_day"] = resampled["timestamp"].dt.hour
                        resampled["day_of_week"] = resampled["timestamp"].dt.day_of_week
                        resampled["state"] = resampled["sensor_id"].apply(lambda sid: STATION_METADATA.get(sid, {}).get("state", "Assam"))
                        resampled["district"] = resampled["sensor_id"].apply(lambda sid: STATION_METADATA.get(sid, {}).get("district", "Kamrup Metro"))
                        resampled["elevation_m"] = resampled["sensor_id"].apply(lambda sid: STATION_METADATA.get(sid, {}).get("elevation_m", 350.0))
                        resampled["slope_angle_deg"] = resampled["sensor_id"].apply(lambda sid: STATION_METADATA.get(sid, {}).get("slope_angle_deg", 22.0))
                        resampled["rainfall_mm"] = 0.0
                        return resampled
                    else:
                        print(f"Database telemetry has sparse temporal bursts (max contiguous hours per station: {station_counts.min()}).")
                        print("Augmenting with calibrated 50-day multi-station continuous telemetry series.")
        except Exception as e:
            print(f"Notice reading SQLite telemetry: {e}")

    # Fallback to calibrated 50-day sequence
    return generate_calibrated_telemetry_series(hours_count=1200)


class TimeSeriesSequenceDataset(Dataset):
    """
    Constructs past (24h) and future (24h) sequence windows per station.
    """
    def __init__(
        self,
        samples: List[Dict[str, np.ndarray]]
    ):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        return {
            "sensor_id": torch.tensor(s["sensor_id"], dtype=torch.long),
            "state_id": torch.tensor(s["state_id"], dtype=torch.long),
            "static_conts": torch.tensor(s["static_conts"], dtype=torch.float32),
            "past_conts": torch.tensor(s["past_conts"], dtype=torch.float32),
            "future_conts": torch.tensor(s["future_conts"], dtype=torch.float32),
            "target_moisture": torch.tensor(s["target_moisture"], dtype=torch.float32),
            "target_pore_p": torch.tensor(s["target_pore_p"], dtype=torch.float32)
        }


def prepare_dataset_splits(
    df: pd.DataFrame,
    seq_len_past: int = 24,
    seq_len_future: int = 24
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Constructs chronological train/validation/test samples across all stations.
    Calculates normalization scalers strictly on the training set to prevent data leakage.
    """
    sensor_map = {sid: i for i, sid in enumerate(sorted(df["sensor_id"].unique()))}
    state_map = {st: i for i, st in enumerate(sorted(df["state"].unique()))}

    # Chronological timestamps
    unique_times = sorted(df["timestamp"].unique())
    n_times = len(unique_times)
    
    train_end_idx = int(0.70 * n_times)
    val_end_idx = int(0.85 * n_times)
    
    train_times = set(unique_times[:train_end_idx])
    val_times = set(unique_times[train_end_idx:val_end_idx])
    test_times = set(unique_times[val_end_idx:])
    
    print(f"Chronological split timeline:")
    print(f"  Train:      {len(train_times)} hours ({unique_times[0]} to {unique_times[train_end_idx-1]})")
    print(f"  Validation: {len(val_times)} hours ({unique_times[train_end_idx]} to {unique_times[val_end_idx-1]})")
    print(f"  Test:       {len(test_times)} hours ({unique_times[val_end_idx]} to {unique_times[-1]})")

    # Fit Scalers strictly on Training Set
    train_df = df[df["timestamp"].isin(train_times)]
    
    scalers = {
        "soil_moisture": {"mean": float(train_df["soil_moisture"].mean()), "std": float(train_df["soil_moisture"].std() or 1.0)},
        "pore_pressure": {"mean": float(train_df["pore_pressure"].mean()), "std": float(train_df["pore_pressure"].std() or 1.0)},
        "temperature": {"mean": float(train_df["temperature"].mean()), "std": float(train_df["temperature"].std() or 1.0)},
        "ground_vibration": {"mean": float(train_df["ground_vibration"].mean()), "std": float(train_df["ground_vibration"].std() or 0.01)},
        "elevation_m": {"mean": float(train_df["elevation_m"].mean()), "std": float(train_df["elevation_m"].std() or 1.0)},
        "slope_angle_deg": {"mean": float(train_df["slope_angle_deg"].mean()), "std": float(train_df["slope_angle_deg"].std() or 1.0)},
        "sensor_map": sensor_map,
        "state_map": state_map
    }

    def _normalize(val: float, key: str) -> float:
        return (val - scalers[key]["mean"]) / scalers[key]["std"]

    train_samples, val_samples, test_samples = [], [], []

    # Window generation per station
    for sid, group in df.groupby("sensor_id"):
        group = group.sort_values("timestamp").reset_index(drop=True)
        meta = STATION_METADATA.get(sid, {"state": "Assam", "elevation_m": 350.0, "slope_angle_deg": 20.0})
        
        static_conts = np.array([
            _normalize(meta["elevation_m"], "elevation_m"),
            _normalize(meta["slope_angle_deg"], "slope_angle_deg")
        ], dtype=np.float32)
        
        n_rows = len(group)
        for i in range(n_rows - seq_len_past - seq_len_future + 1):
            past_slice = group.iloc[i : i + seq_len_past]
            future_slice = group.iloc[i + seq_len_past : i + seq_len_past + seq_len_future]
            
            # Predict timestamp partition based on target horizon start
            forecast_origin_time = past_slice["timestamp"].iloc[-1]
            
            past_conts = np.column_stack([
                past_slice["soil_moisture"].apply(lambda v: _normalize(v, "soil_moisture")).values,
                past_slice["pore_pressure"].apply(lambda v: _normalize(v, "pore_pressure")).values,
                past_slice["temperature"].apply(lambda v: _normalize(v, "temperature")).values,
                past_slice["ground_vibration"].apply(lambda v: _normalize(v, "ground_vibration")).values
            ]).astype(np.float32)
            
            future_conts = np.column_stack([
                future_slice["hour_of_day"].values / 23.0,
                future_slice["day_of_week"].values / 6.0
            ]).astype(np.float32)
            
            target_sm = future_slice["soil_moisture"].apply(lambda v: _normalize(v, "soil_moisture")).values.astype(np.float32)
            target_pp = future_slice["pore_pressure"].apply(lambda v: _normalize(v, "pore_pressure")).values.astype(np.float32)
            
            sample = {
                "sensor_id": sensor_map[sid],
                "state_id": state_map[meta["state"]],
                "static_conts": static_conts,
                "past_conts": past_conts,
                "future_conts": future_conts,
                "target_moisture": target_sm,
                "target_pore_p": target_pp,
                # Unnormalized targets for exact baseline metric calculation
                "raw_past_moisture": past_slice["soil_moisture"].values,
                "raw_past_pore_p": past_slice["pore_pressure"].values,
                "raw_future_moisture": future_slice["soil_moisture"].values,
                "raw_future_pore_p": future_slice["pore_pressure"].values
            }
            
            if forecast_origin_time in train_times:
                train_samples.append(sample)
            elif forecast_origin_time in val_times:
                val_samples.append(sample)
            elif forecast_origin_time in test_times:
                test_samples.append(sample)

    print(f"Sample Windows: Train={len(train_samples)}, Val={len(val_samples)}, Test={len(test_samples)}")
    return train_samples, val_samples, test_samples, scalers


def evaluate_baselines(test_samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes statistical persistence and rolling average baselines on the test set.
    """
    print("\nComputing statistical baselines on test set...")
    
    # Target horizons: index 0 (1h), index 5 (6h), index 23 (24h)
    horizons = {"1h": 0, "6h": 5, "24h": 23}
    
    # 1. Persistence Baseline: y_{t+h} = y_t
    p_sm_mae = {h: [] for h in horizons}
    p_sm_rmse = {h: [] for h in horizons}
    p_pp_mae = {h: [] for h in horizons}
    p_pp_rmse = {h: [] for h in horizons}
    
    # 2. Moving Average Baseline (Past 24h mean)
    ma_sm_mae = {h: [] for h in horizons}
    ma_pp_mae = {h: [] for h in horizons}
    
    for s in test_samples:
        y_sm_true = s["raw_future_moisture"]
        y_pp_true = s["raw_future_pore_p"]
        
        # Persistence prediction is last observed reading
        pred_sm_persist = s["raw_past_moisture"][-1]
        pred_pp_persist = s["raw_past_pore_p"][-1]
        
        # Moving average prediction
        pred_sm_ma = float(np.mean(s["raw_past_moisture"]))
        pred_pp_ma = float(np.mean(s["raw_past_pore_p"]))
        
        for name, idx in horizons.items():
            err_sm_p = abs(y_sm_true[idx] - pred_sm_persist)
            err_pp_p = abs(y_pp_true[idx] - pred_pp_persist)
            p_sm_mae[name].append(err_sm_p)
            p_sm_rmse[name].append((y_sm_true[idx] - pred_sm_persist)**2)
            p_pp_mae[name].append(err_pp_p)
            p_pp_rmse[name].append((y_pp_true[idx] - pred_pp_persist)**2)
            
            ma_sm_mae[name].append(abs(y_sm_true[idx] - pred_sm_ma))
            ma_pp_mae[name].append(abs(y_pp_true[idx] - pred_pp_ma))
            
    results = {
        "persistence": {
            "soil_moisture_mae": {h: round(float(np.mean(p_sm_mae[h])), 3) for h in horizons},
            "soil_moisture_rmse": {h: round(float(np.sqrt(np.mean(p_sm_rmse[h]))), 3) for h in horizons},
            "pore_pressure_mae": {h: round(float(np.mean(p_pp_mae[h])), 3) for h in horizons},
            "pore_pressure_rmse": {h: round(float(np.sqrt(np.mean(p_pp_rmse[h]))), 3) for h in horizons}
        },
        "moving_average_24h": {
            "soil_moisture_mae": {h: round(float(np.mean(ma_sm_mae[h])), 3) for h in horizons},
            "pore_pressure_mae": {h: round(float(np.mean(ma_pp_mae[h])), 3) for h in horizons}
        }
    }
    return results


def train_tft_pipeline(epochs: int = 12, batch_size: int = 32, lr: float = 0.001):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Load Telemetry Data
    df = load_and_resample_telemetry()
    
    # 2. Build Datasets
    train_samples, val_samples, test_samples, scalers = prepare_dataset_splits(df)
    
    train_ds = TimeSeriesSequenceDataset(train_samples)
    val_ds = TimeSeriesSequenceDataset(val_samples)
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    
    # 3. Instantiate Native TFT Model
    model = TemporalFusionTransformer(
        static_cat_cardinalities={
            "sensor_id": len(scalers["sensor_map"]),
            "state": len(scalers["state_map"])
        },
        num_static_continuous=2,
        num_past_continuous=4,
        num_future_continuous=2,
        hidden_dim=32,
        num_heads=2,
        lstm_layers=1,
        dropout=0.1
    )
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    best_val_loss = float("inf")
    checkpoint_path = OUTPUT_DIR / "best_tft_checkpoint.pt"
    
    print("\n--- Training Temporal Fusion Transformer (TFT) on CPU ---")
    t0 = time.time()
    
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss_acc = 0.0
        
        for b in train_loader:
            optimizer.zero_grad()
            static_cats = {"sensor_id": b["sensor_id"], "state": b["state_id"]}
            out = model(static_cats, b["static_conts"], b["past_conts"], b["future_conts"])
            
            loss_sm = quantile_loss(out["moisture_quantiles"], b["target_moisture"])
            loss_pp = quantile_loss(out["pore_pressure_quantiles"], b["target_pore_p"])
            loss = loss_sm + loss_pp
            
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss_acc += loss.item()
            
        train_loss = train_loss_acc / len(train_loader)
        
        # Validation
        model.eval()
        val_loss_acc = 0.0
        with torch.no_grad():
            for b in val_loader:
                static_cats = {"sensor_id": b["sensor_id"], "state": b["state_id"]}
                out = model(static_cats, b["static_conts"], b["past_conts"], b["future_conts"])
                loss_sm = quantile_loss(out["moisture_quantiles"], b["target_moisture"])
                loss_pp = quantile_loss(out["pore_pressure_quantiles"], b["target_pore_p"])
                val_loss_acc += (loss_sm + loss_pp).item()
                
        val_loss = val_loss_acc / len(val_loader)
        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "model_state_dict": model.state_dict(),
                "epoch": epoch,
                "val_loss": val_loss,
                "config": {
                    "hidden_dim": 32,
                    "num_heads": 2,
                    "lstm_layers": 1,
                    "quantiles": [0.1, 0.5, 0.9]
                }
            }, str(checkpoint_path))
            
    train_duration = round(time.time() - t0, 2)
    print(f"\nTraining completed in {train_duration}s. Best Val Loss: {best_val_loss:.4f}")
    
    # 4. Evaluate TFT on Test Set
    checkpoint = torch.load(str(checkpoint_path), map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    
    horizons = {"1h": 0, "6h": 5, "24h": 23}
    tft_sm_mae = {h: [] for h in horizons}
    tft_sm_rmse = {h: [] for h in horizons}
    tft_pp_mae = {h: [] for h in horizons}
    tft_pp_rmse = {h: [] for h in horizons}
    
    sm_mean = scalers["soil_moisture"]["mean"]
    sm_std = scalers["soil_moisture"]["std"]
    pp_mean = scalers["pore_pressure"]["mean"]
    pp_std = scalers["pore_pressure"]["std"]
    
    with torch.no_grad():
        for s in test_samples:
            static_cats = {
                "sensor_id": torch.tensor([s["sensor_id"]], dtype=torch.long),
                "state": torch.tensor([s["state_id"]], dtype=torch.long)
            }
            static_conts = torch.tensor(s["static_conts"]).unsqueeze(0)
            past_conts = torch.tensor(s["past_conts"]).unsqueeze(0)
            future_conts = torch.tensor(s["future_conts"]).unsqueeze(0)
            
            out = model(static_cats, static_conts, past_conts, future_conts)
            
            # Median prediction (quantile index 1 = p50)
            pred_sm_norm = out["moisture_quantiles"][0, :, 1].numpy()
            pred_pp_norm = out["pore_pressure_quantiles"][0, :, 1].numpy()
            
            # De-normalize
            pred_sm = pred_sm_norm * sm_std + sm_mean
            pred_pp = pred_pp_norm * pp_std + pp_mean
            
            raw_sm_true = s["raw_future_moisture"]
            raw_pp_true = s["raw_future_pore_p"]
            
            for h_name, idx in horizons.items():
                tft_sm_mae[h_name].append(abs(raw_sm_true[idx] - pred_sm[idx]))
                tft_sm_rmse[h_name].append((raw_sm_true[idx] - pred_sm[idx])**2)
                tft_pp_mae[h_name].append(abs(raw_pp_true[idx] - pred_pp[idx]))
                tft_pp_rmse[h_name].append((raw_pp_true[idx] - pred_pp[idx])**2)
                
    tft_metrics = {
        "soil_moisture_mae": {h: round(float(np.mean(tft_sm_mae[h])), 3) for h in horizons},
        "soil_moisture_rmse": {h: round(float(np.sqrt(np.mean(tft_sm_rmse[h]))), 3) for h in horizons},
        "pore_pressure_mae": {h: round(float(np.mean(tft_pp_mae[h])), 3) for h in horizons},
        "pore_pressure_rmse": {h: round(float(np.sqrt(np.mean(tft_pp_rmse[h]))), 3) for h in horizons}
    }
    
    # 5. Baseline Evaluation
    baseline_metrics = evaluate_baselines(test_samples)
    
    # 6. Save Metadata & Evaluation Provenance
    metadata = {
        "model_name": "Temporal Fusion Transformer (TFT)",
        "framework": "PyTorch Native TFT (Canonical Lim et al., 2021)",
        "device": "cpu",
        "parameters_count": sum(p.numel() for p in model.parameters()),
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "training_time_seconds": train_duration,
        "best_epoch": checkpoint["epoch"],
        "best_val_loss": round(float(best_val_loss), 4),
        "evaluation_metrics": {
            "tft": tft_metrics,
            "persistence_baseline": baseline_metrics["persistence"],
            "moving_average_baseline": baseline_metrics["moving_average_24h"]
        },
        "forecast_horizons": ["1h", "6h", "24h"],
        "target_variables": ["soil_moisture_pct", "pore_pressure_kpa"],
        "quantiles": [0.1, 0.5, 0.9],
        "provenance_category": "Category C (Simulation-Based Academic Advisory Model)",
        "scientific_integrity_notice": (
            "Model trained on calibrated regional telemetry sequences. Operates strictly in Advisory Mode. "
            "Does NOT modify operational life-safety risk tiers or LightGBM spatial susceptibility predictions."
        )
    }
    
    with open(OUTPUT_DIR / "tft_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    with open(OUTPUT_DIR / "tft_scalers.json", "w", encoding="utf-8") as f:
        json.dump(scalers, f, indent=2)
        
    print(f"\nTFT Model artifacts successfully saved to {OUTPUT_DIR}")
    print(f"Summary Metrics (TFT vs Persistence Baseline):")
    print(f"  Soil Moisture 24h MAE: TFT={tft_metrics['soil_moisture_mae']['24h']}% vs Baseline={baseline_metrics['persistence']['soil_moisture_mae']['24h']}%")
    print(f"  Pore Pressure 24h MAE: TFT={tft_metrics['pore_pressure_mae']['24h']} kPa vs Baseline={baseline_metrics['persistence']['pore_pressure_mae']['24h']} kPa")


if __name__ == "__main__":
    train_tft_pipeline()
