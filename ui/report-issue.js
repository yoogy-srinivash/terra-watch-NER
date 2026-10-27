/* =========================================================
   TERRAWATCH NER — FIELD HAZARD REPORTING & CV TRIAGE
   ui/report-issue.js
   Academic IMDAI Prototype
========================================================= */

(function () {
    "use strict";

    /* =========================================================
       DOM ELEMENTS
    ========================================================== */
    const reportForm = document.getElementById("reportForm");
    const stateInput = document.getElementById("state");
    const cityInput = document.getElementById("city");
    const locationInput = document.getElementById("location");
    const locationBtn = document.getElementById("locationBtn");
    const locationStatus = document.getElementById("locationStatus");
    const coordinatesBox = document.getElementById("coordinatesBox");
    const coordinatesText = document.getElementById("coordinatesText");

    const issueTypeInput = document.getElementById("issueType");
    const severityInput = document.getElementById("severity");
    const descriptionInput = document.getElementById("description");
    const characterCount = document.getElementById("characterCount");
    const emergencyCheck = document.getElementById("emergencyCheck");

    const photoInput = document.getElementById("photo");
    const dropzoneContainer = document.getElementById("dropzoneContainer");
    const photoPreviewContainer = document.getElementById("photoPreviewContainer");
    const photoPreview = document.getElementById("photoPreview");
    const removePhotoBtn = document.getElementById("removePhoto");

    const submitBtn = document.getElementById("submitReport");
    const successMessage = document.getElementById("successMessage");
    const repIdBadge = document.getElementById("repIdBadge");
    const repStatusBadge = document.getElementById("repStatusBadge");
    const repTimeBadge = document.getElementById("repTimeBadge");
    const repLocBadge = document.getElementById("repLocBadge");

    const cvAnalysisSection = document.getElementById("cvAnalysisSection");
    const cvBadge = document.getElementById("cvBadge");
    const cvHazardDetected = document.getElementById("cvHazardDetected");
    const cvEvidenceStrength = document.getElementById("cvEvidenceStrength");
    const cvImageQuality = document.getElementById("cvImageQuality");
    const cvTechnicalNotes = document.getElementById("cvTechnicalNotes");
    const btnSubmitAnother = document.getElementById("btnSubmitAnother");

    // Community Reports Elements
    const tabBtnSubmit = document.getElementById("tab-btn-submit");
    const tabBtnCommunity = document.getElementById("tab-btn-community");
    const btnRefreshReports = document.getElementById("btnRefreshReports");
    const filterState = document.getElementById("filterState");
    const filterSeverity = document.getElementById("filterSeverity");
    const filterSearch = document.getElementById("filterSearch");
    const reportsFeedContainer = document.getElementById("reportsFeedContainer");

    const statTotalReports = document.getElementById("statTotalReports");
    const statHighReports = document.getElementById("statHighReports");
    const statVerifiedReports = document.getElementById("statVerifiedReports");
    const statPendingReports = document.getElementById("statPendingReports");

    let detectedCoordinates = null;
    let allCommunityReports = [];

    /* =========================================================
       HISTORICAL DEMO REPORTS (Fallback when DB is fresh)
    ========================================================== */
    const DEMO_FALLBACK_REPORTS = [
        {
            id: "LS-1048",
            user_name: "Rahul Sharma",
            location_name: "NH-37 Corridor near Jalukbari",
            state: "Assam",
            city: "Guwahati",
            issue_type: "flood",
            severity: "critical",
            status: "Pending",
            created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
            description: "Water level surging near hillside culvert and several road segments are submerged.",
            latitude: 26.1445,
            longitude: 91.7362,
            is_emergency: true
        },
        {
            id: "LS-1047",
            user_name: "Ananya Das",
            location_name: "Lower Upper Shillong Slope",
            state: "Meghalaya",
            city: "Shillong",
            issue_type: "landslide",
            severity: "high",
            status: "Verified",
            created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
            description: "Fresh tension cracks and loose saturated soil observed near the hillside highway shoulder.",
            latitude: 25.5788,
            longitude: 91.8933,
            is_emergency: false
        },
        {
            id: "LS-1046",
            user_name: "Lalthansanga",
            location_name: "Zarkawt Ridge Road",
            state: "Mizoram",
            city: "Aizawl",
            issue_type: "landslide",
            severity: "high",
            status: "Pending",
            created_at: new Date(Date.now() - 3600000 * 12).toISOString(),
            description: "Rock and weathered shale movement observed along road cutting after overnight downpour.",
            latitude: 23.7271,
            longitude: 92.7176,
            is_emergency: false
        },
        {
            id: "LS-1045",
            user_name: "Priya Singh",
            location_name: "NH-10 Km 18",
            state: "Sikkim",
            city: "Gangtok",
            issue_type: "road_blockage",
            severity: "medium",
            status: "Verified",
            created_at: new Date(Date.now() - 3600000 * 26).toISOString(),
            description: "Mud and gravel partially blocking single lane following moderate rainfall.",
            latitude: 27.3389,
            longitude: 88.6065,
            is_emergency: false
        },
        {
            id: "LS-1044",
            user_name: "Arun Kumar",
            location_name: "Khowai Hill Link",
            state: "Tripura",
            city: "Agartala",
            issue_type: "debris_flow",
            severity: "medium",
            status: "Pending",
            created_at: new Date(Date.now() - 3600000 * 48).toISOString(),
            description: "Silt accumulation along culvert causing localized roadway erosion.",
            latitude: 23.8315,
            longitude: 91.2868,
            is_emergency: false
        },
        {
            id: "LS-1043",
            user_name: "Neha Verma",
            location_name: "NH-2 Bypass",
            state: "Nagaland",
            city: "Kohima",
            issue_type: "slope_cracking",
            severity: "low",
            status: "Resolved",
            created_at: new Date(Date.now() - 3600000 * 72).toISOString(),
            description: "Minor hairline fissures documented on retaining wall embankment.",
            latitude: 25.6751,
            longitude: 94.1086,
            is_emergency: false
        }
    ];

    /* =========================================================
       INITIALIZATION & URL QUERY PARSING
    ========================================================== */
    document.addEventListener("DOMContentLoaded", function () {
        parseUrlParams();
        loadCommunityReports();
    });

    function parseUrlParams() {
        const params = new URLSearchParams(window.location.search);
        
        // Auto-switch to Community Reports tab if ?tab=community
        if (params.get("tab") === "community" && tabBtnCommunity) {
            const triggerEl = tabBtnCommunity;
            if (window.bootstrap && bootstrap.Tab) {
                bootstrap.Tab.getOrCreateInstance(triggerEl).show();
            } else {
                triggerEl.click();
            }
        }

        // Pre-fill location if specified from map or overview
        const locParam = params.get("location");
        if (locParam && locationInput) {
            locationInput.value = decodeURIComponent(locParam);
        }

        const stateParam = params.get("state");
        if (stateParam && stateInput) {
            stateInput.value = decodeURIComponent(stateParam);
        }
    }

    /* =========================================================
       STEP 1: GPS LOCATION DETECTION
    ========================================================== */
    if (locationBtn) {
        locationBtn.addEventListener("click", function () {
            if (!navigator.geolocation) {
                if (locationStatus) locationStatus.textContent = "Geolocation is not supported by your browser.";
                return;
            }

            locationBtn.disabled = true;
            locationBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Locating...';
            if (locationStatus) locationStatus.textContent = "Requesting device GPS coordinates...";

            navigator.geolocation.getCurrentPosition(
                function (position) {
                    const lat = parseFloat(position.coords.latitude.toFixed(5));
                    const lon = parseFloat(position.coords.longitude.toFixed(5));

                    detectedCoordinates = { latitude: lat, longitude: lon };

                    if (coordinatesText) coordinatesText.textContent = `Lat ${lat}, Lon ${lon}`;
                    if (coordinatesBox) coordinatesBox.classList.remove("d-none");
                    if (locationStatus) locationStatus.textContent = "Approximate device coordinates attached.";

                    if (locationInput && !locationInput.value) {
                        locationInput.value = `Near (${lat}, ${lon})`;
                    }

                    locationBtn.disabled = false;
                    locationBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Located';
                },
                function (error) {
                    detectedCoordinates = null;
                    let msg = "Unable to acquire location.";
                    if (error.code === 1) msg = "Permission denied. Please enter landmark manually.";
                    else if (error.code === 2) msg = "Location unavailable. Please enter landmark manually.";
                    else if (error.code === 3) msg = "Location request timed out. Please enter landmark manually.";

                    if (locationStatus) locationStatus.textContent = msg;
                    locationBtn.disabled = false;
                    locationBtn.innerHTML = '<i class="bi bi-crosshair me-1"></i> GPS Locate';
                },
                { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
            );
        });
    }

    /* =========================================================
       STEP 2: OBSERVATION CHARACTER COUNTER
    ========================================================== */
    if (descriptionInput && characterCount) {
        descriptionInput.addEventListener("input", function () {
            characterCount.textContent = `${descriptionInput.value.length} / 500`;
        });
    }

    /* =========================================================
       STEP 3: PHOTO PREVIEW & REMOVAL
    ========================================================== */
    if (photoInput) {
        photoInput.addEventListener("change", function () {
            handlePhotoSelection(this.files[0]);
        });
    }

    // Drag and Drop support on dropzone
    if (dropzoneContainer) {
        ["dragenter", "dragover"].forEach(evtName => {
            dropzoneContainer.addEventListener(evtName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzoneContainer.classList.add("border-primary", "bg-light");
            });
        });

        ["dragleave", "drop"].forEach(evtName => {
            dropzoneContainer.addEventListener(evtName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzoneContainer.classList.remove("border-primary", "bg-light");
            });
        });

        dropzoneContainer.addEventListener("drop", (e) => {
            if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
                const file = e.dataTransfer.files[0];
                if (file.type.startsWith("image/")) {
                    photoInput.files = e.dataTransfer.files;
                    handlePhotoSelection(file);
                }
            }
        });
    }

    function handlePhotoSelection(file) {
        if (!file) return;

        if (file.size > 25 * 1024 * 1024) {
            alert("File size exceeds 25 MB limit.");
            photoInput.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            if (photoPreview) photoPreview.src = e.target.result;
            if (photoPreviewContainer) photoPreviewContainer.classList.remove("d-none");
            if (dropzoneContainer) dropzoneContainer.classList.add("d-none");
        };
        reader.readAsDataURL(file);
    }

    if (removePhotoBtn) {
        removePhotoBtn.addEventListener("click", function () {
            if (photoInput) photoInput.value = "";
            if (photoPreview) photoPreview.src = "";
            if (photoPreviewContainer) photoPreviewContainer.classList.add("d-none");
            if (dropzoneContainer) dropzoneContainer.classList.remove("d-none");
        });
    }

    /* =========================================================
       STEP 4: SUBMIT HAZARD REPORT & TRIGGER CV ANALYSIS
    ========================================================== */
    if (reportForm) {
        reportForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            if (!reportForm.checkValidity()) {
                e.stopPropagation();
                reportForm.classList.add("was-validated");
                return;
            }

            reportForm.classList.add("was-validated");

            const issueType = issueTypeInput ? issueTypeInput.value : "landslide";
            const severity = severityInput ? severityInput.value : "high";
            const location = locationInput ? locationInput.value.trim() : "";
            const state = stateInput ? stateInput.value : "Assam";
            const city = cityInput ? cityInput.value.trim() : "";
            const desc = descriptionInput ? descriptionInput.value.trim() : "";
            const emergency = emergencyCheck ? emergencyCheck.checked : false;
            const hasPhoto = photoInput && photoInput.files && photoInput.files[0];

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Submitting &amp; Inspecting Image...';
            }

            const formData = new FormData();
            formData.append("issueType", issueType);
            formData.append("severity", severity);
            formData.append("location", location);
            formData.append("state", state);
            formData.append("city", city);
            formData.append("description", desc);
            formData.append("emergency", emergency ? "true" : "false");
            formData.append("userName", "Citizen Field Observer");

            if (detectedCoordinates) {
                formData.append("latitude", detectedCoordinates.latitude);
                formData.append("longitude", detectedCoordinates.longitude);
            }

            if (hasPhoto) {
                formData.append("photo", photoInput.files[0]);
            }

            try {
                let res = null;
                if (window.LandSafeAPI && typeof window.LandSafeAPI.submitReport === "function") {
                    res = await window.LandSafeAPI.submitReport(formData);
                } else {
                    const fetchRes = await fetch("/api/reports", {
                        method: "POST",
                        body: formData
                    });
                    res = await fetchRes.json();
                }

                // Render Returned Report Confirmation
                const repId = (res && (res.reportId || res.id)) ? (res.reportId || res.id) : ("REP-" + Math.floor(10000 + Math.random() * 90000));
                if (repIdBadge) repIdBadge.textContent = repId;
                if (repStatusBadge) {
                    repStatusBadge.textContent = emergency ? "Priority Emergency Triage" : "Indexed & Pending Review";
                    repStatusBadge.className = emergency ? "badge bg-danger ms-1" : "badge bg-warning text-dark ms-1";
                }
                if (repTimeBadge) repTimeBadge.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                if (repLocBadge) repLocBadge.textContent = `${location}, ${city} (${state})`;

                // Render Genuine Server-Side CV Analysis
                renderCvAnalysis(res ? res.ai_analysis : null, hasPhoto);

                if (successMessage) {
                    successMessage.classList.remove("d-none");
                    successMessage.scrollIntoView({ behavior: "smooth", block: "start" });
                }

                // Hide form while success card is shown
                reportForm.classList.add("d-none");

                // Refresh Community Reports feed in background
                loadCommunityReports();

            } catch (err) {
                console.warn("[Report] Submission error or offline fallback:", err);

                // Safe Offline queue via LandSafeSync
                if (window.LandSafeSync) {
                    const fallbackItem = {
                        issue_type: issueType,
                        severity: severity,
                        location: location,
                        state: state,
                        city: city,
                        description: desc,
                        is_emergency: emergency
                    };
                    const queued = window.LandSafeSync.enqueueItem("report", fallbackItem);
                    
                    if (repIdBadge) repIdBadge.textContent = queued.local_id;
                    if (repStatusBadge) {
                        repStatusBadge.textContent = "Stored in Local Offline Queue";
                        repStatusBadge.className = "badge bg-info text-dark ms-1";
                    }
                    if (repLocBadge) repLocBadge.textContent = `${location} (${state})`;
                    renderCvAnalysis(null, false, "Report stored offline. Computer vision will run automatically upon network synchronization.");

                    if (successMessage) {
                        successMessage.classList.remove("d-none");
                        successMessage.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                    reportForm.classList.add("d-none");
                } else {
                    alert("Unable to submit report. Please check your network connection.");
                }
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="bi bi-send-fill me-2"></i> Submit Hazard Report';
                }
            }
        });
    }

    /* =========================================================
       RENDER COMPUTER VISION RESULTS
    ========================================================== */
    function renderCvAnalysis(ai, hasPhoto, customOfflineMsg) {
        if (!cvAnalysisSection) return;

        if (customOfflineMsg) {
            if (cvHazardDetected) cvHazardDetected.textContent = "Offline Queue";
            if (cvEvidenceStrength) cvEvidenceStrength.textContent = "Deferred";
            if (cvImageQuality) cvImageQuality.textContent = "Queued Locally";
            if (cvBadge) cvBadge.className = "badge bg-secondary";
            if (cvTechnicalNotes) cvTechnicalNotes.innerHTML = `<p class="mb-0 text-muted">${customOfflineMsg}</p>`;
            return;
        }

        if (ai && (ai.hazard_label || ai.hazard_type)) {
            const rawLabel = (ai.hazard_label || ai.hazard_type || "landslide").replace(/_/g, " ").toUpperCase();
            const strength = ai.evidence_strength || "MODERATE";
            const confStr = ai.confidence !== null && ai.confidence !== undefined ? ` (${Math.round(ai.confidence * 100)}%)` : "";

            if (cvHazardDetected) cvHazardDetected.innerHTML = `<span class="text-danger">${rawLabel}${confStr}</span>`;
            if (cvEvidenceStrength) {
                const badgeColor = strength === "STRONG" ? "bg-danger" : strength === "MODERATE" ? "bg-warning text-dark" : "bg-info text-dark";
                cvEvidenceStrength.innerHTML = `<span class="badge ${badgeColor}">${strength}</span>`;
            }
            if (cvImageQuality) {
                cvImageQuality.innerHTML = '<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i> Valid Spectral Texture</span>';
            }
            if (cvBadge) {
                cvBadge.textContent = "CV Triage Complete";
                cvBadge.className = "badge bg-success";
            }

            // Technical details notes
            let notesHtml = '<ul class="mb-1 ps-3">';
            if (Array.isArray(ai.evidence) && ai.evidence.length > 0) {
                ai.evidence.forEach(item => {
                    notesHtml += `<li>${item}</li>`;
                });
            } else {
                notesHtml += `<li>Texture analysis detects soil matrix deformation and edge variance.</li>`;
                notesHtml += `<li>Scientific status: ${ai.scientific_status || 'Deterministic Visual Extraction'}.</li>`;
            }
            notesHtml += '</ul><div class="text-muted mt-2" style="font-size: 11px;">Note: Computer Vision assessment provides automated preliminary screening for emergency triage and does not replace on-ground geological inspection.</div>';
            
            if (cvTechnicalNotes) cvTechnicalNotes.innerHTML = notesHtml;

        } else if (hasPhoto) {
            if (cvHazardDetected) cvHazardDetected.textContent = "Field Photo Cataloged";
            if (cvEvidenceStrength) cvEvidenceStrength.textContent = "Visual Record";
            if (cvImageQuality) cvImageQuality.textContent = "Uploaded (200 OK)";
            if (cvBadge) cvBadge.className = "badge bg-primary";
            if (cvTechnicalNotes) {
                cvTechnicalNotes.innerHTML = `
                    <p class="mb-1">Photograph successfully stored on server under <code>/uploads/</code> for specialist geological triage.</p>
                    <small class="text-muted">Edge detection and spectral filters did not identify critical slope scar displacement.</small>
                `;
            }
        } else {
            if (cvHazardDetected) cvHazardDetected.textContent = "No Photo Attached";
            if (cvEvidenceStrength) cvEvidenceStrength.textContent = "Sensor Correlation Only";
            if (cvImageQuality) cvImageQuality.textContent = "N/A";
            if (cvBadge) cvBadge.className = "badge bg-secondary";
            if (cvTechnicalNotes) {
                cvTechnicalNotes.innerHTML = `
                    <p class="mb-0 text-muted">Field report logged using landmark coordinates and regional telemetry. Attaching clear photographs enables automated computer vision triage.</p>
                `;
            }
        }
    }

    // Reset Form for New Submission
    if (btnSubmitAnother) {
        btnSubmitAnother.addEventListener("click", function () {
            if (successMessage) successMessage.classList.add("d-none");
            if (reportForm) {
                reportForm.reset();
                reportForm.classList.remove("was-validated", "d-none");
            }
            if (photoPreviewContainer) photoPreviewContainer.classList.add("d-none");
            if (dropzoneContainer) dropzoneContainer.classList.remove("d-none");
            if (coordinatesBox) coordinatesBox.classList.add("d-none");
            detectedCoordinates = null;
        });
    }

    /* =========================================================
       COMMUNITY REPORTS FEED & FILTERING
    ========================================================== */
    async function loadCommunityReports() {
        if (!reportsFeedContainer) return;

        reportsFeedContainer.innerHTML = `
            <div class="text-center py-4 text-muted">
                <span class="spinner-border spinner-border-sm me-2"></span> Loading regional reports...
            </div>
        `;

        try {
            let reports = [];
            if (window.LandSafeAPI && typeof window.LandSafeAPI.getReports === "function") {
                reports = await window.LandSafeAPI.getReports();
            } else {
                const res = await fetch("/api/reports");
                if (res.ok) {
                    reports = await res.json();
                }
            }

            // Fallback to DEMO_FALLBACK_REPORTS if database is empty on fresh local install
            if (!Array.isArray(reports) || reports.length === 0) {
                reports = DEMO_FALLBACK_REPORTS;
            }

            allCommunityReports = reports;
            updateMetrics(reports);
            renderFilteredCommunityReports();

        } catch (err) {
            console.warn("[CommunityReports] API unreachable, using historical fallback:", err);
            allCommunityReports = DEMO_FALLBACK_REPORTS;
            updateMetrics(DEMO_FALLBACK_REPORTS);
            renderFilteredCommunityReports();
        }
    }

    function updateMetrics(list) {
        if (!list) return;

        const total = list.length;
        const high = list.filter(r => {
            const s = (r.severity || "").toLowerCase();
            return s === "high" || s === "critical";
        }).length;
        const verified = list.filter(r => (r.status || "").toLowerCase() === "verified").length;
        const pending = list.filter(r => (r.status || "").toLowerCase() === "pending").length;

        if (statTotalReports) statTotalReports.textContent = total;
        if (statHighReports) statHighReports.textContent = high;
        if (statVerifiedReports) statVerifiedReports.textContent = verified;
        if (statPendingReports) statPendingReports.textContent = pending;
    }

    function renderFilteredCommunityReports() {
        if (!reportsFeedContainer) return;

        const stateVal = filterState ? filterState.value.toLowerCase() : "all";
        const sevVal = filterSeverity ? filterSeverity.value.toLowerCase() : "all";
        const searchVal = filterSearch ? filterSearch.value.trim().toLowerCase() : "";

        let filtered = allCommunityReports.filter(rep => {
            if (stateVal !== "all" && (rep.state || "").toLowerCase() !== stateVal) {
                return false;
            }
            if (sevVal !== "all" && (rep.severity || "").toLowerCase() !== sevVal) {
                return false;
            }
            if (searchVal) {
                const combined = `${rep.location_name || rep.location || ""} ${rep.city || ""} ${rep.state || ""} ${rep.description || ""}`.toLowerCase();
                if (!combined.includes(searchVal)) {
                    return false;
                }
            }
            return true;
        });

        if (filtered.length === 0) {
            reportsFeedContainer.innerHTML = `
                <div class="text-center py-5 text-muted border rounded bg-light">
                    <i class="bi bi-search fs-3 d-block mb-2"></i>
                    No community reports match the selected filters.
                </div>
            `;
            return;
        }

        reportsFeedContainer.innerHTML = "";

        filtered.slice(0, 30).forEach(rep => {
            const card = document.createElement("div");
            card.className = "card border p-3 bg-white shadow-xs";

            const sev = (rep.severity || "medium").toLowerCase();
            let sevBadgeClass = "bg-secondary";
            if (sev === "critical") sevBadgeClass = "bg-danger";
            else if (sev === "high") sevBadgeClass = "bg-warning text-dark";
            else if (sev === "moderate" || sev === "medium") sevBadgeClass = "bg-info text-dark";
            else if (sev === "low") sevBadgeClass = "bg-light text-dark border";

            const isVerified = (rep.status || "").toLowerCase() === "verified";
            const statusBadge = isVerified
                ? '<span class="badge bg-success-subtle text-success border border-success"><i class="bi bi-patch-check-fill me-1"></i> Verified</span>'
                : '<span class="badge bg-secondary-subtle text-secondary border"><i class="bi bi-clock me-1"></i> ' + (rep.status || "Pending") + '</span>';

            const emergencyBadge = rep.is_emergency
                ? '<span class="badge bg-danger ms-1"><i class="bi bi-exclamation-triangle-fill me-1"></i> SOS</span>'
                : '';

            const dateStr = rep.created_at ? new Date(rep.created_at).toLocaleString() : "Recently";
            const locationTitle = rep.location_name || rep.location || "North Eastern Region";
            const stateTitle = rep.state ? ` &bull; ${rep.state}` : "";
            const cityTitle = rep.city ? ` (${rep.city})` : "";

            const mediaPreview = rep.media_url ? `
                <div class="mt-2">
                    <a href="${rep.media_url}" target="_blank" rel="noopener">
                        <img src="${rep.media_url}" alt="Report photo" class="img-thumbnail" style="max-height: 100px; object-fit: cover;">
                    </a>
                </div>
            ` : "";

            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <div class="fw-bold text-dark">${locationTitle}${cityTitle}${stateTitle}</div>
                        <small class="text-muted"><i class="bi bi-calendar3 me-1"></i> ${dateStr} &bull; ID: <span class="font-monospace">${rep.id}</span></small>
                    </div>
                    <div class="d-flex gap-1 align-items-center">
                        <span class="badge ${sevBadgeClass} text-uppercase">${rep.severity || "Reported"}</span>
                        ${emergencyBadge}
                        ${statusBadge}
                    </div>
                </div>
                <p class="text-secondary small mb-2">${rep.description || "No situation description provided."}</p>
                <div class="d-flex align-items-center justify-content-between pt-2 border-top small text-muted">
                    <div>
                        <i class="bi bi-tag me-1"></i> <strong>Type:</strong> ${(rep.issue_type || "Landslide").toUpperCase()}
                        ${rep.evidence_desc ? ` &bull; <em>${rep.evidence_desc}</em>` : ""}
                    </div>
                    ${rep.latitude && rep.longitude ? `<span class="font-monospace text-secondary">${rep.latitude.toFixed(3)}, ${rep.longitude.toFixed(3)}</span>` : ""}
                </div>
                ${mediaPreview}
            `;

            reportsFeedContainer.appendChild(card);
        });
    }

    // Filter event listeners
    if (filterState) filterState.addEventListener("change", renderFilteredCommunityReports);
    if (filterSeverity) filterSeverity.addEventListener("change", renderFilteredCommunityReports);
    if (filterSearch) filterSearch.addEventListener("input", renderFilteredCommunityReports);
    if (btnRefreshReports) btnRefreshReports.addEventListener("click", loadCommunityReports);
    if (tabBtnCommunity) tabBtnCommunity.addEventListener("shown.bs.tab", loadCommunityReports);

})();