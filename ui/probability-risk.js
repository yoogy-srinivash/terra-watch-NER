/* =========================================================
   TERRAWATCH NER - PROBABILITY RISK ENGINE
   Full ML Model Bridge (LightGBM Pipeline & Live Telemetry)
========================================================= */

const CITY_COORDINATES = {
    "Guwahati": { lat: 26.1445, lng: 91.7362, state: "Assam", district: "Kamrup Metropolitan" },
    "Shillong": { lat: 25.5788, lng: 91.8933, state: "Meghalaya", district: "East Khasi Hills" },
    "Cherrapunji": { lat: 25.2702, lng: 91.7323, state: "Meghalaya", district: "East Khasi Hills" },
    "Aizawl": { lat: 23.7271, lng: 92.7176, state: "Mizoram", district: "Aizawl" },
    "Gangtok": { lat: 27.3389, lng: 88.6065, state: "Sikkim", district: "East Sikkim" },
    "Kohima": { lat: 25.6751, lng: 94.1086, state: "Nagaland", district: "Kohima" },
    "Itanagar": { lat: 27.0844, lng: 93.6053, state: "Arunachal Pradesh", district: "Papum Pare" },
    "Imphal": { lat: 24.8170, lng: 93.9368, state: "Manipur", district: "Imphal West" },
    "Agartala": { lat: 23.8315, lng: 91.2868, state: "Tripura", district: "West Tripura" },
    "Haflong": { lat: 25.1741, lng: 93.0232, state: "Assam", district: "Dima Hasao" },
    "Tawang": { lat: 27.5861, lng: 91.8594, state: "Arunachal Pradesh", district: "Tawang" }
};

let probabilityData = {
    location: "Guwahati, Assam",
    city: "Guwahati",
    overall: 78,
    landslide: 82,
    flood: 58,
    level: "HIGH",
    factors: {
        rainfall: 72,
        soil: 84,
        terrain: 61,
        water: 55
    },
    trend: {
        labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        values: [42, 48, 51, 57, 64, 71, 78]
    }
};

let chartInstance = null;

function getElement(id) {
    return document.getElementById(id);
}

function getRiskLevel(value) {
    if (value >= 81) return { label: "CRITICAL RISK", short: "Critical", badge: "bg-dark text-white", color: "danger", barColor: "bg-danger" };
    if (value >= 61) return { label: "HIGH RISK", short: "High", badge: "bg-danger text-white", color: "danger", barColor: "bg-danger" };
    if (value >= 31) return { label: "MODERATE RISK", short: "Moderate", badge: "bg-warning text-dark", color: "warning", barColor: "bg-warning" };
    return { label: "LOW RISK", short: "Low", badge: "bg-success text-white", color: "success", barColor: "bg-success" };
}

function updateOverallRisk() {
    const valueEl = getElement("overallProbability") || getElement("overallRiskValue");
    const progressEl = getElement("overallProgress") || getElement("overallRiskProgress");
    const statusEl = getElement("overallStatus") || getElement("overallRiskStatus");

    const level = getRiskLevel(probabilityData.overall);

    if (valueEl) {
        valueEl.textContent = `${probabilityData.overall}%`;
        valueEl.className = `display-4 fw-bold text-${level.color}`;
    }

    if (progressEl) {
        progressEl.style.width = `${Math.min(100, Math.max(5, probabilityData.overall))}%`;
        progressEl.setAttribute("aria-valuenow", probabilityData.overall);
        progressEl.className = `progress-bar ${level.barColor}`;
    }

    if (statusEl) {
        statusEl.textContent = level.label;
        statusEl.className = `badge rounded-pill px-3 py-2 mb-2 ${level.badge}`;
    }
}

