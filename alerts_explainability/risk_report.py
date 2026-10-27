from risk_levels import get_risk_level
from alert_engine import generate_alert
from explainability import generate_reasons
from recommendations import generate_recommendations


def generate_risk_report(risk_score, rainfall, soil_moisture, slope):

    risk_level = get_risk_level(risk_score)

    alert = generate_alert(risk_score)

    reasons = generate_reasons(
        rainfall,
        soil_moisture,
        slope
    )

    recommendations = generate_recommendations(
        risk_level,
        reasons
    )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "features": {
            "rainfall": rainfall,
            "soil_moisture": soil_moisture,
            "slope": slope
        },
        "alert": alert,
        "reasons": reasons,
        "recommendations": recommendations
    }