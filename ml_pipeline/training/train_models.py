import os
import sys
import json
import time
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

# NER Geographical Stations for domain calibration
NER_REGIONS = [
    {"state": "Arunachal Pradesh", "district": "Tawang", "lat": 27.58, "lon": 91.86, "base_elev": 3000, "tectonic": 1.4, "monsoon": 1.1},
    {"state": "Arunachal Pradesh", "district": "West Kameng", "lat": 27.26, "lon": 92.42, "base_elev": 2200, "tectonic": 1.4, "monsoon": 1.2},
    {"state": "Arunachal Pradesh", "district": "Papum Pare", "lat": 27.08, "lon": 93.60, "base_elev": 450, "tectonic": 1.2, "monsoon": 1.3},
    {"state": "Assam", "district": "Kamrup Metropolitan", "lat": 26.14, "lon": 91.73, "base_elev": 350, "tectonic": 1.0, "monsoon": 1.2},
    {"state": "Assam", "district": "Cachar", "lat": 24.83, "lon": 92.78, "base_elev": 180, "tectonic": 1.1, "monsoon": 1.3},
    {"state": "Assam", "district": "Karbi Anglong", "lat": 25.84, "lon": 93.43, "base_elev": 550, "tectonic": 1.2, "monsoon": 1.3},
    {"state": "Meghalaya", "district": "East Khasi Hills", "lat": 25.58, "lon": 91.89, "base_elev": 1500, "tectonic": 1.3, "monsoon": 2.2},
    {"state": "Meghalaya", "district": "West Garo Hills", "lat": 25.51, "lon": 90.20, "base_elev": 650, "tectonic": 1.2, "monsoon": 1.6},
    {"state": "Manipur", "district": "Imphal West", "lat": 24.81, "lon": 93.93, "base_elev": 780, "tectonic": 1.3, "monsoon": 1.3},
    {"state": "Manipur", "district": "Ukhrul", "lat": 25.10, "lon": 94.36, "base_elev": 1600, "tectonic": 1.4, "monsoon": 1.4},
    {"state": "Mizoram", "district": "Aizawl", "lat": 23.72, "lon": 92.71, "base_elev": 1130, "tectonic": 1.4, "monsoon": 1.4},
    {"state": "Mizoram", "district": "Lunglei", "lat": 22.88, "lon": 92.73, "base_elev": 1200, "tectonic": 1.4, "monsoon": 1.3},
    {"state": "Nagaland", "district": "Kohima", "lat": 25.67, "lon": 94.10, "base_elev": 1444, "tectonic": 1.4, "monsoon": 1.3},
    {"state": "Nagaland", "district": "Mokokchung", "lat": 26.32, "lon": 94.52, "base_elev": 1320, "tectonic": 1.3, "monsoon": 1.2},
    {"state": "Sikkim", "district": "Gangtok", "lat": 27.33, "lon": 88.60, "base_elev": 1650, "tectonic": 1.6, "monsoon": 1.5},
    {"state": "Sikkim", "district": "Mangan", "lat": 27.50, "lon": 88.53, "base_elev": 1800, "tectonic": 1.7, "monsoon": 1.6},
    {"state": "Tripura", "district": "West Tripura", "lat": 23.83, "lon": 91.28, "base_elev": 150, "tectonic": 1.0, "monsoon": 1.1},
    {"state": "Tripura", "district": "North Tripura", "lat": 24.36, "lon": 92.16, "base_elev": 220, "tectonic": 1.1, "monsoon": 1.2}
]

NUM_COLS = [
    "elevation_m", "slope_angle_deg", "aspect_deg", "plan_curvature", "profile_curvature",
    "soil_depth_m", "ndvi", "distance_to_road_m", "distance_to_fault_m", "distance_to_stream_m",
    "rainfall_24h_mm", "rainfall_72h_mm", "rainfall_intensity_mm_h",
    "soil_moisture_pct", "pore_pressure_kpa", "ground_vibration_g"
]
CAT_COLS = ["state", "lithology", "soil_type", "land_use"]

