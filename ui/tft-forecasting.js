/**
 * TerraWatch NER - Temporal Fusion Transformer (TFT) Client Controller
 * Manages station selection, horizon toggles (1h, 6h, 24h), and Chart.js multi-horizon rendering.
 */

class TFTForecastingController {
    constructor() {
        this.currentStation = "SN-AS-001";
        this.currentHorizon = "24h";
        this.currentMetric = "moisture"; // 'moisture' or 'pore_pressure'
        this.chartInstance = null;
        this.cachedData = null;
    }

    init() {
        this.bindEvents();
        this.fetchForecast();
    }

    bindEvents() {
        const stationSelect = document.getElementById("tftStationSelect");
        if (stationSelect) {
            stationSelect.addEventListener("change", (e) => {
                this.currentStation = e.target.value;
                this.fetchForecast();
            });
        }

        const horizonBtns = document.querySelectorAll(".tft-horizon-btn");
        horizonBtns.forEach(btn => {
            btn.addEventListener("click", (e) => {
                horizonBtns.forEach(b => b.classList.remove("active", "btn-primary"));
                horizonBtns.forEach(b => b.classList.add("btn-outline-secondary"));
                btn.classList.add("active", "btn-primary");
                btn.classList.remove("btn-outline-secondary");
                this.currentHorizon = btn.getAttribute("data-horizon");
                this.fetchForecast();
            });
        });

        const metricRadios = document.querySelectorAll("input[name='tftMetricToggle']");
        metricRadios.forEach(radio => {
            radio.addEventListener("change", (e) => {
                this.currentMetric = e.target.value;
                if (this.cachedData) {
                    this.renderChart(this.cachedData);
                }
            });
        });

        const refreshBtn = document.getElementById("btnRefreshTFT");
        if (refreshBtn) {
            refreshBtn.addEventListener("click", () => this.fetchForecast());
        }
    }

    async fetchForecast() {
        const loadingIndicator = document.getElementById("tftLoadingSpinner");
        if (loadingIndicator) loadingIndicator.classList.remove("d-none");

        try {
            const url = `/api/forecast/tft?station_id=${encodeURIComponent(this.currentStation)}&horizon=${this.currentHorizon}`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            this.cachedData = data;
            this.updateKPIs(data);
            this.renderChart(data);
        } catch (err) {
            console.warn("Notice fetching TFT forecast:", err);
            this.renderFallbackState(err);
        } finally {
            if (loadingIndicator) loadingIndicator.classList.add("d-none");
        }
    }

    updateKPIs(data) {
        const smElem = document.getElementById("kpiTftMoisture");
        const ppElem = document.getElementById("kpiTftPorePressure");
        const horizonElem = document.getElementById("kpiTftHorizonLabel");
        const latencyElem = document.getElementById("kpiTftLatency");
        const badgeElem = document.getElementById("tftStatusBadge");

        const lastTrajectory = data.forecast_trajectory[data.forecast_trajectory.length - 1];
        if (lastTrajectory) {
            if (smElem) {
                smElem.innerHTML = `${lastTrajectory.soil_moisture.p50}% <small class="text-muted fw-normal" style="font-size:0.75rem;">[${lastTrajectory.soil_moisture.p10}% - ${lastTrajectory.soil_moisture.p90}%]</small>`;
            }
            if (ppElem) {
                ppElem.innerHTML = `${lastTrajectory.pore_pressure.p50} <small class="text-muted fw-normal" style="font-size:0.75rem;">kPa [${lastTrajectory.pore_pressure.p10} - ${lastTrajectory.pore_pressure.p90}]</small>`;
            }
        }
        if (horizonElem) horizonElem.innerText = `${data.horizon_hours} Hours Forward Horizon`;
        if (latencyElem) latencyElem.innerText = `${data.inference_latency_ms} ms (CPU)`;
        if (badgeElem) {
            badgeElem.className = data.model_type.includes("Transformer") 
                ? "badge bg-success-subtle text-success border border-success" 
                : "badge bg-warning-subtle text-warning border border-warning";
            badgeElem.innerText = data.model_type.includes("Transformer") ? "PyTorch TFT Active" : "Analytical Fallback";
        }
    }