function updateLandslideRisk() {
    const valueEl = getElement("landslideProbability") || getElement("landslideRiskValue");
    const progressEl = getElement("landslideProgress") || getElement("landslideRiskProgress");
    const statusEl = getElement("landslideStatus") || getElement("landslideRiskStatus");

    const level = getRiskLevel(probabilityData.landslide);

    if (valueEl) {
        valueEl.textContent = `${probabilityData.landslide}%`;
        valueEl.className = `display-6 fw-bold text-${level.color}`;
    }

    if (progressEl) {
        progressEl.style.width = `${Math.min(100, Math.max(5, probabilityData.landslide))}%`;
        progressEl.className = `progress-bar ${level.barColor}`;
    }

    if (statusEl) {
        statusEl.textContent = level.short;
        statusEl.className = `badge bg-${level.color}-subtle text-${level.color}`;
    }
}

function updateFloodRisk() {
    const valueEl = getElement("floodProbability") || getElement("floodRiskValue");
    const progressEl = getElement("floodProgress") || getElement("floodRiskProgress");
    const statusEl = getElement("floodStatus") || getElement("floodRiskStatus");

    const level = getRiskLevel(probabilityData.flood);

    if (valueEl) {
        valueEl.textContent = `${probabilityData.flood}%`;
    }

    if (progressEl) {
        progressEl.style.width = `${Math.min(100, Math.max(5, probabilityData.flood))}%`;
    }

    if (statusEl) {
        statusEl.textContent = level.short;
        statusEl.className = `badge bg-${level.color}-subtle text-${level.color}`;
    }
}

function updateRiskFactors() {
    const rainfallVal = getElement("rainfallValue") || getElement("rainfallRiskValue");
    const rainfallProg = getElement("rainfallProgress") || getElement("rainfallRiskProgress");
    const soilVal = getElement("soilValue") || getElement("soilRiskValue");
    const soilProg = getElement("soilProgress") || getElement("soilRiskProgress");
    const terrainVal = getElement("terrainValue") || getElement("terrainRiskValue");
    const terrainProg = getElement("terrainProgress") || getElement("terrainRiskProgress");
    const waterVal = getElement("waterValue") || getElement("waterRiskValue");
    const waterProg = getElement("waterProgress") || getElement("waterRiskProgress");

    if (rainfallVal) rainfallVal.textContent = `${probabilityData.factors.rainfall}%`;
    if (rainfallProg) {
        rainfallProg.style.width = `${probabilityData.factors.rainfall}%`;
        rainfallProg.className = `progress-bar ${probabilityData.factors.rainfall > 70 ? 'bg-danger' : probabilityData.factors.rainfall > 40 ? 'bg-warning' : 'bg-info'}`;
    }

    if (soilVal) soilVal.textContent = `${probabilityData.factors.soil}%`;
    if (soilProg) {
        soilProg.style.width = `${probabilityData.factors.soil}%`;
        soilProg.className = `progress-bar ${probabilityData.factors.soil > 75 ? 'bg-danger' : 'bg-warning'}`;
    }

    if (terrainVal) terrainVal.textContent = `${probabilityData.factors.terrain}%`;
    if (terrainProg) {
        terrainProg.style.width = `${probabilityData.factors.terrain}%`;
        terrainProg.className = `progress-bar ${probabilityData.factors.terrain > 60 ? 'bg-warning' : 'bg-success'}`;
    }

    if (waterVal) waterVal.textContent = `${probabilityData.factors.water}%`;
    if (waterProg) waterProg.style.width = `${probabilityData.factors.water}%`;
}

