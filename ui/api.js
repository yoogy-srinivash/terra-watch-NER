/**
 * TerraWatch NER - Unified API Client
 * Seamlessly bridges the frontend to the FastAPI REST backend.
 * Provides resilient network fallback so UI never breaks when offline.
 */

const TerraWatchAPI = (function() {
    // Determine Base URL dynamically
    let API_BASE = "http://localhost:8000/api";
    if (window.location.origin && window.location.origin.startsWith("http")) {
        // If served from FastAPI (e.g. localhost:8000/ui/...)
        API_BASE = `${window.location.origin}/api`;
    }

    function getToken() {
        return localStorage.getItem("terrawatch_token") || localStorage.getItem("landsafe_token");
    }

    function setToken(token, user) {
        if (token) {
            localStorage.setItem("terrawatch_token", token);
            localStorage.setItem("landsafe_token", token);
        } else {
            localStorage.removeItem("terrawatch_token");
            localStorage.removeItem("landsafe_token");
        }
        if (user) {
            localStorage.setItem("terrawatch_user", JSON.stringify(user));
            localStorage.setItem("landsafe_user", JSON.stringify(user));
        } else {
            localStorage.removeItem("terrawatch_user");
            localStorage.removeItem("landsafe_user");
        }
    }

    function getUser() {
        const u = localStorage.getItem("terrawatch_user") || localStorage.getItem("landsafe_user");
        return u ? JSON.parse(u) : null;
    }

    function authHeaders() {
        const headers = { "Content-Type": "application/json" };
        const token = getToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        return headers;
    }

    async function request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...authHeaders(),
                ...(options.headers || {})
            }
        };

        // If body is FormData, delete Content-Type so browser sets boundary
        if (config.body instanceof FormData) {
            delete config.headers["Content-Type"];
        }

        try {
            const resp = await fetch(url, config);
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({ detail: resp.statusText }));
                throw new Error(err.detail || `HTTP error ${resp.status}`);
            }
            return await resp.json();
        } catch (error) {
            console.warn(`[TerraWatchAPI] Request to ${endpoint} failed:`, error.message);
            throw error;
        }
    }

    return {
        BASE_URL: API_BASE,
        getToken,
        setToken,
        getUser,

        // Auth
        async login(email, password) {
            const res = await request("/auth/login", {
                method: "POST",
                body: JSON.stringify({ email, password })
            });
            setToken(res.access_token, res.user);
            return res;
        },

        async getProfile() {
            return await request("/auth/me");
        },

        async updateProfile(profileData) {
            return await request("/auth/profile", {
                method: "PUT",
                body: JSON.stringify(profileData)
            });
        },

        logout() {
            setToken(null, null);
            try {
                localStorage.removeItem("terrawatch_user");
                localStorage.removeItem("landsafe_user");
                sessionStorage.clear();
            } catch (e) {}
            window.location.href = "index.html";
        },

        // Risk & Early Warning
        async getLiveRisk(location = "Guwahati") {
            try {
                return await request(`/risk/live?location=${encodeURIComponent(location)}`);
            } catch (e) {
                return null;
            }
        },

        async getProbability(location = "Guwahati") {
            try {
                return await request(`/risk/probability?location=${encodeURIComponent(location)}`);
            } catch (e) {
                return null;
            }
        },

        async predictRisk(features) {
            return await request("/risk/predict", {
                method: "POST",
                body: JSON.stringify(features)
            });
        },

        // GIS & Map Layers
        async getLocationsGeoJSON() {
            return await request("/gis/locations");
        },

        async getSheltersGeoJSON() {
            return await request("/gis/shelters");
        },

        async getRescuePointsGeoJSON() {
            return await request("/gis/rescue-points");
        },

        async getRoadsGeoJSON() {
            return await request("/gis/roads");
        },

        async getLandslidesGeoJSON() {
            return await request("/gis/landslides");
        },

        // Alerts & Sirens
        async getAlerts(params = {}) {
            const query = new URLSearchParams(params).toString();
            return await request(`/alerts${query ? '?' + query : ''}`);
        },

        async getActiveAlerts() {
            return await request("/alerts/active");
        },

        async createAlert(alertData) {
            return await request("/alerts", {
                method: "POST",
                body: JSON.stringify(alertData)
            });
        },

        async resolveAlert(alertId) {
            return await request(`/alerts/${alertId}/resolve`, {
                method: "PATCH"
            });
        },

        async triggerSiren(location, durationSeconds = 60) {
            return await request("/alerts/sirens/trigger", {
                method: "POST",
                body: JSON.stringify({ location, duration_seconds: durationSeconds })
            });
        },

        async stopSiren() {
            return await request("/alerts/sirens/stop", {
                method: "POST"
            });
        },

        async getSirenStatus() {
            return await request("/alerts/sirens/status");
        },

        // Field Reports & Verification
        async submitReport(formData) {
            return await request("/reports", {
                method: "POST",
                body: formData
            });
        },

        async getReports(params = {}) {
            const query = new URLSearchParams(params).toString();
            return await request(`/reports${query ? '?' + query : ''}`);
        },

        async updateReportStatus(reportId, status) {
            return await request(`/reports/${reportId}/status`, {
                method: "PATCH",
                body: JSON.stringify({ status })
            });
        },

        // Emergency Response
        async getEmergencyRequests(params = {}) {
            const query = new URLSearchParams(params).toString();
            return await request(`/emergency/requests${query ? '?' + query : ''}`);
        },

        async getEmergencyPriorities() {
            return await request("/emergency/priorities");
        },

        async updateEmergencyStatus(taskId, status, assignedTeam = null) {
            return await request(`/emergency/requests/${taskId}/status`, {
                method: "PATCH",
                body: JSON.stringify({ status, assigned_team: assignedTeam })
            });
        },

        // Admin & Analytics
        async getAdminDashboard() {
            return await request("/admin/dashboard");
        },

        async getMonitorLocations() {
            return await request("/admin/monitor-locations");
        },

        async getAnalyticsLocations() {
            return await request("/analytics/locations");
        },

        async getAnalyticsSummary() {
            return await request("/analytics/summary");
        },

        async getAnalyticsTrends() {
            return await request("/analytics/trends");
        },

        async getHistoryLandslides(params = {}) {
            const query = new URLSearchParams(params).toString();
            return await request(`/admin/history/landslides${query ? '?' + query : ''}`);
        },

        // Offline Sync
        async pushSyncQueue(items) {
            return await request("/sync/push", {
                method: "POST",
                body: JSON.stringify({ items })
            });
        },

        async pullOfflineCache() {
            return await request("/sync/pull");
        },

        showToast(message, type = "info") {
            if (!document.body) return;
            let container = document.getElementById("terrawatch-toast-container") || document.getElementById("landsafe-toast-container");
            if (!container) {
                container = document.createElement("div");
                container.id = "terrawatch-toast-container";
                container.style.cssText = "position:fixed;top:20px;right:20px;z-index:99999;max-width:380px;pointer-events:none;";
                document.body.appendChild(container);
            }
            const bgClass = (type === "success") ? "bg-success text-white" :
                            (type === "danger" || type === "error") ? "bg-danger text-white" :
                            (type === "warning") ? "bg-warning text-dark" : "bg-dark text-white";
            const icon = (type === "success") ? "bi-shield-check" :
                         (type === "danger" || type === "error") ? "bi-exclamation-octagon-fill" :
                         (type === "warning") ? "bi-exclamation-triangle-fill" : "bi-bell-fill";
            const toastEl = document.createElement("div");
            toastEl.className = `toast show align-items-center ${bgClass} border-0 shadow-lg mb-2`;
            toastEl.style.cssText = "pointer-events:auto;min-width:280px;border-radius:10px;";
            toastEl.setAttribute("role", "alert");
            toastEl.innerHTML = `
                <div class="d-flex p-3 align-items-center">
                    <i class="bi ${icon} fs-4 me-3"></i>
                    <div class="toast-body p-0 flex-grow-1 small fw-semibold" style="line-height: 1.4;">${message}</div>
                    <button type="button" class="btn-close ${type === 'warning' ? '' : 'btn-close-white'} ms-2" onclick="this.closest('.toast').remove()"></button>
                </div>
            `;
            container.appendChild(toastEl);
            setTimeout(() => {
                toastEl.style.transition = "opacity 0.4s ease, transform 0.4s ease";
                toastEl.style.opacity = "0";
                toastEl.style.transform = "translateY(-10px)";
                setTimeout(() => toastEl.remove(), 400);
            }, 4500);
        }
    };
})();

