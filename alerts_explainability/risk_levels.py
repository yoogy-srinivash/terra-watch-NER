def get_risk_level(risk_score):

    if risk_score >= 0.80:
        return "CRITICAL"

    elif risk_score >= 0.60:
        return "HIGH"

    elif risk_score >= 0.40:
        return "MODERATE"

    elif risk_score >= 0.20:
        return "LOW"

    else:
        return "VERY LOW"