    renderChart(data) {
        const ctx = document.getElementById("tftForecastChart");
        if (!ctx) return;

        const isMoisture = this.currentMetric === "moisture";
        const unit = isMoisture ? "%" : "kPa";
        const labelName = isMoisture ? "Soil Moisture Saturation" : "Pore Water Pressure";

        // Historical observations
        const histLabels = data.historical_observed.map(h => {
            const d = new Date(h.timestamp);
            return `${d.getHours()}:00`;
        });
        const histValues = data.historical_observed.map(h => 
            isMoisture ? h.soil_moisture : h.pore_pressure
        );

        // Future forecast trajectory
        const futureLabels = data.forecast_trajectory.map(f => {
            const d = new Date(f.timestamp);
            return `+${f.step_hours}h (${d.getHours()}:00)`;
        });
        const futureP50 = data.forecast_trajectory.map(f => 
            isMoisture ? f.soil_moisture.p50 : f.pore_pressure.p50
        );
        const futureP10 = data.forecast_trajectory.map(f => 
            isMoisture ? f.soil_moisture.p10 : f.pore_pressure.p10
        );
        const futureP90 = data.forecast_trajectory.map(f => 
            isMoisture ? f.soil_moisture.p90 : f.pore_pressure.p90
        );

        const allLabels = [...histLabels, ...futureLabels];
        
        // Observed dataset (null for future steps)
        const observedDataset = [...histValues, ...new Array(futureLabels.length).fill(null)];
        
        // Forecast dataset (connects from last historical point)
        const lastHistVal = histValues[histValues.length - 1];
        const forecastDataset = [
            ...new Array(histValues.length - 1).fill(null),
            lastHistVal,
            ...futureP50
        ];

        // Ribbon upper (p90) and lower (p10)
        const ribbonUpper = [
            ...new Array(histValues.length - 1).fill(null),
            lastHistVal,
            ...futureP90
        ];
        const ribbonLower = [
            ...new Array(histValues.length - 1).fill(null),
            lastHistVal,
            ...futureP10
        ];

        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        const colorPrimary = isMoisture ? "#0d6efd" : "#fd7e14";
        const colorForecast = isMoisture ? "#6f42c1" : "#d63384";

        this.chartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: allLabels,
                datasets: [
                    {
                        label: `Historical Observed (${unit})`,
                        data: observedDataset,
                        borderColor: colorPrimary,
                        backgroundColor: colorPrimary,
                        borderWidth: 2.5,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        tension: 0.25
                    },
                    {
                        label: `TFT Median Forecast p50 (${unit})`,
                        data: forecastDataset,
                        borderColor: colorForecast,
                        backgroundColor: colorForecast,
                        borderWidth: 2.5,
                        borderDash: [6, 4],
                        pointRadius: 4,
                        pointHoverRadius: 7,
                        tension: 0.3
                    },
                    {
                        label: "Confidence Bound (p90)",
                        data: ribbonUpper,
                        borderColor: "transparent",
                        backgroundColor: "rgba(111, 66, 193, 0.15)",
                        pointRadius: 0,
                        fill: "+1",
                        tension: 0.3
                    },
                    {
                        label: "Confidence Bound (p10)",
                        data: ribbonLower,
                        borderColor: "transparent",
                        backgroundColor: "transparent",
                        pointRadius: 0,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: "index"
                },
                plugins: {
                    legend: {
                        position: "top",
                        labels: {
                            filter: item => !item.text.includes("Confidence Bound"),
                            font: { family: "Inter", size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.raw === null || context.dataset.label.includes("Confidence Bound")) return null;
                                return `${context.dataset.label}: ${context.raw} ${unit}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: "rgba(0, 0, 0, 0.05)" },
                        ticks: { font: { family: "Inter", size: 11 }, maxRotation: 45 }
                    },
                    y: {
                        title: { display: true, text: `${labelName} (${unit})`, font: { family: "Inter", size: 12 } },
                        grid: { color: "rgba(0, 0, 0, 0.05)" },
                        ticks: { font: { family: "Inter", size: 11 } }
                    }
                }
            }
        });
    }

    renderFallbackState(err) {
        const chartBox = document.getElementById("tftForecastChart");
        if (chartBox) {
            console.error("TFT render error:", err);
        }
    }
}

// Global initialization
document.addEventListener("DOMContentLoaded", () => {
    window.tftController = new TFTForecastingController();
    window.tftController.init();
});
