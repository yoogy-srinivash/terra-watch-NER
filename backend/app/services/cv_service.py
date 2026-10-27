"""
LandSafe Connect - Computer Vision Hazard Evidence Engine (Phase 3)

SCIENTIFIC STATUS & INTEGRITY NOTICE:
-------------------------------------
The current repository does NOT contain a scientifically validated, labeled landslide
image dataset. Therefore:
1. No arbitrary numerical confidence scores (e.g. 0.78, 0.85) are fabricated.
   When no trained classifier exists, `confidence` is strictly `None` (null).
2. MobileNetV2 (if PyTorch is present) is treated STRICTLY as a general-purpose
   feature extractor (`FEATURE_EXTRACTION_ONLY`), NOT as a landslide classifier.
   ImageNet classes (e.g., 'alp', 'valley', 'cliff') are NOT landslide probabilities.
3. In the absence of a trained classifier, the system operates as a
   "Deterministic Visual Evidence Analyzer" (`HEURISTIC_NOT_VALIDATED`).
4. Measurable physical features (color statistics, edge density, local variance,
   vegetation indices) are explicitly reported with qualitative evidence strength
   (LOW | MODERATE | HIGH).
5. A modular `HazardVisionModel` interface is provided so that a genuine model
   trained on real labeled landslide imagery can be plugged in seamlessly in the future.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image, UnidentifiedImageError

from ..utils.logging import audit_logger


# =============================================================================
# 1. HAZARD EVIDENCE CATEGORIES & MODEL INTERFACE
# =============================================================================

SUPPORTED_HAZARD_CATEGORIES = [
    "landslide_debris",
    "exposed_soil_or_scar",
    "tension_crack",
    "rockfall_or_displaced_rock",
    "water_accumulation_or_mudflow",
    "unstable_slope_indicators",
    "stable_terrain",
    "unclassified"
]


class HazardVisionModel(ABC):
    """
    Abstract interface for future trained computer vision hazard classifiers.
    A future model trained on a verified landslide dataset (e.g., Landslide4Sense,
    NER Field Hazard Dataset) must implement this interface.
    """

    @abstractmethod
    def predict(self, image: Image.Image) -> Dict[str, Any]:
        """Predict hazard class from image."""
        pass

    @abstractmethod
    def predict_proba(self, image: Image.Image) -> Optional[Dict[str, float]]:
        """Return calibrated class probabilities if trained; otherwise None."""
        pass

    @abstractmethod
    def explain(self, image: Image.Image) -> Dict[str, Any]:
        """Return visual attribution or feature explanations (e.g. Grad-CAM, saliency)."""
        pass

    @abstractmethod
    def model_metadata(self) -> Dict[str, Any]:
        """Return provenance and training metadata of the model."""
        pass


# Active pluggable model holder (None until a trained classifier is registered)
_ACTIVE_TRAINED_MODEL: Optional[HazardVisionModel] = None


def register_hazard_model(model: HazardVisionModel) -> None:
    """Register a genuine trained hazard vision model."""
    global _ACTIVE_TRAINED_MODEL
    _ACTIVE_TRAINED_MODEL = model


def get_active_hazard_model() -> Optional[HazardVisionModel]:
    """Retrieve currently active trained hazard vision model, if any."""
    return _ACTIVE_TRAINED_MODEL


def get_empty_model_metadata() -> Dict[str, Any]:
    """
    Standard model metadata schema for recording provenance when a trained model exists.
    All fields are None when no trained model is available.
    """
    return {
        "dataset_name": None,
        "dataset_version": None,
        "number_of_classes": None,
        "training_samples": None,
        "validation_samples": None,
        "test_samples": None,
        "training_date": None,
        "model_architecture": None,
        "pretrained_weights_source": None,
        "metrics": None,
        "calibration_method": None,
        "geographic_scope": None
    }


# =============================================================================
# 2. IMAGE QUALITY CHECK & VALIDATION LAYER
# =============================================================================

class ImageQualityChecker:
    """
    Validates input field images prior to feature extraction.
    Rejects missing, corrupted, zero-byte, or excessively degraded images.
    """
    MIN_WIDTH: int = 32
    MIN_HEIGHT: int = 32
    RECOMMENDED_WIDTH: int = 64
    RECOMMENDED_HEIGHT: int = 64
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    @classmethod
    def validate_image_file(cls, image_path: str) -> Tuple[bool, Dict[str, Any], Optional[Image.Image]]:
        """
        Validate image existence, format integrity, and resolution.
        Returns: (is_valid, quality_dict, loaded_image_or_none)
        """
        issues: List[str] = []

        if not image_path or not os.path.exists(image_path):
            return False, {
                "valid": False,
                "dimensions": None,
                "format": None,
                "channels": None,
                "file_size_bytes": 0,
                "issues": ["Image file does not exist on disk."]
            }, None

        if not os.path.isfile(image_path):
            return False, {
                "valid": False,
                "dimensions": None,
                "format": None,
                "channels": None,
                "file_size_bytes": 0,
                "issues": ["Path is not a regular file."]
            }, None

        file_size = os.path.getsize(image_path)
        if file_size == 0:
            return False, {
                "valid": False,
                "dimensions": None,
                "format": None,
                "channels": None,
                "file_size_bytes": 0,
                "issues": ["Image file is empty (0 bytes)."]
            }, None

        ext = Path(image_path).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            issues.append(f"Uncommon image extension '{ext}'.")

        try:
            with Image.open(image_path) as raw_img:
                img_format = raw_img.format
                width, height = raw_img.size
                channels = len(raw_img.getbands())

                # Force loading pixel buffer to verify image is not truncated or corrupted
                raw_img.load()
                # Create a persistent copy in RGB mode
                rgb_img = raw_img.convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as e:
            return False, {
                "valid": False,
                "dimensions": None,
                "format": None,
                "channels": None,
                "file_size_bytes": file_size,
                "issues": [f"Corrupted or undecodable image file: {str(e)}"]
            }, None

        # Check resolution thresholds
        if width < cls.MIN_WIDTH or height < cls.MIN_HEIGHT:
            issues.append(f"Image resolution {width}x{height} is below minimum threshold ({cls.MIN_WIDTH}x{cls.MIN_HEIGHT}).")
            return False, {
                "valid": False,
                "dimensions": [width, height],
                "format": img_format,
                "channels": channels,
                "file_size_bytes": file_size,
                "issues": issues
            }, None

        if width < cls.RECOMMENDED_WIDTH or height < cls.RECOMMENDED_HEIGHT:
            issues.append(f"Low resolution warning: {width}x{height} is below recommended {cls.RECOMMENDED_WIDTH}x{cls.RECOMMENDED_HEIGHT}.")

        return True, {
            "valid": True,
            "dimensions": [width, height],
            "format": img_format,
            "channels": channels,
            "file_size_bytes": file_size,
            "issues": issues
        }, rgb_img


# =============================================================================
# 3. PRETRAINED BACKBONE / FEATURE EXTRACTOR
# =============================================================================

class FeatureExtractorBackbone:
    """
    Manages deep feature extraction if PyTorch and MobileNetV2 are available.
    STRICTLY used as an embedding generator; NEVER as a landslide classifier.
    """
    _torch_available: Optional[bool] = None
    _model = None
    _transform = None

    @classmethod
    def is_available(cls) -> bool:
        if cls._torch_available is None:
            try:
                import torch
                import torchvision.models as models
                cls._torch_available = True
            except ImportError:
                cls._torch_available = False
        return cls._torch_available

    @classmethod
    def extract_features(cls, img: Image.Image) -> Optional[List[float]]:
        """Extract 1280-dim embedding vector from MobileNetV2 if available."""
        if not cls.is_available():
            return None
        try:
            import torch
            import torchvision.transforms as transforms
            import torchvision.models as models

            if cls._model is None:
                # Load MobileNetV2 backbone without classification head
                backbone = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
                backbone.classifier = torch.nn.Identity()
                backbone.eval()
                cls._model = backbone
                cls._transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])

            with torch.no_grad():
                tensor = cls._transform(img).unsqueeze(0)
                embedding = cls._model(tensor).squeeze(0).numpy()
                return [round(float(v), 5) for v in embedding[:64]]  # Sample first 64 dimensions for compact representation
        except Exception as e:
            audit_logger.warning(f"PyTorch backbone feature extraction failed: {e}")
            return None


# =============================================================================
# 4. DETERMINISTIC VISUAL EVIDENCE ANALYZER (HEURISTIC FALLBACK)
# =============================================================================

class DeterministicVisualAnalyzer:
    """
    Deterministic visual evidence pipeline based on legitimate mathematical
    and spectral image statistics:
    - Color statistics & RGB distribution
    - Earth-tone (mud / bare soil) reflectance ratio
    - Vegetation indices (Excess Green / GLI)
    - Surface texture variance & edge density
    - Water accumulation / blue spectral dominance
    """

    @staticmethod
    def extract_features(img: Image.Image) -> Dict[str, Any]:
        """Compute transparent, reproducible visual statistics on image."""
        # Standardize evaluation size for deterministic metrics
        eval_img = img.resize((128, 128), Image.Resampling.BILINEAR)
        arr = np.array(eval_img, dtype=np.float32) / 255.0

        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]

        # 1. Color distribution & means
        mean_r = float(np.mean(r))
        mean_g = float(np.mean(g))
        mean_b = float(np.mean(b))
        mean_rgb = [round(mean_r, 4), round(mean_g, 4), round(mean_b, 4)]

        # 2. Grayscale & contrast variance
        gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
        contrast_variance = float(np.var(gray))

        # 3. Earth-tone / Mud & Bare Soil index
        # Soil/mud signatures exhibit R > G > B with positive redness-to-blueness delta
        earth_mask = (r > g) & (g > b * 0.9) & ((r - b) > 0.08)
        earth_tone_ratio = float(np.mean(earth_mask))

        # 4. Vegetation Index (Normalized Excess Green Index: (2G - R - B) / (2G + R + B + eps))
        denom = 2.0 * g + r + b + 1e-6
        exg = (2.0 * g - r - b) / denom
        vegetation_index = float(np.mean(exg))
        vegetation_coverage = float(np.mean(exg > 0.05))

        # 5. Water / Ponding index (B dominant with low localized texture)
        water_mask = (b > r * 1.1) & (b > g * 0.95) & ((b - r) > 0.08)
        water_ratio = float(np.mean(water_mask))

        # 6. Edge density & Gradient roughness (Sobel-like finite differences)
        dx = np.abs(gray[:, 1:] - gray[:, :-1])
        dy = np.abs(gray[1:, :] - gray[:-1, :])
        # Pad to match dimensions
        dx_padded = np.pad(dx, ((0, 0), (0, 1)), mode='constant')
        dy_padded = np.pad(dy, ((0, 1), (0, 0)), mode='constant')
        grad_mag = np.sqrt(dx_padded**2 + dy_padded**2)
        mean_gradient = float(np.mean(grad_mag))
        edge_density = float(np.mean(grad_mag > 0.08))

        return {
            "mean_rgb": mean_rgb,
            "contrast_variance": round(contrast_variance, 4),
            "earth_tone_ratio": round(earth_tone_ratio, 4),
            "vegetation_index": round(vegetation_index, 4),
            "vegetation_coverage": round(vegetation_coverage, 4),
            "water_ratio": round(water_ratio, 4),
            "mean_gradient": round(mean_gradient, 4),
            "edge_density": round(edge_density, 4)
        }

    @classmethod
    def evaluate_evidence(cls, features: Dict[str, Any]) -> Tuple[bool, str, str, List[str]]:
        """
        Evaluate physical hazard evidence indicators from extracted features.
        Returns: (hazard_detected, hazard_type, evidence_strength, evidence_notes)
        """
        earth = features["earth_tone_ratio"]
        veg = features["vegetation_index"]
        veg_cov = features["vegetation_coverage"]
        edge = features["edge_density"]
        variance = features["contrast_variance"]
        water = features["water_ratio"]

        evidence_notes: List[str] = []
        hazard_type = "stable_terrain"
        evidence_strength = "LOW"
        hazard_detected = False

        # Physical evidence rules based on observable optical cues:

        # Case A: Water accumulation / Mudflow
        if water > 0.15:
            hazard_detected = True
            hazard_type = "water_accumulation_or_mudflow"
            evidence_notes.append(f"Significant blue/specular fluid reflectance detected (water_ratio: {water:.2%}).")
            if water > 0.35:
                evidence_strength = "HIGH"
            else:
                evidence_strength = "MODERATE"

        # Case B: Landslide Debris / Fresh Scar
        elif earth > 0.25 and veg < 0.02 and (edge > 0.10 or variance > 0.02):
            hazard_detected = True
            hazard_type = "landslide_debris"
            evidence_notes.append(f"Extensive exposed earth/debris spectral signature (earth_tone_ratio: {earth:.2%}).")
            evidence_notes.append(f"Sparse vegetative canopy (vegetation_index: {veg:.3f}, coverage: {veg_cov:.2%}).")
            evidence_notes.append(f"Fragmented texture and surface roughness observed (edge_density: {edge:.2%}, variance: {variance:.4f}).")

            if earth > 0.45 and edge > 0.18:
                evidence_strength = "HIGH"
            else:
                evidence_strength = "MODERATE"

        # Case C: Exposed Soil / Fresh Scar without heavy fragmentation
        elif earth > 0.30 and veg < -0.02:
            hazard_detected = True
            hazard_type = "exposed_soil_or_scar"
            evidence_notes.append(f"Bare soil cut or scarp signature detected (earth_tone_ratio: {earth:.2%}, veg_index: {veg:.3f}).")
            evidence_strength = "MODERATE" if earth > 0.50 else "LOW"

        # Case D: Tension Crack or Surface Rupture (High linear edge density against moderate terrain)
        elif edge > 0.22 and variance > 0.035:
            hazard_detected = True
            hazard_type = "tension_crack"
            evidence_notes.append(f"High localized edge and gradient discontinuity (edge_density: {edge:.2%}, variance: {variance:.4f}).")
            evidence_strength = "MODERATE"

        # Case E: Rockfall / Displaced Mineral Boulder
        elif edge > 0.16 and variance > 0.028 and earth < 0.15 and veg < 0.05:
            hazard_detected = True
            hazard_type = "rockfall_or_displaced_rock"
            evidence_notes.append(f"High surface gradient roughness with low vegetation and mineral tone (edge_density: {edge:.2%}).")
            evidence_strength = "MODERATE"

        # Case F: Stable Vegetated Slope / Normal Terrain
        elif veg > 0.05 and veg_cov > 0.40 and edge < 0.15:
            hazard_detected = False
            hazard_type = "stable_terrain"
            evidence_strength = "LOW"
            evidence_notes.append(f"Continuous vegetative cover and low surface disruption (vegetation_coverage: {veg_cov:.2%}, edge_density: {edge:.2%}).")

        # Case G: Ambiguous / Unclassified
        else:
            hazard_detected = False
            hazard_type = "stable_terrain"
            evidence_strength = "LOW"
            evidence_notes.append(f"Terrain features within baseline parameters (earth: {earth:.2%}, veg_index: {veg:.3f}, edge_density: {edge:.2%}).")

        return hazard_detected, hazard_type, evidence_strength, evidence_notes


# =============================================================================
# 5. MAIN PUBLIC API: analyze_field_image()
# =============================================================================

def analyze_field_image(image_path: str) -> Dict[str, Any]:
    """
    Modular, scientifically defensible field image hazard evidence analysis.

    Preserves 100% backward compatibility for existing callers and database models
    while providing strict scientific honesty:
    - Never assigns arbitrary fake confidence.
    - If no trained model exists, `confidence` is strictly None.
    - Accurately reports whether a trained classifier is loaded.
    """
    # 1. Quality Validation
    is_valid, quality_info, rgb_image = ImageQualityChecker.validate_image_file(image_path)

    if not is_valid:
        return {
            "hazard_detected": False,
            "hazard_type": "unclassified",
            "hazard_label": "unclassified",           # Backward-compatible field
            "evidence_strength": "LOW",
            "model_available": False,
            "trained_classifier": False,
            "model_type": "Deterministic Visual Evidence Analyzer",
            "scientific_status": "REJECTED_QUALITY_FAILURE",
            "image_quality": quality_info,
            "visual_features": None,
            "evidence": quality_info["issues"],
            "confidence": None,                        # MUST be null
            "is_scientific_validated": False,          # Backward-compatible field
            "notes": quality_info["issues"][0] if quality_info["issues"] else "Quality check failed.",
            "model_metadata": get_empty_model_metadata()
        }

    # 2. Check for pluggable trained model
    trained_model = get_active_hazard_model()
    if trained_model is not None:
        try:
            pred = trained_model.predict(rgb_image)
            proba = trained_model.predict_proba(rgb_image)
            expl = trained_model.explain(rgb_image)
            meta = trained_model.model_metadata()

            hazard_type = pred.get("hazard_type", "unclassified")
            hazard_detected = pred.get("hazard_detected", hazard_type != "stable_terrain")
            confidence_val = proba.get(hazard_type) if proba else None

            return {
                "hazard_detected": hazard_detected,
                "hazard_type": hazard_type,
                "hazard_label": hazard_type,
                "evidence_strength": pred.get("evidence_strength", "HIGH"),
                "model_available": True,
                "trained_classifier": True,
                "model_type": meta.get("model_architecture", "Trained Hazard Classifier"),
                "scientific_status": "TRAINED_MODEL_INFERENCE",
                "image_quality": quality_info,
                "visual_features": expl.get("features"),
                "evidence": expl.get("evidence", []),
                "confidence": confidence_val,
                "is_scientific_validated": True,
                "model_metadata": meta,
                "image_dimensions": f"{quality_info['dimensions'][0]}x{quality_info['dimensions'][1]}"
            }
        except Exception as e:
            audit_logger.error(f"Active trained model inference failed, falling back to heuristic: {e}")

    # 3. Check for Pretrained Backbone (Feature Extraction Only)
    backbone_features = None
    if FeatureExtractorBackbone.is_available():
        backbone_features = FeatureExtractorBackbone.extract_features(rgb_image)

    # 4. Deterministic Visual Analysis
    try:
        visual_features = DeterministicVisualAnalyzer.extract_features(rgb_image)
        if backbone_features:
            visual_features["deep_embedding_sample"] = backbone_features

        hazard_detected, hazard_type, evidence_strength, evidence_notes = (
            DeterministicVisualAnalyzer.evaluate_evidence(visual_features)
        )

        # Map hazard_type to legacy hazard_label format for full backward compatibility
        legacy_label_map = {
            "landslide_debris": "landslide_debris",
            "exposed_soil_or_scar": "landslide_debris",
            "tension_crack": "surface_crack_or_rockfall",
            "rockfall_or_displaced_rock": "surface_crack_or_rockfall",
            "water_accumulation_or_mudflow": "water_accumulation",
            "unstable_slope_indicators": "landslide_debris",
            "stable_terrain": "normal_terrain",
            "unclassified": "unclassified"
        }
        legacy_label = legacy_label_map.get(hazard_type, "normal_terrain")

        model_type_desc = (
            "MobileNetV2 pretrained feature extractor"
            if FeatureExtractorBackbone.is_available()
            else "Deterministic Visual Evidence Analyzer"
        )
        status_desc = (
            "FEATURE_EXTRACTION_ONLY"
            if FeatureExtractorBackbone.is_available()
            else "HEURISTIC_NOT_VALIDATED"
        )

        dim_str = f"{quality_info['dimensions'][0]}x{quality_info['dimensions'][1]}"

        return {
            "hazard_detected": hazard_detected,
            "hazard_type": hazard_type,
            "hazard_label": legacy_label,
            "evidence_strength": evidence_strength,
            "model_available": False,
            "trained_classifier": False,
            "model_type": model_type_desc,
            "scientific_status": status_desc,
            "image_quality": quality_info,
            "visual_features": visual_features,
            "evidence": evidence_notes,
            "confidence": None,                        # MUST be null without trained classifier
            "is_scientific_validated": False,          # Strictly false
            "notes": "Evidence extracted via deterministic color, texture, and spectral variance analysis. Not a trained classifier.",
            "image_dimensions": dim_str,
            "model_metadata": get_empty_model_metadata()
        }
    except Exception as e:
        audit_logger.error(f"Deterministic visual analyzer error: {e}")
        return {
            "hazard_detected": False,
            "hazard_type": "unclassified",
            "hazard_label": "unclassified",
            "evidence_strength": "LOW",
            "model_available": False,
            "trained_classifier": False,
            "model_type": "Deterministic Visual Evidence Analyzer",
            "scientific_status": "HEURISTIC_NOT_VALIDATED",
            "image_quality": quality_info,
            "visual_features": None,
            "evidence": [f"Processing error: {str(e)}"],
            "confidence": None,
            "is_scientific_validated": False,
            "notes": str(e),
            "model_metadata": get_empty_model_metadata()
        }
