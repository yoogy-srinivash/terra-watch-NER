/**
 * TerraWatch NER - Offline Synchronization Engine
 * Manages local queues, IndexedDB/LocalStorage storage, and automatic sync on reconnect.
 */

const TerraWatchSync = (function() {
    const QUEUE_KEY = "terrawatch_offline_queue";
    const LEGACY_QUEUE_KEY = "landsafe_offline_queue";

    function getQueue() {
        try {
            const raw = localStorage.getItem(QUEUE_KEY) || localStorage.getItem(LEGACY_QUEUE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function saveQueue(queue) {
        try {
            const serialized = JSON.stringify(queue);
            localStorage.setItem(QUEUE_KEY, serialized);
            localStorage.setItem(LEGACY_QUEUE_KEY, serialized);
        } catch (e) {
            console.error("Failed to save offline queue to localStorage:", e);
        }
    }

    function enqueueItem(entityType, payload) {
        const queue = getQueue();
        const localId = `OFFLINE-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;
        const item = {
            local_id: localId,
            device_id: "BROWSER-CLIENT-001",
            entity_type: entityType,
            payload: payload,
            client_created_at: new Date().toISOString()
        };
        queue.push(item);
        saveQueue(queue);
        renderIndicator();
        return item;
    }

    async function syncNow() {
        const queue = getQueue();
        if (!queue || queue.length === 0) {
            return;
        }

        if (!navigator.onLine) {
            console.log("[TerraWatchSync] Device still offline. Cannot sync yet.");
            return;
        }

        console.log(`[TerraWatchSync] Attempting to sync ${queue.length} offline records...`);
        try {
            const api = window.TerraWatchAPI || window.LandSafeAPI;
            if (api) {
                const res = await api.pushSyncQueue(queue);
                console.log("[TerraWatchSync] Sync results:", res);
                if (res && res.successful > 0) {
                    // Filter out processed items
                    const processedIds = (res.results || []).map(r => r.local_id);
                    const remaining = queue.filter(item => !processedIds.includes(item.local_id));
                    saveQueue(remaining);
                    showSyncNotification(`Successfully synchronized ${res.successful} offline records.`);
                }
            }
        } catch (e) {
            console.warn("[TerraWatchSync] Sync attempt failed:", e.message);
        }
        renderIndicator();
    }

    function showSyncNotification(msg) {
        const banner = document.createElement("div");
        banner.className = "alert alert-success alert-dismissible fade show position-fixed bottom-0 end-0 m-3 shadow-lg z-3";
        banner.style.zIndex = "9999";
        banner.innerHTML = `
            <i class="bi bi-cloud-check-fill me-2"></i><strong>TerraWatch Sync:</strong> ${msg}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(banner);
        setTimeout(() => banner.remove(), 6000);
    }

    function renderIndicator() {
        let el = document.getElementById("terrawatch-sync-status") || document.getElementById("landsafe-sync-status");
        if (!el) {
            el = document.createElement("div");
            el.id = "terrawatch-sync-status";
            el.className = "position-fixed top-0 end-0 p-2 z-3";
            el.style.zIndex = "9999";
            document.body.appendChild(el);
        }

        const isOnline = navigator.onLine;
        const queue = getQueue();
        const pendingCount = queue.length;

        if (isOnline && pendingCount === 0) {
            el.innerHTML = `
                <span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill shadow-sm px-2 py-1" title="Connected to TerraWatch NER Server">
                    <i class="bi bi-wifi me-1"></i> Live
                </span>
            `;
        } else if (isOnline && pendingCount > 0) {
            el.innerHTML = `
                <span class="badge bg-info-subtle text-info border border-info-subtle rounded-pill shadow-sm px-2 py-1" style="cursor:pointer;" onclick="TerraWatchSync.syncNow()" title="Click to synchronize now">
                    <i class="bi bi-arrow-repeat me-1"></i> Syncing (${pendingCount} pending)
                </span>
            `;
        } else {
            el.innerHTML = `
                <span class="badge bg-warning-subtle text-dark border border-warning-subtle rounded-pill shadow-sm px-2 py-1" title="Network disconnected. Storing offline.">
                    <i class="bi bi-wifi-off me-1"></i> Offline Mode (${pendingCount} queued)
                </span>
            `;
        }
    }

    // Initialize Event Listeners
    window.addEventListener("online", () => {
        renderIndicator();
        syncNow();
    });

    window.addEventListener("offline", () => {
        renderIndicator();
    });

    document.addEventListener("DOMContentLoaded", () => {
        renderIndicator();
        if (navigator.onLine) {
            syncNow();
        }
    });

    return {
        enqueueItem,
        getQueue,
        getQueueLength: () => getQueue().length,
        syncNow
    };
})();

// Attach globally with backward compatibility
window.TerraWatchSync = TerraWatchSync;
window.LandSafeSync = TerraWatchSync;
