/* =========================================================
   LANDSAFE CONNECT - RISK ALERT CONTROLLER
   Full ML Model Telemetry & Emergency Advisory Bridge
========================================================= */

const riskData = {
    location: {
        name: "Guwahati, Assam",
        city: "Guwahati",
        latitude: 26.1445,
        longitude: 91.7362
    },
    overall: 72,
    flood: 76,
    landslide: 68,
    level: "HIGH",
    factors: {
        rainfall: 82,
        terrain: 64,
        water: 76
    }
};

function getElement(id) {
    return document.getElementById(id);
}

function getRiskStatus(score) {
    if (score >= 81) {
        return { label: "CRITICAL", alertClass: "alert-danger", badgeClass: "bg-dark text-white", color: "danger" };
    }
    if (score >= 61) {
        return { label: "HIGH", alertClass: "alert-warning", badgeClass: "bg-danger text-white", color: "danger" };
    }
    if (score >= 31) {
        return { label: "MODERATE", alertClass: "alert-warning", badgeClass: "bg-warning text-dark", color: "warning" };
    }
    return { label: "LOW", alertClass: "alert-success", badgeClass: "bg-success text-white", color: "success" };
}

function getFactorStatus(value) {
    if (value >= 75) return "High";
    if (value >= 50) return "Moderate";
    return "Low";
}

function renderRiskUI() {
    const overallRisk = getElement("overallRisk");
    const overallRiskStatus = getElement("overallRiskStatus");
    const floodRisk = getElement("floodRisk");
    const landslideRisk = getElement("landslideRisk");
    const floodProgress = getElement("floodProgress");
    const landslideProgress = getElement("landslideProgress");
    const rainfallProgress = getElement("rainfallProgress");
    const terrainProgress = getElement("terrainProgress");
    const waterProgress = getElement("waterProgress");
    const locationName = getElement("locationName");
    const latitude = getElement("latitude");
    const longitude = getElement("longitude");
    const rainfallStatus = getElement("rainfallStatus");
    const terrainStatus = getElement("terrainStatus");
    const waterStatus = getElement("waterStatus");
    const lastUpdated = getElement("lastUpdated");

    const status = getRiskStatus(riskData.overall);

    if (overallRisk) overallRisk.textContent = riskData.overall;

    if (overallRiskStatus) {
        overallRiskStatus.textContent = status.label;
        overallRiskStatus.className = `badge ${status.badgeClass} mt-1`;
    }

    if (floodRisk) floodRisk.textContent = `${riskData.flood}%`;
    if (landslideRisk) landslideRisk.textContent = `${riskData.landslide}%`;

    if (floodProgress) floodProgress.style.width = `${riskData.flood}%`;
    if (landslideProgress) landslideProgress.style.width = `${riskData.landslide}%`;

    if (rainfallProgress) rainfallProgress.style.width = `${riskData.factors.rainfall}%`;
    if (terrainProgress) terrainProgress.style.width = `${riskData.factors.terrain}%`;
    if (waterProgress) waterProgress.style.width = `${riskData.factors.water}%`;

    if (rainfallStatus) rainfallStatus.textContent = getFactorStatus(riskData.factors.rainfall);
    if (terrainStatus) terrainStatus.textContent = getFactorStatus(riskData.factors.terrain);
    if (waterStatus) waterStatus.textContent = getFactorStatus(riskData.factors.water);

    if (locationName) locationName.textContent = riskData.location.name;
    if (latitude) latitude.textContent = Number(riskData.location.latitude).toFixed(4);
    if (longitude) longitude.textContent = Number(riskData.location.longitude).toFixed(4);

    // Update Main Alert Banner
    const mainRiskAlert = getElement("mainRiskAlert");
    const alertTitle = getElement("alertTitle");
    const alertDescription = getElement("alertDescription");
    const alertBadge = getElement("alertBadge");

    if (mainRiskAlert) {
        mainRiskAlert.className = `alert ${status.alertClass} shadow-sm mb-3`;
    }

    if (alertTitle) {
        alertTitle.textContent = `${status.label} RISK ADVISORY: ${riskData.location.name}`;
    }

    if (alertDescription) {
        alertDescription.textContent = `${riskData.location.name} currently has a calculated risk level of ${riskData.overall}%. Geotechnical sensors and LightGBM models recommend continuous monitoring of slope corridors.`;
    }

    if (alertBadge) {
        alertBadge.textContent = `${status.label} RISK`;
        alertBadge.className = `badge ${status.badgeClass} px-3 py-2`;
    }

    if (lastUpdated) {
        const now = new Date();
        lastUpdated.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
}

async function fetchAlertRisk(cityName = "Guwahati") {
    const btn = getElement("btnRefreshAlertRisk");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Predicting...`;
    }

    try {
        if (window.LandSafeAPI && typeof window.LandSafeAPI.getLiveRisk === "function") {
            const live = await window.LandSafeAPI.getLiveRisk(cityName);
            if (live) {
                riskData.overall = live.overall;
                riskData.landslide = live.landslide;
                riskData.flood = live.flood;
                riskData.level = live.level || "HIGH";

                if (live.location) {
                    riskData.location.name = live.location.name;
                    riskData.location.city = live.location.city || cityName;
                    riskData.location.latitude = live.location.latitude;
                    riskData.location.longitude = live.location.longitude;
                }

                if (live.factors) {
                    riskData.factors.rainfall = live.factors.rainfall || 82;
                    riskData.factors.terrain = live.factors.slope || 64;
                    riskData.factors.water = live.factors.soil || 76;
                }

                renderRiskUI();

                if (window.LandSafeAPI && window.LandSafeAPI.showToast) {
                    window.LandSafeAPI.showToast(
                        `Risk calculation updated for ${riskData.location.name}: ${riskData.overall}% (${riskData.level})`,
                        riskData.overall >= 60 ? "warning" : "success"
                    );
                }
            }
        }
    } catch (e) {
        console.warn("[RiskAlert] Fetch failed:", e);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i class="bi bi-lightning-charge-fill me-1"></i> Predict Risk`;
        }
    }
}

