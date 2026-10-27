from risk_levels import get_risk_level


def generate_alert(risk_score):

    risk_level = get_risk_level(risk_score)

    alerts = {
        "VERY LOW": {
            "title": "Very Low Landslide Risk",
            "message": "No significant landslide risk detected. Continue normal activities."
        },

        "LOW": {
            "title": "Low Landslide Risk",
            "message": "Landslide risk is currently low. Continue monitoring weather conditions."
        },

        "MODERATE": {
            "title": "Moderate Landslide Risk",
            "message": "Moderate landslide risk detected. Exercise caution near vulnerable areas."
        },

        "HIGH": {
            "title": "High Landslide Risk",
            "message": "High landslide risk detected. Avoid vulnerable areas and monitor official warnings."
        },

        "CRITICAL": {
            "title": "Critical Landslide Risk",
            "message": "Critical landslide risk detected. Take immediate precautions and follow local authority warnings."
        }
    }

    return {
        "risk_level": risk_level,
        "title": alerts[risk_level]["title"],
        "message": alerts[risk_level]["message"]
    }