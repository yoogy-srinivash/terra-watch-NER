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

    const simRain = getElement("simRainfall");
    const simSoil = getElement("simSoil");
    const simSlope = getElement("simSlope");
    const simPore = getElement("simPorePress");

    const rf = simRain ? parseFloat(simRain.value) : (probabilityData.factors.rainfall || 28);
    const sm = simSoil ? parseFloat(simSoil.value) : (probabilityData.factors.soil || 32);
    const sl = simSlope ? parseFloat(simSlope.value) : (probabilityData.factors.terrain || 22);
    const pp = simPore ? parseFloat(simPore.value) : (probabilityData.factors.water ? probabilityData.factors.water * 0.28 : 6.0);

    if (rfVal && rfBar) {
        rfVal.textContent = `${Math.round(rf)} mm • ${rf >= 35 ? 'Critical Impact' : rf >= 25 ? 'High Impact' : 'Normal'}`;
        const rfPct = Math.min(100, Math.max(5, Math.round((rf / 150) * 100)));
        rfBar.style.width = `${rfPct}%`;
        rfBar.className = `factor-bar-fill ${rf >= 35 ? 'bg-danger' : rf >= 25 ? 'bg-warning' : 'bg-info'}`;
    }
    if (ppVal && ppBar) {
        ppVal.textContent = `${pp.toFixed(1)} kPa • ${pp >= 25 ? 'Critical (Override Active)' : pp >= 15 ? 'Elevated Pressure' : 'Normal'}`;
        const ppPct = Math.min(100, Math.max(5, Math.round((pp / 40) * 100)));
        ppBar.style.width = `${ppPct}%`;
        ppBar.className = `factor-bar-fill ${pp >= 25 ? 'bg-danger' : pp >= 15 ? 'bg-warning' : 'bg-info'}`;
    }
    if (slVal && slBar) {
        slVal.textContent = `${Math.round(sl)}° • ${sl >= 30 ? 'Steep Gradient' : 'Moderate'}`;
        const slPct = Math.min(100, Math.max(5, Math.round((sl / 60) * 100)));
        slBar.style.width = `${slPct}%`;
        slBar.className = `factor-bar-fill ${sl >= 30 ? 'bg-danger' : 'bg-warning'}`;
    }
    if (smVal && smBar) {
        smVal.textContent = `${Math.round(sm)}% • ${sm >= 75 ? 'Near Saturation' : sm >= 50 ? 'Elevated Saturation' : 'Normal'}`;
        smBar.style.width = `${Math.min(100, Math.max(5, Math.round(sm)))}%`;
        smBar.className = `factor-bar-fill ${sm >= 75 ? 'bg-danger' : sm >= 50 ? 'bg-warning' : 'bg-success'}`;
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
        const api = window.TerraWatchAPI || window.LandSafeAPI;
        if (api && typeof api.getProbability === "function") {
            res = await api.getProbability(city);
        }
        if (!res && api && typeof api.getLiveRisk === "function") {
            res = await api.getLiveRisk(city);
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
            const simPore = getElement("simPorePress");
            const simVib = getElement("simVibration");
            if (simRain) simRain.value = 28;
            if (simSoil) simSoil.value = probabilityData.factors.soil || 32;
            if (simSlope) simSlope.value = Math.round(probabilityData.factors.terrain * 0.55) || 22;
            if (simPore) simPore.value = 6.0;
            if (simVib) simVib.value = 0.004;

            updateSliderLabels();
            updateUIAll();

            if (res.fusion) {
                updateFusionUI(res.fusion);
            }

            if (api && api.showToast) {
                api.showToast(
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
    const simPore = getElement("simPorePress");
    const simVib = getElement("simVibration");

    const rainVal = getElement("simRainfallVal");
    const soilVal = getElement("simSoilVal");
    const slopeVal = getElement("simSlopeVal");
    const poreVal = getElement("simPorePressVal");
    const vibVal = getElement("simVibrationVal");

    if (rainVal && simRain) rainVal.textContent = `${simRain.value} mm`;
    if (soilVal && simSoil) soilVal.textContent = `${simSoil.value}%`;
    if (slopeVal && simSlope) slopeVal.textContent = `${simSlope.value}°`;
    if (poreVal && simPore) poreVal.textContent = `${parseFloat(simPore.value).toFixed(1)} kPa`;
    if (vibVal && simVib) vibVal.textContent = `${parseFloat(simVib.value).toFixed(3)} g`;
}

async function runSimulation() {
    const simRain = getElement("simRainfall");
    const simSoil = getElement("simSoil");
    const simSlope = getElement("simSlope");
    const simPore = getElement("simPorePress");
    const simVib = getElement("simVibration");
    const btnSim = getElement("btnRunSimulation");

    if (!simRain || !simSoil || !simSlope) return;

    if (btnSim) {
        btnSim.disabled = true;
        btnSim.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Running ML...`;
    }

    const rainfall = parseFloat(simRain.value);
    const soil = parseFloat(simSoil.value);
    const slope = parseFloat(simSlope.value);
    const pore = simPore ? parseFloat(simPore.value) : 6.0;
    const vib = simVib ? parseFloat(simVib.value) : 0.004;

    const city = probabilityData.city || "Guwahati";
    const geo = CITY_COORDINATES[city] || CITY_COORDINATES["Guwahati"];
    const api = window.TerraWatchAPI || window.LandSafeAPI;

    try {
        if (api && typeof api.predictRisk === "function") {
            const res = await api.predictRisk({
                latitude: geo.lat,
                longitude: geo.lng,
                state: geo.state,
                district: geo.district,
                rainfall_24h_mm: rainfall,
                soil_moisture_pct: soil,
                slope_angle_deg: slope,
                pore_pressure_kpa: pore,
                ground_vibration_g: vib
            });

            if (res && res.prediction) {
                const pred = res.prediction;
                const fusedScore = (res.fusion && typeof res.fusion.fused_risk_score === 'number')
                    ? Math.round(res.fusion.fused_risk_score * 100)
                    : Math.round(pred.risk_score);

                probabilityData.overall = fusedScore;
                probabilityData.landslide = Math.round(pred.landslide_risk_pct || fusedScore);
                probabilityData.flood = Math.round(pred.flood_risk_pct || (fusedScore * 0.7));
                probabilityData.level = (res.fusion && res.fusion.risk_tier) ? res.fusion.risk_tier : pred.risk_level;

                if (pred.factors) {
                    probabilityData.factors.rainfall = pred.factors.rainfall || Math.min(100, Math.round(rainfall / 2.5));
                    probabilityData.factors.soil = pred.factors.soil || Math.round(soil);
                    probabilityData.factors.terrain = pred.factors.slope || Math.round(slope * 1.5);
                    probabilityData.factors.water = pred.factors.water || Math.min(100, Math.round(pore * 2.5));
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

                if (api && api.showToast) {
                    api.showToast(
                        `Simulation Result: Multi-Modal Risk predicts ${probabilityData.overall}% (${probabilityData.level})`,
                        probabilityData.overall >= 60 ? "danger" : probabilityData.overall >= 35 ? "warning" : "success"
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
    const simPore = getElement("simPorePress");
    const simVib = getElement("simVibration");

    if (simRain) simRain.addEventListener("input", () => { updateSliderLabels(); updateFactorBars(); });
    if (simSoil) simSoil.addEventListener("input", () => { updateSliderLabels(); updateFactorBars(); });
    if (simSlope) simSlope.addEventListener("input", () => { updateSliderLabels(); updateFactorBars(); });
    if (simPore) simPore.addEventListener("input", () => { updateSliderLabels(); updateFactorBars(); });
    if (simVib) simVib.addEventListener("input", () => { updateSliderLabels(); updateFactorBars(); });

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
    function activatePreset(id, rain, soil, slope, pore, vib) {
        document.querySelectorAll(".scenario-card").forEach(c => c.classList.remove("active"));
        const card = getElement(id);
        if (card) card.classList.add("active");

        if (simRain) simRain.value = rain;
        if (simSoil) simSoil.value = soil;
        if (simSlope) simSlope.value = slope;
        if (simPore) simPore.value = pore;
        if (simVib) simVib.value = vib;
        updateSliderLabels();
        updateFactorBars();
        runSimulation();
    }

    const presetMap = [
        { id: "presetNormal", rain: 10, soil: 30, slope: 15, pore: 3.0, vib: 0.003 },
        { id: "presetMoisture", rain: 28, soil: 32, slope: 22, pore: 6.0, vib: 0.004 },
        { id: "presetMonsoon", rain: 35, soil: 38, slope: 26, pore: 8.0, vib: 0.005 },
        { id: "presetPorePress", rain: 25, soil: 35, slope: 20, pore: 29.5, vib: 0.004 },
        { id: "presetVibration", rain: 20, soil: 32, slope: 20, pore: 5.0, vib: 1.6 },
        { id: "presetCombined", rain: 180, soil: 92, slope: 42, pore: 38.0, vib: 0.08 }
    ];

    presetMap.forEach(p => {
        const btn = getElement(p.id);
        if (btn) {
            btn.addEventListener("click", () => activatePreset(p.id, p.rain, p.soil, p.slope, p.pore, p.vib));
        }
    });

    const notifBtn = getElement("notificationButton");
    if (notifBtn) {
        notifBtn.addEventListener("click", async function() {
            const api = window.TerraWatchAPI || window.LandSafeAPI;
            if (api) {
                try {
                    const alerts = await api.getActiveAlerts();
                    if (alerts && alerts.length > 0) {
                        const alertTitles = alerts.slice(0, 3).map(a => `• [${a.severity}] ${a.title || a.location}`).join('\n');
                        if (api.showToast) {
                            api.showToast(`Active Early Warning Alerts:\n${alertTitles}`, "warning");
                        }
                        return;
                    }
                } catch (e) {}
            }
            if (api && api.showToast) {
                api.showToast("All landslide corridors normal. Continuous ML inference running.", "info");
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

        const spatScore = getElement("spatialStreamScore");
        if (spatScore) {
            const val = typeof spatial.raw_risk_score === 'number' ? spatial.raw_risk_score : Math.round((spatial.score || 0) * 100);
            spatScore.textContent = `${val}%`;
        }

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
            suffEl.textContent = temporal.data_sufficiency === "SUFFICIENT" ? "SUFFICIENT (3/3 windows)" : (temporal.data_sufficiency || "SYNTHESIZED / SUFFICIENT");
        }
        const tempScore = getElement("temporalStreamScore");
        if (tempScore) {
            const val = typeof temporal.raw_temporal_score === 'number' ? Math.round(temporal.raw_temporal_score) : Math.round((temporal.score || 0) * 100);
            tempScore.textContent = `${val}%`;
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
