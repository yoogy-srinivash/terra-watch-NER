def generate_recommendations(risk_level, reasons):

    recommendations = []

    if "Heavy rainfall detected" in reasons:
        recommendations.append(
            "Avoid vulnerable roads and mountain routes during heavy rainfall."
        )

    if "High soil moisture detected" in reasons:
        recommendations.append(
            "Stay away from unstable slopes and areas showing signs of ground movement."
        )

    if "Steep slope detected" in reasons:
        recommendations.append(
            "Avoid unnecessary movement near steep slopes and exposed hillside areas."
        )

    if risk_level == "HIGH":
        recommendations.append(
            "Monitor official weather and disaster-management warnings."
        )

    elif risk_level == "CRITICAL":
        recommendations.append(
            "Follow local authority warnings and instructions."
        )
        recommendations.append(
            "Prepare evacuation routes and essential emergency supplies."
        )

    if not recommendations:
        recommendations.append(
            "Continue monitoring weather conditions and official advisories."
        )

    return recommendations