def generate_calibrated_dataset(n_samples=7000):
    print(f"Generating {n_samples} domain-calibrated NER training samples across 8 states...")
    np.random.seed(42)
    records = []
    
    litho_types = ["Soft Shale/Mudstone", "Weathered Phyllite/Schist", "Sandstone with Silt Interbeds", "Hard Quartzite", "Granite/Gneiss Complex"]
    litho_vuln = {"Soft Shale/Mudstone": 1.40, "Weathered Phyllite/Schist": 1.30, "Sandstone with Silt Interbeds": 1.05, "Hard Quartzite": 0.65, "Granite/Gneiss Complex": 0.50}
    
    soil_types = ["Weathered Debris/Talus", "Red Sandy-Clay Loam", "Silty Loam", "Residual Clay"]
    soil_vuln = {"Weathered Debris/Talus": 1.35, "Red Sandy-Clay Loam": 1.10, "Silty Loam": 0.95, "Residual Clay": 0.80}
    
    land_types = ["Roadside Cut Slope", "Shifting Cultivation (Jhum)", "Degraded Forest", "Dense Mountain Forest", "Settlement/Infrastructure"]
    land_vuln = {"Roadside Cut Slope": 1.50, "Shifting Cultivation (Jhum)": 1.30, "Degraded Forest": 1.15, "Settlement/Infrastructure": 1.10, "Dense Mountain Forest": 0.55}

    for i in range(n_samples):
        reg = NER_REGIONS[np.random.choice(len(NER_REGIONS))]
        slope_angle = round(float(np.random.beta(2.2, 3.2) * 52.0 + 8.0), 1)
        aspect = round(float(np.random.uniform(0, 360)), 1)
        exposure = 0.5 * (1.0 - np.cos(np.radians(aspect) - np.radians(205)))
        
        lithology = np.random.choice(litho_types, p=[0.35, 0.28, 0.22, 0.08, 0.07])
        soil_type = np.random.choice(soil_types, p=[0.35, 0.35, 0.20, 0.10])
        land_use = np.random.choice(land_types, p=[0.22, 0.20, 0.25, 0.23, 0.10])
        
        ndvi = round(float(np.random.uniform(0.65, 0.88) if land_use == "Dense Mountain Forest" else np.random.uniform(0.10, 0.45)), 3)
        road_dist = round(float(np.random.exponential(35) + 5 if land_use == "Roadside Cut Slope" else np.random.exponential(450) + 50), 1)
        fault_dist = round(float(np.random.exponential(2500) + 100), 1)
        stream_dist = round(float(np.random.exponential(350) + 20), 1)
        
        is_monsoon = np.random.rand() < 0.35
        m_factor = reg["monsoon"] * (1.0 + 0.25 * exposure)
        
        if is_monsoon:
            r24 = round(float(np.random.gamma(3.2, 32.0) * m_factor), 1)
            r72 = round(float(r24 * np.random.uniform(1.6, 2.8) + np.random.uniform(20, 80)), 1)
            soil_moist = round(float(np.clip(60.0 + (r72 / 12.0) + np.random.normal(0, 5), 45, 98)), 1)
            pore_p = round(float(np.clip((soil_moist - 35) * 0.42 + np.random.normal(0, 2), 2, 42)), 1)
        else:
            r24 = round(float(np.random.exponential(12.0) * (m_factor * 0.4)), 1)
            r72 = round(float(r24 * np.random.uniform(1.2, 1.8) + np.random.uniform(0, 15)), 1)
            soil_moist = round(float(np.clip(np.random.normal(32, 10), 10, 58)), 1)
            pore_p = round(float(np.clip(soil_moist * 0.08 + np.random.normal(0, 1.5), 0.5, 12)), 1)
            
        rad = np.radians(slope_angle)
        driving = (np.sin(rad) * 1.50 + 0.3 + (pore_p / 20.0) * 1.20) * (1.45 if road_dist < 40 else 1.0) * (reg["tectonic"] ** 0.5)
        resisting = (np.cos(rad) * np.tan(np.radians(28)) * 1.70 * (0.8 + 0.5 * ndvi)) / (litho_vuln[lithology] * soil_vuln[soil_type] * land_vuln[land_use])
        
        sm_excess = max(0.0, soil_moist - 40.0)
        rain_trig = (r24 / 110.0)**1.4 + (r72 / 230.0)**1.3 + (sm_excess / 45.0)**2.0
        instability = (driving / (resisting + 0.05)) * 0.38 + (rain_trig * 0.62)
        
        prob = 1.0 / (1.0 + np.exp(-4.2 * (instability - 1.0)))
        prob = float(np.clip(prob + np.random.normal(0, 0.02), 0.001, 0.999))
        
        records.append({
            "state": reg["state"], "district": reg["district"],
            "elevation_m": max(120, round(float(reg["base_elev"] + np.random.normal(0, 250)), 1)),
            "slope_angle_deg": slope_angle, "aspect_deg": aspect,
            "plan_curvature": round(float(np.random.normal(0, 0.05)), 3),
            "profile_curvature": round(float(np.random.normal(0, 0.05)), 3),
            "lithology": lithology, "soil_type": soil_type, "soil_depth_m": 2.5,
            "land_use": land_use, "ndvi": ndvi,
            "distance_to_road_m": road_dist, "distance_to_fault_m": fault_dist,
            "distance_to_stream_m": stream_dist, "rainfall_24h_mm": r24,
            "rainfall_72h_mm": r72, "rainfall_intensity_mm_h": round(r24 / 10.0, 1),
            "soil_moisture_pct": soil_moist, "pore_pressure_kpa": pore_p,
            "ground_vibration_g": round(float(np.random.exponential(0.005) + 0.001), 4),
            "landslide_occurred": 1 if prob >= 0.50 else 0
        })
        
    df = pd.DataFrame(records)
    print(f"Dataset generated with positive class rate: {df['landslide_occurred'].mean()*100:.1f}%")
    return df

def build_preprocessor():
    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    return ColumnTransformer([
        ("num", num_pipe, NUM_COLS),
        ("cat", cat_pipe, CAT_COLS)
    ])