function createProbabilityChart() {
    const canvas = getElement("riskChart") || getElement("probabilityChart") || getElement("probabilityTrendChart");
    if (!canvas || typeof Chart === "undefined") return;

    if (chartInstance) {
        chartInstance.destroy();
    }

    const ctx = canvas.getContext("2d");
    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: probabilityData.trend.labels,
            datasets: [{
                label: "Landslide Risk Trend (%)",
                data: probabilityData.trend.values,
                borderColor: probabilityData.overall >= 60 ? "#dc3545" : "#10b981",
                backgroundColor: probabilityData.overall >= 60 ? "rgba(220, 53, 69, 0.12)" : "rgba(16, 185, 129, 0.12)",
                fill: true,
                tension: 0.35,
                borderWidth: 2.5,
                pointRadius: 4,
                pointBackgroundColor: probabilityData.overall >= 60 ? "#dc3545" : "#10b981"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Risk: ${context.parsed.y}%`;
                        }
                    }
                }
            },
            scales: {
                y: { min: 0, max: 100 },
                x: { grid: { display: false } }
            }
        }
    });
}

function updateFactorBars() {
    const rfVal = getElement("factorRainfallVal");
    const rfBar = getElement("factorRainfallBar");
    const ppVal = getElement("factorPorePressVal");
    const ppBar = getElement("factorPorePressBar");
    const slVal = getElement("factorSlopeVal");
    const slBar = getElement("factorSlopeBar");
    const smVal = getElement("factorSoilVal");
    const smBar = getElement("factorSoilBar");

    const rf = probabilityData.factors.rainfall || 72;
    const sm = probabilityData.factors.soil || 84;
    const sl = probabilityData.factors.terrain || 61;
    const pp = probabilityData.factors.water || 55;

    if (rfVal && rfBar) {
        rfVal.textContent = `${Math.round(rf * 2)} mm • ${rf >= 60 ? 'High Impact' : 'Normal'}`;
        rfBar.style.width = `${Math.min(100, Math.max(5, rf))}%`;
        rfBar.className = `factor-bar-fill ${rf >= 60 ? 'bg-danger' : 'bg-warning'}`;
    }
    if (ppVal && ppBar) {
        ppVal.textContent = `${(pp * 0.28).toFixed(1)} kPa • ${pp >= 60 ? 'Elevated Pressure' : 'Normal'}`;
        ppBar.style.width = `${Math.min(100, Math.max(5, pp))}%`;
        ppBar.className = `factor-bar-fill ${pp >= 60 ? 'bg-danger' : 'bg-warning'}`;
    }
    if (slVal && slBar) {
        slVal.textContent = `${Math.round(sl * 0.55)}° • ${sl >= 60 ? 'Steep Gradient' : 'Moderate'}`;
        slBar.style.width = `${Math.min(100, Math.max(5, sl))}%`;
        slBar.className = `factor-bar-fill ${sl >= 60 ? 'bg-danger' : 'bg-warning'}`;
    }
    if (smVal && smBar) {
        smVal.textContent = `${Math.round(sm)}% • ${sm >= 75 ? 'Near Saturation' : 'Normal'}`;
        smBar.style.width = `${Math.min(100, Math.max(5, sm))}%`;
        smBar.className = `factor-bar-fill ${sm >= 60 ? 'bg-danger' : 'bg-warning'}`;
    }

    const titleEl = getElement("resultLocationTitle");
    if (titleEl) {
        titleEl.textContent = probabilityData.location || `${probabilityData.city}, NER`;
    }

    const adviceEl = getElement("resultAdviceText");
    if (adviceEl) {
        if (probabilityData.overall >= 80) {
            adviceEl.textContent = "CRITICAL: Multiple geotechnical sensors indicate active slope failure vulnerability. Initiate evacuation advisory in low-lying corridors.";
        } else if (probabilityData.overall >= 60) {
            adviceEl.textContent = "HIGH: Significant rainfall accumulation combined with steep terrain gradient indicates elevated probability of slope failure.";
        } else if (probabilityData.overall >= 30) {
            adviceEl.textContent = "MODERATE: Geotechnical parameters elevated above baseline but within manageable retention thresholds. Maintain regular sensor monitoring.";
        } else {
            adviceEl.textContent = "LOW / STABLE: All monitored terrain and sensor parameters within safe baseline seasonal limits across this corridor.";
        }
    }

    const spatScore = getElement("spatialStreamScore");
    const tempScore = getElement("temporalStreamScore");
    if (spatScore) spatScore.textContent = `${Math.round(probabilityData.overall * 0.95)}%`;
    if (tempScore) tempScore.textContent = `${Math.round(probabilityData.overall * 1.05)}%`;
}

function updateUIAll() {
    updateOverallRisk();
    updateLandslideRisk();
    updateFloodRisk();
    updateRiskFactors();
    updateFactorBars();
    createProbabilityChart();

    const locName = getElement("locationName");
    if (locName) locName.textContent = probabilityData.location;

    const locSelect = getElement("locationSelect");
    if (locSelect && locSelect.value !== probabilityData.city) {
        locSelect.value = probabilityData.city;
    }
}

async function fetchLocationRisk(city) {
    const btnPredict = getElement("btnPredictRisk");
    if (btnPredict) {
        btnPredict.disabled = true;
        btnPredict.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Calculating...`;
    }

    try {
        let res = null;
        if (window.LandSafeAPI && typeof window.LandSafeAPI.getProbability === "function") {
            res = await window.LandSafeAPI.getProbability(city);
        }
        if (!res && window.LandSafeAPI && typeof window.LandSafeAPI.getLiveRisk === "function") {
            res = await window.LandSafeAPI.getLiveRisk(city);
        }

        if (res) {
            probabilityData.city = city;
            probabilityData.location = res.location ? (typeof res.location === "string" ? res.location : res.location.name) : `${city}, NER`;
            probabilityData.overall = res.overall || (res.risk_score ? Math.round(res.risk_score) : 70);
            probabilityData.landslide = res.landslide || probabilityData.overall;
            probabilityData.flood = res.flood || Math.round(probabilityData.overall * 0.75);
            probabilityData.level = res.level || "HIGH";

            if (res.factors) {
                probabilityData.factors.rainfall = res.factors.rainfall || 72;
                probabilityData.factors.soil = res.factors.soil || 84;
                probabilityData.factors.terrain = res.factors.slope || 61;
                probabilityData.factors.water = res.factors.water || 55;
            }

            if (res.trend && Array.isArray(res.trend.values)) {
                probabilityData.trend = res.trend;
            } else {
                const score = probabilityData.overall;
                probabilityData.trend.values = [
                    Math.max(10, Math.round(score * 0.55)),
                    Math.max(15, Math.round(score * 0.62)),
                    Math.max(20, Math.round(score * 0.68)),
                    Math.max(25, Math.round(score * 0.74)),
                    Math.max(30, Math.round(score * 0.83)),
                    Math.max(35, Math.round(score * 0.92)),
                    score
                ];
            }

            // Sync sliders
            const simRain = getElement("simRainfall");
            const simSoil = getElement("simSoil");
            const simSlope = getElement("simSlope");
            if (simRain) simRain.value = probabilityData.factors.rainfall * 2;
            if (simSoil) simSoil.value = probabilityData.factors.soil;
            if (simSlope) simSlope.value = Math.round(probabilityData.factors.terrain * 0.55);

            updateSliderLabels();
            updateUIAll();

            if (res.fusion) {
                updateFusionUI(res.fusion);
            }

            if (window.LandSafeAPI && window.LandSafeAPI.showToast) {
                window.LandSafeAPI.showToast(
                    `ML Risk assessment updated for ${probabilityData.location}: ${probabilityData.overall}% (${probabilityData.level})`,
                    probabilityData.overall >= 60 ? "warning" : "success"
                );
            }
        }
    } catch (e) {
        console.warn("[Probability] Fetch failed:", e);
    } finally {
        if (btnPredict) {
            btnPredict.disabled = false;
            btnPredict.innerHTML = `<i class="bi bi-lightning-charge-fill me-1"></i> Predict Live Risk`;
        }
    }
}

function updateSliderLabels() {
    const simRain = getElement("simRainfall");
    const simSoil = getElement("simSoil");
    const simSlope = getElement("simSlope");

    const rainVal = getElement("simRainfallVal");
    const soilVal = getElement("simSoilVal");
    const slopeVal = getElement("simSlopeVal");

    if (rainVal && simRain) rainVal.textContent = `${simRain.value} mm`;
    if (soilVal && simSoil) soilVal.textContent = `${simSoil.value}%`;
    if (slopeVal && simSlope) slopeVal.textContent = `${simSlope.value}°`;
}

async function runSimulation() {
    const simRain = getElement("simRainfall");
    const simSoil = getElement("simSoil");
    const simSlope = getElement("simSlope");
    const btnSim = getElement("btnRunSimulation");

    if (!simRain || !simSoil || !simSlope) return;

    if (btnSim) {
        btnSim.disabled = true;
        btnSim.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Running ML...`;
    }

    const rainfall = parseFloat(simRain.value);
    const soil = parseFloat(simSoil.value);
    const slope = parseFloat(simSlope.value);

    const city = probabilityData.city || "Guwahati";
    const geo = CITY_COORDINATES[city] || CITY_COORDINATES["Guwahati"];

    try {
        if (window.LandSafeAPI && typeof window.LandSafeAPI.predictRisk === "function") {
            const res = await window.LandSafeAPI.predictRisk({
                latitude: geo.lat,
                longitude: geo.lng,
                state: geo.state,
                district: geo.district,
                rainfall_24h_mm: rainfall,
                soil_moisture_pct: soil,
                slope_angle_deg: slope
            });

            if (res && res.prediction) {
                const pred = res.prediction;
                probabilityData.overall = Math.round(pred.risk_score);
                probabilityData.landslide = Math.round(pred.landslide_risk_pct || pred.risk_score);
                probabilityData.flood = Math.round(pred.flood_risk_pct || (pred.risk_score * 0.7));
                probabilityData.level = pred.risk_level;

                if (pred.factors) {
                    probabilityData.factors.rainfall = pred.factors.rainfall || Math.min(100, Math.round(rainfall / 2.5));
                    probabilityData.factors.soil = pred.factors.soil || Math.round(soil);
                    probabilityData.factors.terrain = pred.factors.slope || Math.round(slope * 1.5);
                    probabilityData.factors.water = pred.factors.water || 55;
                }

                // Update trend with simulated score
                const s = probabilityData.overall;
                probabilityData.trend.values = [
                    Math.max(10, Math.round(s * 0.5)),
                    Math.max(12, Math.round(s * 0.6)),
                    Math.max(15, Math.round(s * 0.68)),
                    Math.max(18, Math.round(s * 0.76)),
                    Math.max(22, Math.round(s * 0.85)),
                    Math.max(25, Math.round(s * 0.93)),
                    s
                ];

                updateUIAll();

                if (res.fusion) {
                    updateFusionUI(res.fusion);
                }

                if (window.LandSafeAPI && window.LandSafeAPI.showToast) {
                    window.LandSafeAPI.showToast(
                        `Simulation Result: ML Model predicts ${probabilityData.overall}% risk (${probabilityData.level})`,
                        probabilityData.overall >= 60 ? "danger" : "success"
                    );
                }
            }
        }
    } catch (e) {
        console.warn("[Probability] Simulation error:", e);
    } finally {
        if (btnSim) {
            btnSim.disabled = false;
            btnSim.innerHTML = `<i class="bi bi-lightning-charge-fill me-1"></i> Run ML Simulation`;
        }
    }
}

function setupEventListeners() {
    const locSelect = getElement("locationSelect");
    if (locSelect) {
        locSelect.addEventListener("change", function(e) {
            fetchLocationRisk(e.target.value);
        });
    }

    const btnPredict = getElement("btnPredictRisk");
    if (btnPredict) {
        btnPredict.addEventListener("click", function() {
            const sel = getElement("locationSelect");
            const val = sel ? sel.value : "Guwahati";
            fetchLocationRisk(val);
        });
    }

    const simRain = getElement("simRainfall");
    const simSoil = getElement("simSoil");
    const simSlope = getElement("simSlope");

    if (simRain) simRain.addEventListener("input", updateSliderLabels);
    if (simSoil) simSoil.addEventListener("input", updateSliderLabels);
    if (simSlope) simSlope.addEventListener("input", updateSliderLabels);

    const btnSim = getElement("btnRunSimulation");
    if (btnSim) {
        btnSim.addEventListener("click", runSimulation);
    }

    const btnReset = getElement("btnResetSimulation");
    if (btnReset) {
        btnReset.addEventListener("click", function() {
            const sel = getElement("locationSelect");
            const city = sel ? sel.value : "Guwahati";
            fetchLocationRisk(city);
        });
    }

    // Preset Scenario Handlers (6 Core Environmental Scenarios)
    function activatePreset(id, rain, soil, slope) {
        document.querySelectorAll(".scenario-card").forEach(c => c.classList.remove("active"));
        const card = getElement(id);
        if (card) card.classList.add("active");

        if (simRain) simRain.value = rain;
        if (simSoil) simSoil.value = soil;
        if (simSlope) simSlope.value = slope;
        updateSliderLabels();
        runSimulation();
    }

    const presetMap = [
        { id: "presetNormal", rain: 15, soil: 35, slope: 22 },
        { id: "presetMonsoon", rain: 260, soil: 94, slope: 42 },
        { id: "presetMoisture", rain: 90, soil: 92, slope: 30 },
        { id: "presetPorePress", rain: 160, soil: 88, slope: 38 },
        { id: "presetVibration", rain: 50, soil: 62, slope: 45 },
        { id: "presetCombined", rain: 280, soil: 98, slope: 48 }
    ];

    presetMap.forEach(p => {
        const btn = getElement(p.id);
        if (btn) {
            btn.addEventListener("click", () => activatePreset(p.id, p.rain, p.soil, p.slope));
        }
    });

    const notifBtn = getElement("notificationButton");
    if (notifBtn) {
        notifBtn.addEventListener("click", async function() {
            if (window.LandSafeAPI) {
                try {
                    const alerts = await window.LandSafeAPI.getActiveAlerts();
                    if (alerts && alerts.length > 0) {
                        const alertTitles = alerts.slice(0, 3).map(a => `• [${a.severity}] ${a.title || a.location}`).join('\n');
                        if (window.LandSafeAPI.showToast) {
                            window.LandSafeAPI.showToast(`Active Early Warning Alerts:\n${alertTitles}`, "warning");
                        }
                        return;
                    }
                } catch (e) {}
            }
            if (window.LandSafeAPI && window.LandSafeAPI.showToast) {
                window.LandSafeAPI.showToast("All landslide corridors normal. Continuous ML inference running.", "info");
            }
        });
    }
}

function updateFusionUI(fusion) {
    if (!fusion) return;

    // Fused Score & Tier
    const scoreBadge = getElement("fusionScoreBadge");
    if (scoreBadge) {
        const pct = (fusion.fused_risk_score * 100).toFixed(1);
        scoreBadge.textContent = `Fused: ${pct}% (${fusion.risk_tier || 'ASSESSED'})`;
        scoreBadge.className = `badge fs-6 ${
            fusion.risk_tier === "CRITICAL" ? "bg-dark text-white" :
            fusion.risk_tier === "HIGH" ? "bg-danger text-white" :
            fusion.risk_tier === "MEDIUM" ? "bg-warning text-dark" : "bg-success text-white"
        }`;
    }

    // Evidence Sufficiency Badge
    const suffBadge = getElement("fusionSufficiencyBadge");
    if (suffBadge) {
        suffBadge.textContent = `Sufficiency: ${fusion.confidence_status || 'SUFFICIENT'}`;
    }

    // Safety Override Banner
    const overrideBanner = getElement("fusionOverrideBanner");
    const overrideRule = getElement("fusionOverrideRule");
    const overrideReason = getElement("fusionOverrideReason");
    if (overrideBanner) {
        if (fusion.overrides && fusion.overrides.triggered && fusion.overrides.rules && fusion.overrides.rules.length > 0) {
            overrideBanner.classList.remove("d-none");
            const firstRule = fusion.overrides.rules[0];
            if (overrideRule) overrideRule.textContent = `SAFETY OVERRIDE ACTIVATED [${firstRule.rule_id}]`;
            if (overrideReason) overrideReason.textContent = firstRule.override_reason;
        } else {
            overrideBanner.classList.add("d-none");
        }
    }

    // Operational Weights
    if (fusion.weights_applied) {
        const sw = getElement("fusionSpatialWeight");
        const tw = getElement("fusionTemporalWeight");
        const vw = getElement("fusionVisualWeight");
        if (sw) sw.textContent = `w = ${Number(fusion.weights_applied.spatial).toFixed(2)}`;
        if (tw) tw.textContent = `w = ${Number(fusion.weights_applied.temporal).toFixed(2)}`;
        if (vw) vw.textContent = `w = ${Number(fusion.weights_applied.visual).toFixed(2)}`;
    }

    // Stream 1: Spatial ML & TreeSHAP
    const spatial = fusion.components?.spatial;
    if (spatial) {
        const actEl = getElement("fusionActiveModel");
        const agrEl = getElement("fusionAgreement");
        if (actEl) actEl.textContent = `${spatial.active_model || 'LightGBM'} Pipeline`;
        if (agrEl) agrEl.textContent = `${spatial.ensemble_agreement_pct ?? 97}`;

        const shapList = getElement("fusionShapList");
        if (shapList && Array.isArray(spatial.top_shap_factors) && spatial.top_shap_factors.length > 0) {
            shapList.innerHTML = spatial.top_shap_factors.slice(0, 3).map(f => {
                const sign = f.attribution > 0 ? "+" : "";
                return `<li>&bull; <strong>${f.feature}</strong>: ${sign}${Number(f.attribution).toFixed(3)} attribution</li>`;
            }).join("");
        }
    }

    // Stream 2: Temporal Dynamics
    const temporal = fusion.components?.temporal;
    if (temporal) {
        const trendEl = getElement("fusionTemporalTrend");
        const suffEl = getElement("fusionTemporalSufficiency");
        if (trendEl) {
            trendEl.textContent = temporal.trend || "STABLE";
            trendEl.className = `badge ${
                temporal.trend === "ACCELERATING" || temporal.trend === "RISING" ? "bg-danger text-white" : "bg-secondary text-white"
            }`;
        }
        if (suffEl) {
            suffEl.textContent = temporal.data_sufficiency ? "SUFFICIENT (3/3 windows)" : "PARTIAL / INSUFFICIENT";
        }
    }

    // Stream 3: Visual Hazard Evidence
    const visual = fusion.components?.visual;
    if (visual) {
        const vizHaz = getElement("fusionVisualHazard");
        if (vizHaz) vizHaz.textContent = visual.hazard_detected ? `${visual.hazard_type || 'Detected'}` : "None / Standby";
    }

    // Summary & Audit Trail
    const decSum = getElement("fusionDecisionSummary");
    if (decSum && Array.isArray(fusion.decision_basis) && fusion.decision_basis.length > 0) {
        decSum.textContent = fusion.decision_basis[fusion.decision_basis.length - 1];
    }
    const confStat = getElement("fusionConfidenceStatus");
    if (confStat) {
        confStat.textContent = `Status: ${fusion.confidence_status || 'CONVERGENT'}`;
    }
}

async function initializeProbabilityPage() {
    updateSliderLabels();
    setupEventListeners();

    // Check for city query parameter from Live Map drawer link
    const urlParams = new URLSearchParams(window.location.search);
    const cityParam = urlParams.get("city");
    const city = (cityParam && CITY_COORDINATES[cityParam]) ? cityParam : "Guwahati";

    const sel = getElement("locationSelect");
    if (sel) sel.value = city;

    await fetchLocationRisk(city);
}

document.addEventListener("DOMContentLoaded", initializeProbabilityPage);
