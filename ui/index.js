/* =========================================================
   TERRAWATCH NER — OVERVIEW CONTROLLER
   Dynamically binds live regional telemetry from FastAPI
   ========================================================= */

(function () {
    async function initOverviewPage() {
        const api = window.TerraWatchAPI || window.LandSafeAPI;
        if (!api || typeof api.getLiveRisk !== "function") {
            setFallbackState("Awaiting API connection");
            return;
        }

        try {
            const live = await api.getLiveRisk("Guwahati");
            if (!live) {
                setFallbackState("Telemetry standby");
                return;
            }

            const score = typeof live.overall === "number" ? Math.round(live.overall) : 68;
            const level = live.level || (score >= 80 ? "CRITICAL" : score >= 60 ? "HIGH" : score >= 30 ? "MODERATE" : "LOW");

            const scoreEl = document.getElementById("overviewRiskScore");
            const badgeEl = document.getElementById("overviewRiskBadge");
            const labelEl = document.getElementById("overviewRiskLabel");
            const rainEl = document.getElementById("overviewRainfall");
            const slopeEl = document.getElementById("overviewSlope");

            let badgeClass = "bg-success text-white";
            if (level === "CRITICAL") badgeClass = "bg-dark text-white";
            else if (level === "HIGH") badgeClass = "bg-danger text-white";
            else if (level === "MODERATE") badgeClass = "bg-warning text-dark";

            if (scoreEl) scoreEl.textContent = `${score}%`;
            if (badgeEl) {
                badgeEl.className = `badge ${badgeClass}`;
                badgeEl.textContent = `${level} RISK`;
            }
            if (labelEl) {
                labelEl.textContent = `Live Monitored Index (${score}/100)`;
            }

            const env = live.environmental_factors || {};
            if (rainEl) {
                const rain = env.rainfall_24h_mm !== undefined ? Math.round(env.rainfall_24h_mm) : 45;
                rainEl.textContent = `${rain} mm`;
            }
            if (slopeEl) {
                const slope = env.slope_angle_deg !== undefined ? Math.round(env.slope_angle_deg) : 32;
                slopeEl.textContent = `${slope}°`;
            }

            console.log(`[Overview] Regional status updated for Guwahati: ${score}% (${level})`);
        } catch (err) {
            console.warn("[Overview] Live risk fetch failed:", err.message);
            setFallbackState("Telemetry standby");
        }
    }

    function setFallbackState(message) {
        const scoreEl = document.getElementById("overviewRiskScore");
        const badgeEl = document.getElementById("overviewRiskBadge");
        const labelEl = document.getElementById("overviewRiskLabel");

        if (scoreEl) scoreEl.textContent = "--";
        if (badgeEl) {
            badgeEl.className = "badge bg-secondary";
            badgeEl.textContent = "STANDBY";
        }
        if (labelEl) labelEl.textContent = message;
    }

    document.addEventListener("DOMContentLoaded", initOverviewPage);
})();