def train_and_benchmark(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    X = df[NUM_COLS + CAT_COLS]
    y = df["landslide_occurred"].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    models = {
        "Random Forest Classifier": RandomForestClassifier(
            n_estimators=150, max_depth=14, class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "Gradient Boosting (GBDT)": GradientBoostingClassifier(
            n_estimators=150, learning_rate=0.08, max_depth=5, random_state=42
        ),
        "Logistic Regression": LogisticRegression(
            C=1.0, max_iter=1000, random_state=42
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=9, random_state=42
        )
    }
    
    if HAS_XGB:
        models["XGBoost Classifier"] = xgb.XGBClassifier(
            n_estimators=180, learning_rate=0.07, max_depth=6,
            subsample=0.85, colsample_bytree=0.85, eval_metric="logloss",
            random_state=42, n_jobs=-1
        )
        
    if HAS_LGB:
        models["LightGBM Classifier"] = lgb.LGBMClassifier(
            n_estimators=180, learning_rate=0.07, max_depth=6,
            random_state=42, n_jobs=-1, verbose=-1
        )

    results = []
    trained_pipelines = {}
    
    print("\nBenchmarking AI/ML Models (Prioritizing Disaster Recall & ROC-AUC)...")
    for name, clf in models.items():
        t0 = time.time()
        pipe = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("classifier", clf)
        ])
        pipe.fit(X_train, y_train)
        elapsed = time.time() - t0
        
        y_pred = pipe.predict(X_test)
        y_proba = pipe.predict_proba(X_test)[:, 1] if hasattr(pipe, "predict_proba") else y_pred
        
        rec = recall_score(y_test, y_pred, zero_division=0)
        roc = roc_auc_score(y_test, y_proba)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        prec = precision_score(y_test, y_pred, zero_division=0)
        acc = accuracy_score(y_test, y_pred)
        pr_auc = average_precision_score(y_test, y_proba)
        
        # Disaster Early Warning Composite Score
        composite = (0.35 * rec) + (0.30 * roc) + (0.20 * f1) + (0.15 * pr_auc)
        
        results.append({
            "Model": name,
            "Recall (Sensitivity)": round(rec * 100, 2),
            "ROC-AUC": round(roc, 4),
            "F1-Score": round(f1, 4),
            "Precision": round(prec * 100, 2),
            "Accuracy": round(acc * 100, 2),
            "Composite Disaster Score": round(composite, 4),
            "Training Time (s)": round(elapsed, 2)
        })
        trained_pipelines[name] = {"pipeline": pipe, "score": composite}
        print(f"  -> {name:<26} | Recall: {rec*100:.1f}% | ROC-AUC: {roc:.4f} | F1: {f1:.4f} | Disaster Score: {composite:.4f}")

    results_df = pd.DataFrame(results).sort_values(by="Composite Disaster Score", ascending=False).reset_index(drop=True)
    benchmark_csv = os.path.join(output_dir, "benchmark_results.csv")
    results_df.to_csv(benchmark_csv, index=False)
    
    best_name = results_df.iloc[0]["Model"]
    best_pipeline = trained_pipelines[best_name]["pipeline"]
    model_path = os.path.join(output_dir, "best_landslide_model.joblib")
    joblib.dump(best_pipeline, model_path)
    
    # Standby Model Selection (prefer XGBoost Classifier or runner-up model)
    standby_name = None
    for candidate in ["XGBoost Classifier", "Random Forest Classifier", "Gradient Boosting (GBDT)"]:
        if candidate in trained_pipelines and candidate != best_name:
            standby_name = candidate
            break
    if not standby_name and len(results_df) > 1:
        standby_name = results_df.iloc[1]["Model"]

    standby_path = None
    standby_metrics = {}
    if standby_name and standby_name in trained_pipelines:
        standby_pipeline = trained_pipelines[standby_name]["pipeline"]
        standby_path = os.path.join(output_dir, "standby_landslide_model.joblib")
        joblib.dump(standby_pipeline, standby_path)
        standby_row = results_df[results_df["Model"] == standby_name].iloc[0]
        standby_metrics = standby_row.to_dict()
        print(f"Standby Model Saved: {standby_name} -> {standby_path}")

    metadata = {
        "best_model": best_name,
        "active_model": best_name,
        "standby_model": standby_name,
        "metrics": results_df.iloc[0].to_dict(),
        "standby_metrics": standby_metrics,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": NUM_COLS + CAT_COLS,
        "n_samples": len(df)
    }
    with open(os.path.join(output_dir, "best_model_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"\nWinning Model Saved: {best_name} -> {model_path}")
    print(f"Benchmark Saved: {benchmark_csv}")
    return best_pipeline, results_df

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "backend" / "models"
    data_dir = base_dir / "backend" / "data"
    os.makedirs(data_dir, exist_ok=True)
    
    df = generate_calibrated_dataset(7000)
    dataset_path = data_dir / "ner_landslide_dataset.csv"
    df.to_csv(dataset_path, index=False)
    print(f"Dataset saved to: {dataset_path}")
    
    train_and_benchmark(df, str(output_dir))