// Attach globally (TerraWatchAPI is primary, LandSafeAPI kept for backwards compatibility)
window.TerraWatchAPI = TerraWatchAPI;
window.LandSafeAPI = TerraWatchAPI;
window.showToast = TerraWatchAPI.showToast;

// Gracefully elevate standard window.alert to sleek toast notifications
if (!window._originalAlert) {
    window._originalAlert = window.alert;
    window.alert = function(msg) {
        if (typeof msg === "string") {
            const lower = msg.toLowerCase();
            const type = (lower.includes("error") || lower.includes("failed") || lower.includes("danger") || lower.includes("critical")) ? "danger" :
                         (lower.includes("success") || lower.includes("saved") || lower.includes("updated") || lower.includes("resolved") || lower.includes("assigned")) ? "success" :
                         (lower.includes("warning") || lower.includes("caution") || lower.includes("alert")) ? "warning" : "info";
            TerraWatchAPI.showToast(msg, type);
        } else {
            TerraWatchAPI.showToast(String(msg), "info");
        }
    };
}

// Invalidate legacy service worker caches and unregister outdated SW instances
if (typeof window !== "undefined" && typeof navigator !== "undefined" && "serviceWorker" in navigator) {
    try {
        navigator.serviceWorker.getRegistrations().then(function(registrations) {
            for (let registration of registrations) {
                registration.unregister();
            }
        });
        if (window.caches) {
            caches.keys().then(function(names) {
                for (let name of names) {
                    caches.delete(name);
                }
            });
        }
    } catch (e) {
        // Fallback in restricted browser environments
    }
}

