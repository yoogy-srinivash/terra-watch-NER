def generate_reasons(rainfall, soil_moisture, slope, attributions=None):

    reasons = []

    if rainfall >= 100:
        reasons.append("Heavy rainfall detected")

    if soil_moisture >= 0.75:
        reasons.append("High soil moisture detected")

    if slope >= 30:
        reasons.append("Steep slope detected")

    # Integrate scientific feature attributions if available
    if attributions and isinstance(attributions, list):
        for attr in attributions:
            if isinstance(attr, str) and attr not in reasons:
                reasons.append(attr)

    if not reasons:
        reasons.append("No major contributing factors detected")

    return reasons