function setupRiskAlertEvents() {
    const alertLocSelect = getElement("alertLocationSelect");
    if (alertLocSelect) {
        alertLocSelect.addEventListener("change", function(e) {
            fetchAlertRisk(e.target.value);
        });
    }

    const btnRefresh = getElement("btnRefreshAlertRisk");
    if (btnRefresh) {
        btnRefresh.addEventListener("click", function() {
            const sel = getElement("alertLocationSelect");
            fetchAlertRisk(sel ? sel.value : "Guwahati");
        });
    }

    const notificationButton = getElement("notificationButton");
    if (notificationButton) {
        notificationButton.addEventListener("click", async function () {
            if (window.LandSafeAPI) {
                try {
                    const alerts = await window.LandSafeAPI.getActiveAlerts();
                    if (alerts && alerts.length > 0) {
                        const alertTitles = alerts.slice(0, 3).map(a => `• [${a.severity}] ${a.title || (a.hazard_type + ' in ' + a.location)}`).join("\n");
                        if (window.LandSafeAPI.showToast) {
                            window.LandSafeAPI.showToast(`Active Early Warning Alerts:\n${alertTitles}`, "warning");
                        }
                        return;
                    }
                } catch (e) {}
            }
            if (window.LandSafeAPI && window.LandSafeAPI.showToast) {
                window.LandSafeAPI.showToast("All landslide corridors normal. Continuous telemetry streaming.", "info");
            }
        });
    }
}

async function initializeRiskAlertPage() {
    setupRiskAlertEvents();
    await fetchAlertRisk("Guwahati");
}

document.addEventListener("DOMContentLoaded", initializeRiskAlertPage);
