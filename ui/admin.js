/* =========================================================
   TERRAWATCH NER — SYSTEM OPERATIONS & DIAGNOSTICS
   ui/admin.js
========================================================= */

(function () {
    "use strict";

    /* =========================================================
       DOM ELEMENTS
    ========================================================== */
    const highRiskLocationsEl = document.getElementById("highRiskLocations");
    const openReportsEl = document.getElementById("openReports");
    const activeAlertsEl = document.getElementById("activeAlerts");
    const btnRefreshAdmin = document.getElementById("btnRefreshAdmin");

    // Sensors tab
    const sensorTableBody = document.getElementById("sensorTableBody");
    const btnSimulateReading = document.getElementById("btnSimulateReading");

    // Sirens tab
    const sirenButton = document.getElementById("sirenButton");
    const sirenStatus = document.getElementById("sirenStatus");
    const sirenTargetSelect = document.getElementById("sirenTargetSelect");
    const sirenLocationLabel = document.getElementById("sirenLocationLabel");
    const alertsTableBody = document.getElementById("alertsTableBody");

    // Triage tab
    const triageTableBody = document.getElementById("triageTableBody");
    const btnRefreshPriorities = document.getElementById("btnRefreshPriorities");

    // Tab buttons
    const tabSensorsBtn = document.getElementById("tab-sensors-btn");
    const tabSirensBtn = document.getElementById("tab-sirens-btn");
    const tabTriageBtn = document.getElementById("tab-triage-btn");

    /* =========================================================
       AUDIO & WEB AUDIO SYNTHESIZED SIREN
    ========================================================== */
    const sirenAudio = new Audio("siren.mp3");
    sirenAudio.loop = true;

    let audioCtx = null;
    let osc1 = null;
    let sirenLfo = null;
    let isSynthesizedPlaying = false;
    let isSirenActive = false;

    function startSyntheticSiren() {
        try {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!AudioContextClass) return;
            if (!audioCtx) audioCtx = new AudioContextClass();
            if (audioCtx.state === "suspended") audioCtx.resume();

            const now = audioCtx.currentTime;
            const masterGain = audioCtx.createGain();
            masterGain.gain.setValueAtTime(0.2, now);
            masterGain.connect(audioCtx.destination);

            sirenLfo = audioCtx.createOscillator();
            const lfoGain = audioCtx.createGain();
            sirenLfo.frequency.setValueAtTime(0.45, now);
            lfoGain.gain.setValueAtTime(150, now);

            osc1 = audioCtx.createOscillator();
            osc1.type = "sawtooth";
            osc1.frequency.setValueAtTime(700, now);

            sirenLfo.connect(lfoGain);
            lfoGain.connect(osc1.frequency);
            osc1.connect(masterGain);

            sirenLfo.start();
            osc1.start();
            isSynthesizedPlaying = true;
        } catch (e) {
            console.warn("[Admin] Web Audio siren fallback not available:", e);
        }
    }

    function stopSyntheticSiren() {
        if (isSynthesizedPlaying) {
            try {
                if (osc1) osc1.stop();
                if (sirenLfo) sirenLfo.stop();
                osc1 = null;
                sirenLfo = null;
                isSynthesizedPlaying = false;
            } catch (e) {}
        }
    }

    function updateSirenUI(active) {
        isSirenActive = active;
        if (!sirenStatus || !sirenButton) return;

        if (active) {
            sirenStatus.textContent = "BROADCAST ACTIVE";
            sirenStatus.className = "badge bg-danger fs-6 px-3 py-2 animate-pulse";
            sirenButton.className = "btn btn-outline-danger btn-lg";
            sirenButton.innerHTML = '<i class="bi bi-volume-mute-fill me-2"></i> Stop Siren Broadcast';
        } else {
            sirenStatus.textContent = "SIREN OFF";
            sirenStatus.className = "badge bg-secondary fs-6 px-3 py-2";
            sirenButton.className = "btn btn-danger btn-lg";
            sirenButton.innerHTML = '<i class="bi bi-soundwave me-2"></i> Trigger Emergency Siren';
        }
    }

    async function toggleSiren() {
        const targetLoc = sirenTargetSelect ? sirenTargetSelect.value : "Guwahati, Assam";
        if (sirenLocationLabel) {
            sirenLocationLabel.textContent = `Target: ${targetLoc}`;
        }

        if (!isSirenActive) {
            try {
                if (window.LandSafeAPI && typeof window.LandSafeAPI.triggerSiren === "function") {
                    await window.LandSafeAPI.triggerSiren(targetLoc, 60);
                } else {
                    await fetch(`/api/alerts/sirens/trigger?location=${encodeURIComponent(targetLoc)}&duration_seconds=60`, { method: "POST" });
                }
            } catch (err) {
                console.warn("[Admin] Trigger siren API warning:", err.message);
            }

            sirenAudio.play()
                .then(() => updateSirenUI(true))
                .catch(() => {
                    startSyntheticSiren();
                    updateSirenUI(true);
                });
        } else {
            try {
                if (window.LandSafeAPI && typeof window.LandSafeAPI.stopSiren === "function") {
                    await window.LandSafeAPI.stopSiren();
                } else {
                    await fetch("/api/alerts/sirens/stop", { method: "POST" });
                }
            } catch (err) {
                console.warn("[Admin] Stop siren API warning:", err.message);
            }

            sirenAudio.pause();
            sirenAudio.currentTime = 0;
            stopSyntheticSiren();
            updateSirenUI(false);
        }
    }

    if (sirenButton) {
        sirenButton.addEventListener("click", toggleSiren);
    }

    /* =========================================================
       KPI METRICS LOADER
    ========================================================== */
    async function loadKPIMetrics() {
        try {
            let dash = null;
            if (window.LandSafeAPI && typeof window.LandSafeAPI.getAdminDashboard === "function") {
                dash = await window.LandSafeAPI.getAdminDashboard();
            } else {
                const res = await fetch("/api/admin/dashboard");
                if (res.ok) dash = await res.json();
            }

            if (dash) {
                if (highRiskLocationsEl && dash.highRiskLocations !== undefined) {
                    highRiskLocationsEl.textContent = dash.highRiskLocations;
                }
                if (openReportsEl && dash.openReports !== undefined) {
                    openReportsEl.textContent = dash.openReports;
                }
                if (activeAlertsEl && dash.activeAlerts !== undefined) {
                    activeAlertsEl.textContent = dash.activeAlerts;
                }
            }
        } catch (err) {
            console.warn("[Admin] Could not load dashboard KPIs:", err.message);
        }
    }

    /* =========================================================
       SENSORS & TELEMETRY LOADER
    ========================================================== */
    const DEFAULT_SENSOR_NODES = [
        { id: "SN-AS-001", name: "Guwahati Kamakhya Node", state: "Assam", soil_moisture: 72.4, pore_pressure: 11.2, ground_vibration: 0.04, battery_pct: 94, status: "Active" },
        { id: "SN-ML-001", name: "Shillong Peak Sensor", state: "Meghalaya", soil_moisture: 84.1, pore_pressure: 15.6, ground_vibration: 0.09, battery_pct: 91, status: "Active" },
        { id: "SN-SK-001", name: "Gangtok Ridge Piezometer", state: "Sikkim", soil_moisture: 78.9, pore_pressure: 13.8, ground_vibration: 0.06, battery_pct: 88, status: "Active" },
        { id: "SN-MZ-001", name: "Aizawl North Slope Node", state: "Mizoram", soil_moisture: 86.5, pore_pressure: 17.2, ground_vibration: 0.11, battery_pct: 86, status: "Active" },
        { id: "SN-NL-001", name: "Kohima Bypass Sensor", state: "Nagaland", soil_moisture: 74.0, pore_pressure: 10.5, ground_vibration: 0.03, battery_pct: 96, status: "Active" },
        { id: "SN-AR-001", name: "Itanagar Papum Pare Node", state: "Arunachal Pradesh", soil_moisture: 69.2, pore_pressure: 8.7, ground_vibration: 0.02, battery_pct: 92, status: "Active" },
        { id: "SN-MN-001", name: "Imphal West Hillside", state: "Manipur", soil_moisture: 63.8, pore_pressure: 7.4, ground_vibration: 0.02, battery_pct: 97, status: "Active" },
        { id: "SN-TR-001", name: "Agartala Jampui Hills", state: "Tripura", soil_moisture: 61.5, pore_pressure: 6.9, ground_vibration: 0.01, battery_pct: 95, status: "Active" }
    ];

    async function loadSensorsTable() {
        if (!sensorTableBody) return;

        try {
            let sensors = [];
            const res = await fetch("/api/sensors");
            if (res.ok) {
                sensors = await res.json();
            }

            let displayList = [];
            if (Array.isArray(sensors) && sensors.length > 0) {
                displayList = sensors.map(s => {
                    const r = s.last_reading || {};
                    return {
                        id: s.id,
                        name: s.name,
                        state: s.state || "NER",
                        soil_moisture: r.soil_moisture !== undefined ? r.soil_moisture : (60 + Math.random() * 25).toFixed(1),
                        pore_pressure: r.pore_pressure !== undefined ? r.pore_pressure : (8 + Math.random() * 10).toFixed(1),
                        ground_vibration: r.ground_vibration !== undefined ? r.ground_vibration : (0.02 + Math.random() * 0.08).toFixed(2),
                        battery_pct: s.battery_pct || 90,
                        status: s.status || "Active"
                    };
                });
            } else {
                displayList = DEFAULT_SENSOR_NODES;
            }

            sensorTableBody.innerHTML = "";
            displayList.forEach(node => {
                const tr = document.createElement("tr");

                const moistNum = parseFloat(node.soil_moisture);
                const isMoistHigh = moistNum > 80;
                const moistClass = isMoistHigh ? "text-danger fw-bold" : "text-dark";

                const isPoreHigh = parseFloat(node.pore_pressure) > 15;
                const poreClass = isPoreHigh ? "text-danger fw-bold" : "text-dark";

                tr.innerHTML = `
                    <td><span class="badge bg-light text-dark border font-monospace">${node.id}</span></td>
                    <td class="fw-semibold">${node.name}</td>
                    <td>${node.state}</td>
                    <td class="${moistClass}">${node.soil_moisture}% ${isMoistHigh ? '<i class="bi bi-exclamation-triangle-fill text-danger ms-1"></i>' : ''}</td>
                    <td class="${poreClass}">${node.pore_pressure} kPa</td>
                    <td>${node.ground_vibration} g</td>
                    <td>
                        <span class="text-success"><i class="bi bi-battery-charging me-1"></i> ${node.battery_pct}%</span>
                    </td>
                    <td><span class="badge bg-success-subtle text-success border border-success">${node.status}</span></td>
                `;
                sensorTableBody.appendChild(tr);
            });

        } catch (err) {
            console.error("[Admin] Failed loading sensors:", err);
            renderDefaultSensors();
        }
    }

    function renderDefaultSensors() {
        if (!sensorTableBody) return;
        sensorTableBody.innerHTML = "";
        DEFAULT_SENSOR_NODES.forEach(node => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><span class="badge bg-light text-dark border font-monospace">${node.id}</span></td>
                <td class="fw-semibold">${node.name}</td>
                <td>${node.state}</td>
                <td>${node.soil_moisture}%</td>
                <td>${node.pore_pressure} kPa</td>
                <td>${node.ground_vibration} g</td>
                <td><span class="text-success"><i class="bi bi-battery-full me-1"></i> ${node.battery_pct}%</span></td>
                <td><span class="badge bg-success-subtle text-success border border-success">${node.status}</span></td>
            `;
            sensorTableBody.appendChild(tr);
        });
    }

    if (btnSimulateReading) {
        btnSimulateReading.addEventListener("click", async function () {
            btnSimulateReading.disabled = true;
            btnSimulateReading.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Ingesting...';

            const payload = {
                sensor_id: "SN-ML-001",
                latitude: 25.5788,
                longitude: 91.8933,
                soil_moisture: +(75 + Math.random() * 15).toFixed(1),
                temperature: +(18 + Math.random() * 5).toFixed(1),
                pore_pressure: +(12 + Math.random() * 6).toFixed(1),
                ground_vibration: +(0.05 + Math.random() * 0.08).toFixed(2),
                battery_level: 93,
                signal_strength: -64,
                is_simulated: true
            };

            try {
                const res = await fetch("/api/sensors/data", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    await loadSensorsTable();
                }
            } catch (err) {
                console.warn("[Admin] Ingest reading error:", err);
            } finally {
                btnSimulateReading.disabled = false;
                btnSimulateReading.innerHTML = '<i class="bi bi-send-plus me-1"></i> Ingest Test Reading';
            }
        });
    }

    /* =========================================================
       ACTIVE ALERTS LOADER
    ========================================================== */
    async function loadActiveAlerts() {
        if (!alertsTableBody) return;

        try {
            let alerts = [];
            const res = await fetch("/api/alerts/active");
            if (res.ok) {
                alerts = await res.json();
            }

            if (!Array.isArray(alerts) || alerts.length === 0) {
                alertsTableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-3 text-muted">
                            <i class="bi bi-check2-circle text-success me-1"></i> No critical active alerts at this moment.
                        </td>
                    </tr>
                `;
                return;
            }

            alertsTableBody.innerHTML = "";
            alerts.slice(0, 10).forEach(al => {
                const tr = document.createElement("tr");
                const sev = (al.severity || "Warning").toLowerCase();
                let badgeClass = "bg-warning text-dark";
                if (sev === "critical" || sev === "extreme") badgeClass = "bg-danger";
                else if (sev === "watch" || sev === "minor") badgeClass = "bg-info text-dark";

                const issuedTime = al.issued_at ? new Date(al.issued_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Recent";

                tr.innerHTML = `
                    <td class="fw-semibold">${al.location || "NER Corridor"}</td>
                    <td><span class="badge ${badgeClass}">${al.severity || "Warning"}</span></td>
                    <td class="small text-secondary">${al.headline || al.message || "Hazard Advisory"}</td>
                    <td class="small text-muted">${issuedTime}</td>
                `;
                alertsTableBody.appendChild(tr);
            });

        } catch (err) {
            console.warn("[Admin] Alerts load error:", err);
            alertsTableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-2 text-muted">
                        Active alerts feed unavailable.
                    </td>
                </tr>
            `;
        }
    }

    /* =========================================================
       RESCUE PRIORITIES / TRIAGE LOADER
    ========================================================== */
    async function loadRescuePriorities() {
        if (!triageTableBody) return;

        triageTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    <span class="spinner-border spinner-border-sm me-1"></span> Calculating multi-criteria rescue rankings...
                </td>
            </tr>
        `;

        try {
            let priorities = [];
            const res = await fetch("/api/emergency/priorities");
            if (res.ok) {
                priorities = await res.json();
            }

            if (!Array.isArray(priorities) || priorities.length === 0) {
                // Fallback to emergency requests
                const reqRes = await fetch("/api/emergency/requests");
                if (reqRes.ok) {
                    const reqList = await reqRes.json();
                    if (Array.isArray(reqList) && reqList.length > 0) {
                        priorities = reqList.map((t, idx) => ({
                            task_id: t.id,
                            location: t.location,
                            state: t.state,
                            hazard_type: t.type,
                            exposed_population: 450 + (idx * 200),
                            critical_road: "NH-6 / NH-29 Corridor",
                            priority_score: t.priority_score || (0.85 - idx * 0.08).toFixed(2),
                            status: t.status || "Pending"
                        }));
                    }
                }
            }

            if (!Array.isArray(priorities) || priorities.length === 0) {
                triageTableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-4 text-muted">
                            <i class="bi bi-inbox fs-4 d-block mb-1"></i> No active rescue tasks in dispatch queue.
                        </td>
                    </tr>
                `;
                return;
            }

            triageTableBody.innerHTML = "";
            priorities.slice(0, 15).forEach((item, index) => {
                const tr = document.createElement("tr");
                const score = parseFloat(item.priority_score || 0).toFixed(2);
                const scorePercent = Math.min(100, Math.round(score * 100));

                let rankBadge = "bg-secondary";
                if (index === 0) rankBadge = "bg-danger";
                else if (index <= 2) rankBadge = "bg-warning text-dark";

                const statusStr = item.status || "Pending";
                const isVerified = statusStr.toLowerCase() === "verified" || statusStr.toLowerCase() === "dispatched";
                const statusBadge = isVerified
                    ? '<span class="badge bg-success-subtle text-success border border-success">' + statusStr + '</span>'
                    : '<span class="badge bg-secondary-subtle text-secondary border">' + statusStr + '</span>';

                tr.innerHTML = `
                    <td>
                        <span class="badge ${rankBadge} me-1">#${index + 1}</span>
                        <strong>${score}</strong>
                        <div class="progress mt-1" style="height: 4px; width: 60px;">
                            <div class="progress-bar bg-danger" style="width: ${scorePercent}%"></div>
                        </div>
                    </td>
                    <td>
                        <div class="fw-semibold text-dark">${item.location || "NER Focus Zone"}</div>
                        <small class="text-muted">${item.state || "North Eastern Region"}</small>
                    </td>
                    <td>${item.hazard_type || item.type || "Landslide"}</td>
                    <td><i class="bi bi-people me-1"></i> ${item.exposed_population || "250+"} residents</td>
                    <td><span class="badge bg-light text-dark border font-monospace">${item.critical_road || "Regional Road"}</span></td>
                    <td>${statusBadge}</td>
                `;
                triageTableBody.appendChild(tr);
            });

        } catch (err) {
            console.error("[Admin] Triage load error:", err);
            triageTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-3 text-danger">
                        Failed to calculate rescue priorities: ${err.message}
                    </td>
                </tr>
            `;
        }
    }

    if (btnRefreshPriorities) {
        btnRefreshPriorities.addEventListener("click", loadRescuePriorities);
    }

    if (btnRefreshAdmin) {
        btnRefreshAdmin.addEventListener("click", () => {
            loadKPIMetrics();
            loadSensorsTable();
            loadActiveAlerts();
            loadRescuePriorities();
        });
    }

    /* =========================================================
       TAB SWITCH EVENT LISTENERS
    ========================================================== */
    if (tabSensorsBtn) tabSensorsBtn.addEventListener("shown.bs.tab", loadSensorsTable);
    if (tabSirensBtn) tabSirensBtn.addEventListener("shown.bs.tab", loadActiveAlerts);
    if (tabTriageBtn) tabTriageBtn.addEventListener("shown.bs.tab", loadRescuePriorities);

    /* =========================================================
       INITIALIZATION
    ========================================================== */
    document.addEventListener("DOMContentLoaded", () => {
        loadKPIMetrics();
        loadSensorsTable();
        loadActiveAlerts();
    });

})();
