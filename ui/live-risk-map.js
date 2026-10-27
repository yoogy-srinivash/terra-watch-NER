/**
 * TerraWatch NER — Live Risk Map Engine
 * Environmental Geospatial Intelligence Platform (North Eastern Region of India)
 *
 * Information Architecture:
 * - Current Risk: 32 Geographically Grounded Monitoring Stations (Low, Moderate, High, Critical)
 * - Emergency Resources:
 *     - 4 Designated Relief Shelters (Academic Prototype Demonstration)
 *     - 3 Active Rescue Points (Academic Prototype Demonstration)
 *     - 7 State Emergency Operations Centres (SEOC) (Official Government-documented)
 * - State Filter: Synchronized multi-layer regional filtering across all resources
 * - Station Inspector: Slide-out desktop panel / mobile bottom-sheet with multi-modal explainability
 *
 * Academic Prototype Notice:
 * 32 geographically grounded monitoring locations with simulated/heuristic baselines.
 */

/* =========================================================
   MAP INITIALIZATION & BOUNDS
========================================================= */

const NER_BOUNDS = [
    [21.5, 89.5],
    [29.5, 97.5]
];

const map = L.map("riskMap", {
    zoomControl: false // Custom placement for clean floating toolbar integration
}).setView([26.1445, 91.7362], 6);

// Reposition zoom controls to bottom-left to avoid colliding with top toolbar
L.control.zoom({ position: "bottomleft" }).addTo(map);

// OpenStreetMap Base Tile Layer
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &bull; TerraWatch NER IMDAI',
    maxZoom: 18,
    minZoom: 5
}).addTo(map);

/* =========================================================
   LAYER GROUPS
========================================================= */

const riskLayer = L.layerGroup().addTo(map);
const shelterLayer = L.layerGroup().addTo(map);
const rescueLayer = L.layerGroup().addTo(map);
const eocLayer = L.layerGroup().addTo(map);

let userLocationMarker = null;
let selectedStationId = null;

/* =========================================================
   EMERGENCY RESOURCES DATA & OFFICIAL PROVENANCE
========================================================= */

// 1. Emergency Shelters (Prototype Demonstration Points)
const shelters = [
    {
        id: "shelter1",
        name: "Guwahati Relief Shelter",
        type: "Emergency Relief Centre",
        lat: 26.1550,
        lng: 91.7500,
        state: "Assam",
        district: "Kamrup Metropolitan",
        capacity: 250,
        availability: "Available",
        hazardSafe: "Flood-safe elevated shelter",
        source: "Demonstration baseline data for prototype",
        verification: "Academic Prototype Resource"
    },
    {
        id: "shelter2",
        name: "Shillong Higher Ground Shelter",
        type: "Higher Ground Shelter",
        lat: 25.5900,
        lng: 91.8800,
        state: "Meghalaya",
        district: "East Khasi Hills",
        capacity: 180,
        availability: "Available",
        hazardSafe: "Landslide-aware safe zone",
        source: "Demonstration baseline data for prototype",
        verification: "Academic Prototype Resource"
    },
    {
        id: "shelter3",
        name: "Aizawl Community Relief Centre",
        type: "Relief Shelter",
        lat: 23.7350,
        lng: 92.7300,
        state: "Mizoram",
        district: "Aizawl",
        capacity: 150,
        availability: "Limited",
        hazardSafe: "Emergency relocation centre",
        source: "Demonstration baseline data for prototype",
        verification: "Academic Prototype Resource"
    },
    {
        id: "shelter4",
        name: "Agartala Emergency Shelter",
        type: "Emergency Relief Centre",
        lat: 23.8400,
        lng: 91.3000,
        state: "Tripura",
        district: "West Tripura",
        capacity: 220,
        availability: "Available",
        hazardSafe: "Flood evacuation shelter",
        source: "Demonstration baseline data for prototype",
        verification: "Academic Prototype Resource"
    }
];

// 2. Rescue Points (Prototype Demonstration Points)
const rescuePoints = [
    {
        id: "rescue1",
        name: "Guwahati Rescue Point",
        lat: 26.1350,
        lng: 91.7250,
        state: "Assam",
        district: "Kamrup Metropolitan",
        service: "Emergency Rescue Team",
        status: "Active Duty",
        source: "Demonstration baseline data for prototype",
        verification: "Academic Prototype Resource"
    },
    {
        id: "rescue2",
        name: "Shillong Rescue Point",
        lat: 25.5700,
        lng: 91.9050,
        state: "Meghalaya",
        district: "East Khasi Hills",
        service: "Mountain Rescue Team",
        status: "Active Duty",
        source: "Demonstration baseline data for prototype",
        verification: "Academic Prototype Resource"
    },
    {
        id: "rescue3",
        name: "Aizawl Rescue Point",
        lat: 23.7150,
        lng: 92.7000,
        state: "Mizoram",
        district: "Aizawl",
        service: "Emergency Response Team",
        status: "Active Duty",
        source: "Demonstration baseline data for prototype",
        verification: "Academic Prototype Resource"
    }
];

// 3. State Emergency Operations Centres (SEOC) — Government-Documented Public Contacts
const emergencyOperationsCentres = [
    {
        id: "eoc-assam",
        name: "Assam State Emergency Operation Centre",
        type: "Emergency Operations Centre",
        state: "Assam",
        district: "Kamrup Metropolitan",
        lat: 26.1433,
        lng: 91.7898,
        phone: "0361-2237219 / 1070",
        email: "sdma-assam@gov.in",
        authority: "Assam State Disaster Management Authority (ASDMA)",
        source: "Official Government Portal (sdma.assam.gov.in)",
        verification: "Government-documented"
    },
    {
        id: "eoc-meghalaya",
        name: "Meghalaya State Emergency Operation Centre",
        type: "Emergency Operations Centre",
        state: "Meghalaya",
        district: "East Khasi Hills",
        lat: 25.5788,
        lng: 91.8933,
        phone: "0364-2502098 / 1070",
        email: "sdmadeptt-meg@gov.in",
        authority: "Meghalaya State Disaster Management Authority (MSDMA)",
        source: "Official Government Portal (msdma.gov.in)",
        verification: "Government-documented"
    },
    {
        id: "eoc-sikkim",
        name: "Sikkim State Emergency Operation Centre",
        type: "Emergency Operations Centre",
        state: "Sikkim",
        district: "Gangtok",
        lat: 27.3389,
        lng: 88.6065,
        phone: "03592-201145 / 1070",
        email: "ssdma01@gmail.com",
        authority: "Sikkim State Disaster Management Authority (SSDMA)",
        source: "Official Government Portal (ssdma.nic.in)",
        verification: "Government-documented"
    },
    {
        id: "eoc-mizoram",
        name: "Mizoram State Emergency Operation Centre",
        type: "Emergency Operations Centre",
        state: "Mizoram",
        district: "Aizawl",
        lat: 23.7367,
        lng: 92.7176,
        phone: "0389-2342520 / 1070",
        email: "mizoramdmr@gmail.com",
        authority: "Disaster Management & Rehabilitation Dept, Mizoram",
        source: "Official Government Portal (mizoram.gov.in)",
        verification: "Government-documented"
    },
    {
        id: "eoc-nagaland",
        name: "Nagaland State Emergency Operation Centre",
        type: "Emergency Operations Centre",
        state: "Nagaland",
        district: "Kohima",
        lat: 25.6751,
        lng: 94.1086,
        phone: "0370-2291122 / 1070",
        email: "seoc.nsdma@gmail.com",
        authority: "Nagaland State Disaster Management Authority (NSDMA)",
        source: "Official Government Portal (nsdma.nagaland.gov.in)",
        verification: "Government-documented"
    },
    {
        id: "eoc-arunachal",
        name: "Arunachal Pradesh State Disaster Control Room",
        type: "Emergency Operations Centre",
        state: "Arunachal Pradesh",
        district: "Papum Pare",
        lat: 27.0844,
        lng: 93.6053,
        phone: "0360-3510046 / 1070",
        email: "arun01ddm@gmail.com",
        authority: "Directorate of Disaster Management, Govt of Arunachal Pradesh",
        source: "Official Government Portal (arunachal.gov.in)",
        verification: "Government-documented"
    },
    {
        id: "eoc-tripura",
        name: "Tripura State Emergency Operation Centre",
        type: "Emergency Operations Centre",
        state: "Tripura",
        district: "West Tripura",
        lat: 23.8315,
        lng: 91.2868,
        phone: "0381-2416045 / 1070",
        email: "tdma-agt@gov.in",
        authority: "Revenue Dept / Disaster Management Cell, Govt of Tripura",
        source: "Official Government Portal (tripura.gov.in)",
        verification: "Government-documented"
    }
];

let riskLocations = [];
let stationMarkersMap = new Map(); // id -> leaflet marker

/* =========================================================
   RISK COLORING & CLASSIFICATION (MONITORING STATIONS ONLY)
========================================================= */

function getRiskCategory(risk) {
    const score = Number(risk) || 0;
    if (score >= 80) return { level: "CRITICAL", class: "crit", color: "#7f1d1d", badgeClass: "bg-dark text-white" };
    if (score >= 60) return { level: "HIGH", class: "high", color: "#dc2626", badgeClass: "bg-danger text-white" };
    if (score >= 35) return { level: "MODERATE", class: "mod", color: "#d97706", badgeClass: "bg-warning text-dark" };
    return { level: "LOW", class: "low", color: "#16a34a", badgeClass: "bg-success text-white" };
}

/* =========================================================
   CUSTOM DISTINCT SVG DIVICONS
========================================================= */

// 1. Monitoring Station Marker (Sensor radial glyph color-coded by risk status)
function createStationDivIcon(location, isSelected = false) {
    const cat = getRiskCategory(location.risk);
    const hasPulse = (cat.level === "HIGH" || cat.level === "CRITICAL");
    const selectedClass = isSelected ? "is-selected" : "";
    const pulseHtml = hasPulse ? '<span class="station-pulse-ring"></span>' : "";

    const html = `
        <div class="ls-station-marker-container ${cat.class} ${selectedClass}">
            ${pulseHtml}
            <div class="station-marker-badge" style="background-color: ${cat.color};">
                <svg viewBox="0 0 24 24" class="sensor-svg-icon" aria-hidden="true">
                    <circle cx="12" cy="12" r="3" fill="#ffffff"/>
                    <path d="M12 2a10 10 0 0 0-7.07 17.07l1.41-1.41A8 8 0 0 1 12 4v-2z" fill="#ffffff" opacity="0.9"/>
                    <path d="M12 6a6 6 0 0 0-4.24 10.24l1.41-1.41A4 4 0 0 1 12 8V6z" fill="#ffffff" opacity="0.9"/>
                    <path d="M12 2a10 10 0 0 1 7.07 17.07l-1.41-1.41A8 8 0 0 0 12 4v-2z" fill="#ffffff" opacity="0.9"/>
                    <path d="M12 6a6 6 0 0 1 4.24 10.24l-1.41-1.41A4 4 0 0 0 12 8V6z" fill="#ffffff" opacity="0.9"/>
                </svg>
            </div>
        </div>
    `;

    return L.divIcon({
        className: "ls-station-divicon",
        html: html,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
    });
}

// 2. Emergency Shelter Marker (House + Shield icon, teal infrastructure accent)
function createShelterDivIcon() {
    const html = `
        <div class="ls-shelter-marker-container" title="Emergency Shelter">
            <div class="shelter-badge">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="#ffffff" aria-hidden="true">
                    <path d="M12 3L2 12h3v8h6v-5h2v5h6v-8h3L12 3z"/>
                </svg>
            </div>
            <div class="shelter-tip"></div>
        </div>
    `;

    return L.divIcon({
        className: "ls-shelter-divicon",
        html: html,
        iconSize: [26, 32],
        iconAnchor: [13, 30],
        popupAnchor: [0, -30]
    });
}

// 3. Rescue Point Marker (Lifesaver / emergency response icon, royal blue accent)
function createRescueDivIcon() {
    const html = `
        <div class="ls-rescue-marker-container" title="Rescue Point">
            <div class="rescue-badge">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="#ffffff" aria-hidden="true">
                    <circle cx="12" cy="12" r="9" stroke="#ffffff" stroke-width="2.4" fill="none"/>
                    <circle cx="12" cy="12" r="4" stroke="#ffffff" stroke-width="2.4" fill="none"/>
                    <line x1="12" y1="3" x2="12" y2="7.5" stroke="#ffffff" stroke-width="2.4"/>
                    <line x1="12" y1="16.5" x2="12" y2="21" stroke="#ffffff" stroke-width="2.4"/>
                    <line x1="3" y1="12" x2="7.5" y2="12" stroke="#ffffff" stroke-width="2.4"/>
                    <line x1="16.5" y1="12" x2="21" y2="12" stroke="#ffffff" stroke-width="2.4"/>
                </svg>
            </div>
            <div class="rescue-tip"></div>
        </div>
    `;

    return L.divIcon({
        className: "ls-rescue-divicon",
        html: html,
        iconSize: [26, 32],
        iconAnchor: [13, 30],
        popupAnchor: [0, -30]
    });
}

// 4. Emergency Operations Centre (SEOC) Marker (Institutional broadcast building, indigo accent)
function createEocDivIcon() {
    const html = `
        <div class="ls-eoc-marker-container" title="Emergency Operations Centre">
            <div class="eoc-badge">
                <svg viewBox="0 0 24 24" width="15" height="15" fill="#ffffff" aria-hidden="true">
                    <path d="M12 2L2 7v2h20V7L12 2zm-8 8v9h2v-9H4zm5 0v9h2v-9H9zm5 0v9h2v-9h-2zm5 0v9h2v-9h-2zM2 20v2h20v-2H2z"/>
                </svg>
            </div>
            <div class="eoc-tip"></div>
        </div>
    `;

    return L.divIcon({
        className: "ls-eoc-divicon",
        html: html,
        iconSize: [26, 32],
        iconAnchor: [13, 30],
        popupAnchor: [0, -30]
    });
}

// 5. User Geolocation Marker (Cyan radar pulse pin)
function createUserDivIcon() {
    const html = `
        <div class="ls-user-marker-container" title="Your Location">
            <div class="user-pulse-wave"></div>
            <div class="user-center-point"></div>
        </div>
    `;

    return L.divIcon({
        className: "ls-user-divicon",
        html: html,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14]
    });
}

/* =========================================================
   GEOTECHNICAL BASELINE ESTIMATION (ACADEMIC PROTOTYPE)
========================================================= */

function calculateGeotechnicalBaselineRisk(loc) {
    const slope = loc.slope_angle_deg != null ? Number(loc.slope_angle_deg) : 22.0;
    const elev = loc.elevation_m != null ? Number(loc.elevation_m) : 400.0;
    const ndvi = loc.ndvi != null ? Number(loc.ndvi) : 0.6;

    let score = (slope * 2.1) + ((elev / 1000) * 8.0) + ((1 - ndvi) * 15.0);
    let rain = 40;
    const state = loc.state || "";
    if (state.includes("Meghalaya")) rain = 82;
    else if (state.includes("Sikkim")) rain = 68;
    else if (state.includes("Mizoram")) rain = 62;
    else if (state.includes("Arunachal")) rain = 55;
    else if (state.includes("Nagaland")) rain = 50;
    else rain = 38;

    score += (rain * 0.22);
    score = Math.min(94, Math.max(22, Math.round(score)));

    const cat = getRiskCategory(score);
    return { score, level: cat.level, rain };
}

function normalizeLocation(location) {
    return {
        id: location.id,
        name: location.location,
        district: location.district,
        state: location.state,
        lat: Number(location.latitude),
        lng: Number(location.longitude),
        population_exposed: Number(location.population_exposed || 0),
        roads_exposed: Number(location.roads_exposed || 0),
        critical_assets: Number(location.critical_assets || 0),
        slope_angle_deg: location.slope_angle_deg != null ? location.slope_angle_deg : null,
        elevation_m: location.elevation_m != null ? location.elevation_m : null,
        risk: null,
        riskLevel: null,
        rainfall: null,
        status: "Monitoring Active"
    };
}

/* =========================================================
   LOAD STATIONS DATA
========================================================= */

async function loadRiskLocations() {
    try {
        let locations = null;

        // 1. Try static JSON first for zero-latency load
        try {
            const resp = await fetch("/gis/locations.json");
            if (resp.ok) {
                locations = await resp.json();
            }
        } catch (e) {
            console.warn("[LiveMap] Static locations.json fetch fallback:", e.message);
        }

        // 2. Fallback to API GeoJSON
        const api = window.TerraWatchAPI || window.LandSafeAPI;
        if (!locations && api) {
            try {
                const geojson = await api.getLocationsGeoJSON();
                if (geojson && geojson.features && geojson.features.length > 0) {
                    locations = geojson.features.map(f => ({
                        id: f.properties.id,
                        location: f.properties.name,
                        district: f.properties.district,
                        state: f.properties.state,
                        latitude: f.geometry.coordinates[1],
                        longitude: f.geometry.coordinates[0],
                        population_exposed: f.properties.population_exposed,
                        roads_exposed: f.properties.roads_exposed,
                        critical_assets: f.properties.critical_assets,
                        risk: f.properties.risk || f.properties.risk_score,
                        riskLevel: f.properties.riskLevel || f.properties.risk_level,
                        rainfall: f.properties.rainfall_24h_mm || 45
                    }));
                }
            } catch (e) {
                console.warn("[LiveMap] API GeoJSON fallback:", e.message);
            }
        }

        if (!Array.isArray(locations) || locations.length === 0) {
            throw new Error("Could not load GIS stations array");
        }

        const ids = new Set();
        riskLocations = locations.map(loc => {
            if (!loc.id || ids.has(loc.id)) return null;
            ids.add(loc.id);

            const normalized = normalizeLocation(loc);
            if (loc.risk != null) {
                normalized.risk = loc.risk;
                normalized.riskLevel = loc.riskLevel || getRiskCategory(loc.risk).level;
                normalized.rainfall = loc.rainfall || 45;
            } else {
                const baseline = calculateGeotechnicalBaselineRisk(loc);
                normalized.risk = baseline.score;
                normalized.riskLevel = baseline.level;
                normalized.rainfall = baseline.rain;
            }

            if (loc.slope_angle_deg != null) normalized.slope_angle_deg = loc.slope_angle_deg;
            if (loc.elevation_m != null) normalized.elevation_m = loc.elevation_m;
            return normalized;
        }).filter(Boolean);

        // Render all layers
        renderStations(riskLocations);
        renderShelters(shelters);
        renderRescuePoints(rescuePoints);
        renderEocPoints(emergencyOperationsCentres);
        updateResourceCounts(riskLocations.length, shelters.length, rescuePoints.length, emergencyOperationsCentres.length);

        console.log(`[LiveMap] Successfully loaded ${riskLocations.length} monitoring stations across NER.`);
    } catch (err) {
        console.error("[LiveMap] Error loading locations:", err);
    }
}

/* =========================================================
   MARKER RENDERING FUNCTIONS
========================================================= */

// 1. Render Stations (No duplicate Leaflet popup; click opens Inspector Drawer directly)
function renderStations(stationsList) {
    riskLayer.clearLayers();
    stationMarkersMap.clear();

    stationsList.forEach(location => {
        const isSelected = (location.id === selectedStationId);
        const icon = createStationDivIcon(location, isSelected);

        const marker = L.marker([location.lat, location.lng], {
            icon: icon,
            title: `${location.name} — ${location.state} (${location.riskLevel} Risk)`
        });

        // Lightweight hover tooltip only (NO duplicate popup clash)
        const cat = getRiskCategory(location.risk);
        marker.bindTooltip(`
            <div class="fw-semibold">${location.name}</div>
            <div class="small text-muted">${location.state} &bull; <span style="color: ${cat.color}; font-weight:700;">${cat.level} (${Math.round(location.risk)}/100)</span></div>
        `, {
            direction: "top",
            offset: [0, -14],
            className: "ls-station-tooltip"
        });

        // Click selects marker and opens the Station Inspector Drawer
        marker.on("click", () => {
            selectStation(location.id);
        });

        marker.addTo(riskLayer);
        stationMarkersMap.set(location.id, marker);
    });
}

// 2. Render Emergency Shelters (Accurate popup with academic provenance)
function renderShelters(sheltersList) {
    shelterLayer.clearLayers();

    sheltersList.forEach(shelter => {
        const marker = L.marker([shelter.lat, shelter.lng], {
            icon: createShelterDivIcon(),
            title: shelter.name
        });

        marker.bindPopup(`
            <div class="ls-compact-popup">
                <div class="popup-tag text-teal"><i class="bi bi-house-door me-1"></i> Emergency Shelter</div>
                <h6 class="fw-bold mb-1">${shelter.name}</h6>
                <div class="small text-muted mb-2">${shelter.district ? shelter.district + ', ' : ''}${shelter.state}</div>
                <div class="popup-row"><span>Type:</span><strong>${shelter.type}</strong></div>
                <div class="popup-row"><span>Capacity:</span><strong>${shelter.capacity} people</strong></div>
                <div class="popup-row"><span>Status:</span><span class="badge bg-secondary">${shelter.availability}</span></div>
                <div class="popup-row"><span>Safety Note:</span><span class="text-secondary">${shelter.hazardSafe}</span></div>
                <div class="popup-provenance mt-2 pt-1 border-top">
                    <small class="text-muted"><i class="bi bi-info-circle me-1"></i> Provenance: <strong>${shelter.verification}</strong></small>
                </div>
                <button type="button" class="btn btn-xs btn-outline-secondary w-100 mt-2 py-1" onclick="focusShelter('${shelter.id}')">
                    <i class="bi bi-compass me-1"></i> Center Shelter View
                </button>
            </div>
        `, { maxWidth: 260 });

        marker.addTo(shelterLayer);
    });
}

// 3. Render Rescue Points (Accurate popup with prototype provenance)
function renderRescuePoints(rescueList) {
    rescueLayer.clearLayers();

    rescueList.forEach(point => {
        const marker = L.marker([point.lat, point.lng], {
            icon: createRescueDivIcon(),
            title: point.name
        });

        marker.bindPopup(`
            <div class="ls-compact-popup">
                <div class="popup-tag text-primary"><i class="bi bi-life-preserver me-1"></i> Rescue Point</div>
                <h6 class="fw-bold mb-1">${point.name}</h6>
                <div class="small text-muted mb-2">${point.district ? point.district + ', ' : ''}${point.state}</div>
                <div class="popup-row"><span>Service:</span><strong>${point.service}</strong></div>
                <div class="popup-row"><span>Status:</span><span class="badge bg-secondary">${point.status}</span></div>
                <div class="popup-provenance mt-2 pt-1 border-top">
                    <small class="text-muted"><i class="bi bi-info-circle me-1"></i> Provenance: <strong>${point.verification}</strong></small>
                </div>
                <a href="report-issue.html" class="btn btn-xs btn-outline-primary w-100 mt-2 py-1">
                    <i class="bi bi-flag-fill me-1"></i> Citizen Hazard Report
                </a>
            </div>
        `, { maxWidth: 260 });

        marker.addTo(rescueLayer);
    });
}

// 4. Render Emergency Operations Centres (SEOC) (Official government contacts)
function renderEocPoints(eocList) {
    eocLayer.clearLayers();

    eocList.forEach(eoc => {
        const marker = L.marker([eoc.lat, eoc.lng], {
            icon: createEocDivIcon(),
            title: eoc.name
        });

        marker.bindPopup(`
            <div class="ls-compact-popup">
                <div class="popup-tag text-indigo"><i class="bi bi-building-check me-1"></i> Emergency Operations Centre</div>
                <h6 class="fw-bold mb-1">${eoc.name}</h6>
                <div class="small text-muted mb-2">${eoc.district ? eoc.district + ', ' : ''}${eoc.state}</div>
                <div class="popup-row"><span>Helpline:</span><strong class="text-primary">${eoc.phone}</strong></div>
                ${eoc.email ? `<div class="popup-row"><span>Email:</span><span class="text-secondary small text-break">${eoc.email}</span></div>` : ''}
                <div class="popup-row"><span>Authority:</span><span class="small">${eoc.authority}</span></div>
                <div class="popup-provenance mt-2 pt-1 border-top">
                    <span class="badge bg-light text-dark border"><i class="bi bi-patch-check-fill text-primary me-1"></i> ${eoc.verification}</span>
                </div>
                <a href="tel:${eoc.phone.split('/')[0].trim()}" class="btn btn-xs btn-outline-dark w-100 mt-2 py-1">
                    <i class="bi bi-telephone-fill me-1"></i> Call Control Room
                </a>
            </div>
        `, { maxWidth: 270 });

        marker.addTo(eocLayer);
    });
}

/* =========================================================
   STATION SELECTION & INSPECTOR DRAWER
========================================================= */

function selectStation(stationId) {
    const location = riskLocations.find(l => l.id === stationId || l.name === stationId);
    if (!location) return;

    selectedStationId = location.id;

    // Refresh marker icons to reflect active selection state
    stationMarkersMap.forEach((marker, id) => {
        const loc = riskLocations.find(l => l.id === id);
        if (loc) {
            marker.setIcon(createStationDivIcon(loc, id === selectedStationId));
        }
    });

    // Fly camera smoothly to station (offset on desktop to account for drawer width)
    const isDesktop = window.innerWidth >= 992;
    if (isDesktop) {
        // Offset center slightly to the left so drawer doesn't obstruct station
        const targetLng = location.lng + 0.15;
        map.flyTo([location.lat, targetLng], 11, { animate: true, duration: 0.8 });
    } else {
        map.flyTo([location.lat, location.lng], 12, { animate: true, duration: 0.6 });
    }

    // Render Inspector Drawer Content
    showLocationDetails(location);
}

function showLocationDetails(location) {
    const drawer = document.getElementById("stationDrawer");
    if (drawer) {
        drawer.classList.add("active");
    }

    const selectedContainer = document.getElementById("selectedLocation");
    if (!selectedContainer) return;

    const cat = getRiskCategory(location.risk);
    const riskScore = Math.round(location.risk);

    // Plain language contributing factors
    let whyElevatedText = "";
    if (cat.level === "CRITICAL" || cat.level === "HIGH") {
        whyElevatedText = `Rainfall accumulation combined with steep terrain gradient (slope angle ${location.slope_angle_deg || 32}°) indicates elevated probability of slope instability along transportation and settlement corridors. Geotechnical sensor alert threshold active.`;
    } else if (cat.level === "MODERATE") {
        whyElevatedText = `Localized precipitation and topographic slope gradient warrant active observation. Seasonal saturation indices approaching caution threshold.`;
    } else {
        whyElevatedText = `Current topographic slope equilibrium and moderate precipitation baselines indicate stable terrain conditions across this regional monitoring corridor.`;
    }

    selectedContainer.className = "card border-0 mb-0 p-0 overflow-hidden";
    selectedContainer.innerHTML = `
        <!-- Drawer Header -->
        <div class="station-drawer-header d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
                <div class="d-flex align-items-center gap-2">
                    <span class="legend-glyph station me-1"></span>
                    <h5 class="fw-bold mb-0 text-dark">${location.name}</h5>
                </div>
                <small class="text-secondary">${location.district ? location.district + ', ' : ''}${location.state} &bull; Station ID: <code>${location.id}</code></small>
            </div>
            <div class="d-flex align-items-center gap-2">
                <span class="badge ${cat.badgeClass} px-3 py-1 fs-6">${cat.level} RISK &bull; ${riskScore}/100</span>
                <button type="button" class="btn-close ms-1" onclick="closeStationDrawer()" aria-label="Close" title="Close Panel"></button>
            </div>
        </div>

        <div class="station-drawer-body p-3">
            <!-- 1. WHY IS THIS RISK ELEVATED? -->
            <div class="mb-3">
                <div class="text-uppercase fw-bold text-muted small mb-1" style="letter-spacing: 0.5px; font-size: 0.72rem;">
                    <i class="bi bi-question-circle me-1 text-primary"></i> Why is this risk assessed as ${cat.level}?
                </div>
                <div class="p-2 px-3 bg-light border rounded small text-dark" style="line-height: 1.45;">
                    ${whyElevatedText}
                </div>
            </div>

            <!-- 2. MONITORING (SENSOR & TERRAIN INFORMATION) -->
            <div class="mb-3">
                <div class="text-uppercase fw-bold text-muted small mb-2" style="letter-spacing: 0.5px; font-size: 0.72rem;">
                    <i class="bi bi-activity me-1 text-primary"></i> Monitoring & Telemetry Parameters
                </div>
                <div class="row g-2">
                    <div class="col-6">
                        <div class="metric-pill">
                            <div class="label"><i class="bi bi-cloud-rain me-1"></i> 24h Rainfall</div>
                            <div class="value">${location.rainfall ? location.rainfall + ' mm' : '42 mm'}</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="metric-pill">
                            <div class="label"><i class="bi bi-layers me-1"></i> Slope Angle</div>
                            <div class="value">${location.slope_angle_deg != null ? location.slope_angle_deg + '°' : '32°'}</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="metric-pill">
                            <div class="label"><i class="bi bi-droplet-half me-1"></i> Soil Moisture</div>
                            <div class="value" id="drawerSoilMoisture_${location.id}">74%</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="metric-pill">
                            <div class="label"><i class="bi bi-speedometer2 me-1"></i> Pore Pressure</div>
                            <div class="value" id="drawerPorePress_${location.id}">18.4 kPa</div>
                        </div>
                    </div>
                    ${location.elevation_m != null ? `
                    <div class="col-6">
                        <div class="metric-pill">
                            <div class="label"><i class="bi bi-triangle me-1"></i> Elevation</div>
                            <div class="value">${Math.round(location.elevation_m)} m</div>
                        </div>
                    </div>` : ''}
                    <div class="col-6">
                        <div class="metric-pill">
                            <div class="label"><i class="bi bi-people me-1"></i> Population Exposed</div>
                            <div class="value">${Number(location.population_exposed || 0).toLocaleString()}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 3. ACTIONS -->
            <div class="mb-3">
                <a href="probability-risk.html?city=${encodeURIComponent(location.name)}" class="btn btn-sm btn-primary w-100 py-2 fw-semibold">
                    <i class="bi bi-cpu me-1"></i> Assess in AI Risk Lab (Inference)
                </a>
            </div>

            <!-- 4. TECHNICAL AI EXPLAINABILITY & PROVENANCE (EXPANDABLE) -->
            <details class="tech-details-accordion">
                <summary class="tech-details-summary d-flex justify-content-between align-items-center">
                    <span><i class="bi bi-cpu-fill text-success me-1"></i> Dual ML Models & TreeSHAP Details</span>
                    <span class="small text-muted">Inspect</span>
                </summary>
                <div class="p-3 bg-white border border-top-0 rounded-bottom" id="mapFusionDetails_${location.id}">
                    <div class="text-center text-muted small py-2">
                        <span class="spinner-border spinner-border-sm me-1"></span> Loading TreeSHAP attribution and dual-model weights...
                    </div>
                </div>
            </details>
        </div>
    `;

    // Asynchronously fetch live fusion & TreeSHAP attributions
    const apiForRisk = window.TerraWatchAPI || window.LandSafeAPI;
    if (apiForRisk && typeof apiForRisk.getLiveRisk === "function") {
        apiForRisk.getLiveRisk(location.name || location.id).then((liveData) => {
            const fusionEl = document.getElementById(`mapFusionDetails_${location.id}`);
            if (!fusionEl || !liveData) return;

            const fusion = liveData.fusion;
            const spatial = fusion?.components?.spatial;
            const temporal = fusion?.components?.temporal;

            // Update live telemetry pills
            const soilEl = document.getElementById(`drawerSoilMoisture_${location.id}`);
            if (soilEl && temporal?.metrics?.soil_moisture?.current) {
                soilEl.textContent = `${temporal.metrics.soil_moisture.current}%`;
            }
            const poreEl = document.getElementById(`drawerPorePress_${location.id}`);
            if (poreEl && temporal?.metrics?.pore_pressure?.current) {
                poreEl.textContent = `${temporal.metrics.pore_pressure.current} kPa`;
            }

            const shapFactors = spatial?.top_shap_factors || [];
            const shapHtml = shapFactors.length > 0 
                ? shapFactors.slice(0, 3).map(f => `<li>&bull; <strong>${f.feature}</strong>: ${f.attribution > 0 ? '+' : ''}${Number(f.attribution).toFixed(3)} log-odds</li>`).join("")
                : "<li>&bull; Primary contributors: Topographic slope gradient and recent rainfall volume</li>";

            const overrideHtml = (fusion?.overrides?.triggered && fusion.overrides.rules?.length > 0)
                ? `<div class="alert alert-danger py-1 px-2 mb-2 small"><strong><i class="bi bi-shield-exclamation me-1"></i>Safety Override Active:</strong> ${fusion.overrides.rules[0].override_reason}</div>`
                : "";

            fusionEl.innerHTML = `
                ${overrideHtml}
                <div class="row g-2 small text-secondary">
                    <div class="col-12 col-md-6">
                        <div><strong>Dual ML Pipeline:</strong> ${spatial?.active_model || 'LightGBM'} (Standby: ${spatial?.standby_model || 'XGBoost'}, Agreement: ${spatial?.ensemble_agreement_pct ?? 97}%)</div>
                        <div class="mt-1"><strong>Top Contributing Drivers:</strong></div>
                        <ul class="list-unstyled ps-1 text-dark mb-1">${shapHtml}</ul>
                    </div>
                    <div class="col-12 col-md-6">
                        <div><strong>Telemetry Trend:</strong> <span class="badge bg-secondary">${temporal?.trend || 'STABLE'}</span></div>
                        <div class="mt-1"><strong>Decision Basis:</strong> ${fusion?.decision_basis ? fusion.decision_basis[fusion.decision_basis.length - 1] : 'Continuous multi-modal risk integration.'}</div>
                        <div class="mt-1"><strong>Model Weights:</strong> Spatial (w=0.50), Temporal (w=0.35), Visual (w=0.15)</div>
                    </div>
                </div>
                <div class="mt-2 pt-2 border-top small text-muted" style="font-size: 11px;">
                    <em>Academic Demonstration Prototype &bull; 32 geographically grounded monitoring locations &bull; Simulated or heuristic academic baselines.</em>
                </div>
            `;
        }).catch(() => {});
    }
}

function closeStationDrawer() {
    const drawer = document.getElementById("stationDrawer");
    if (drawer) {
        drawer.classList.remove("active");
        drawer.classList.remove("expanded");
    }
    selectedStationId = null;
    stationMarkersMap.forEach((marker, id) => {
        const loc = riskLocations.find(l => l.id === id);
        if (loc) {
            marker.setIcon(createStationDivIcon(loc, false));
        }
    });
}
window.closeStationDrawer = closeStationDrawer;

function toggleDrawerExpand() {
    const drawer = document.getElementById("stationDrawer");
    if (drawer) {
        drawer.classList.toggle("expanded");
    }
}
window.toggleDrawerExpand = toggleDrawerExpand;

/* =========================================================
   SYNCHRONIZED STATE FILTERING (ALL RESOURCES)
========================================================= */

function updateResourceCounts(stationsCount, sheltersCount, rescueCount, eocCount) {
    const stationCountEl = document.getElementById("totalStationCount");
    if (stationCountEl) stationCountEl.textContent = stationsCount;

    const shelterCountEl = document.getElementById("shelterCount");
    if (shelterCountEl) shelterCountEl.textContent = sheltersCount;

    const rescueCountEl = document.getElementById("rescueCount");
    if (rescueCountEl) rescueCountEl.textContent = rescueCount;

    const eocCountEl = document.getElementById("eocCount");
    if (eocCountEl) eocCountEl.textContent = eocCount;
}

function filterByState(selectedState) {
    const stateNorm = (selectedState || "ALL").trim().toUpperCase();

    // 1. Filter stations
    const filteredStations = (stateNorm === "ALL")
        ? riskLocations
        : riskLocations.filter(loc => (loc.state || "").trim().toUpperCase() === stateNorm);

    // 2. Filter shelters
    const filteredShelters = (stateNorm === "ALL")
        ? shelters
        : shelters.filter(s => (s.state || "").trim().toUpperCase() === stateNorm);

    // 3. Filter rescue points
    const filteredRescue = (stateNorm === "ALL")
        ? rescuePoints
        : rescuePoints.filter(r => (r.state || "").trim().toUpperCase() === stateNorm);

    // 4. Filter Emergency Operations Centres
    const filteredEOC = (stateNorm === "ALL")
        ? emergencyOperationsCentres
        : emergencyOperationsCentres.filter(e => (e.state || "").trim().toUpperCase() === stateNorm);

    // Render layers
    renderStations(filteredStations);
    renderShelters(filteredShelters);
    renderRescuePoints(filteredRescue);
    renderEocPoints(filteredEOC);
    updateResourceCounts(filteredStations.length, filteredShelters.length, filteredRescue.length, filteredEOC.length);

    // Dynamic bounding box recalculation
    if (stateNorm === "ALL") {
        map.fitBounds(NER_BOUNDS, { padding: [20, 20] });
    } else {
        const allPoints = [
            ...filteredStations.map(l => [l.lat, l.lng]),
            ...filteredShelters.map(s => [s.lat, s.lng]),
            ...filteredRescue.map(r => [r.lat, r.lng]),
            ...filteredEOC.map(e => [e.lat, e.lng])
        ];

        if (allPoints.length > 0) {
            const lats = allPoints.map(p => p[0]);
            const lngs = allPoints.map(p => p[1]);
            const bounds = [
                [Math.min(...lats) - 0.25, Math.min(...lngs) - 0.25],
                [Math.max(...lats) + 0.25, Math.max(...lngs) + 0.25]
            ];
            map.fitBounds(bounds, { padding: [35, 35] });
        } else {
            map.fitBounds(NER_BOUNDS, { padding: [20, 20] });
        }
    }
}

/* =========================================================
   SEARCH WITH AUTOCOMPLETE & INLINE FEEDBACK (NO ALERTS)
========================================================= */

function setupSearch() {
    const searchInput = document.getElementById("locationSearch");
    const searchBtn = document.getElementById("searchButton");
    const clearBtn = document.getElementById("searchClearBtn");
    const suggestionsMenu = document.getElementById("searchSuggestions");
    const feedbackMsg = document.getElementById("searchFeedback");

    if (!searchInput) return;

    function showInlineFeedback(msg, isSuccess = false) {
        if (!feedbackMsg) return;
        feedbackMsg.textContent = msg;
        feedbackMsg.className = `search-feedback-msg ${isSuccess ? 'text-success' : 'text-danger'}`;
        feedbackMsg.classList.remove("d-none");
        setTimeout(() => {
            feedbackMsg.classList.add("d-none");
        }, 3200);
    }

    function renderSuggestions(query) {
        if (!suggestionsMenu) return;
        const q = query.trim().toLowerCase();

        if (q.length < 1) {
            suggestionsMenu.classList.add("d-none");
            suggestionsMenu.innerHTML = "";
            return;
        }

        const matches = riskLocations.filter(loc => 
            loc.name.toLowerCase().includes(q) ||
            (loc.district && loc.district.toLowerCase().includes(q)) ||
            (loc.state && loc.state.toLowerCase().includes(q))
        ).slice(0, 5);

        if (matches.length === 0) {
            suggestionsMenu.innerHTML = `<div class="suggestion-item text-muted">No matching station found</div>`;
            suggestionsMenu.classList.remove("d-none");
            return;
        }

        suggestionsMenu.innerHTML = matches.map(loc => {
            const cat = getRiskCategory(loc.risk);
            return `
                <div class="suggestion-item d-flex justify-content-between align-items-center" data-id="${loc.id}">
                    <div>
                        <div class="fw-semibold text-dark">${loc.name}</div>
                        <small class="text-secondary">${loc.district ? loc.district + ', ' : ''}${loc.state}</small>
                    </div>
                    <span class="badge ${cat.badgeClass}">${cat.level}</span>
                </div>
            `;
        }).join("");

        suggestionsMenu.querySelectorAll(".suggestion-item[data-id]").forEach(item => {
            item.addEventListener("click", () => {
                const stationId = item.getAttribute("data-id");
                const loc = riskLocations.find(l => l.id === stationId);
                if (loc) {
                    searchInput.value = loc.name;
                    if (clearBtn) clearBtn.classList.remove("d-none");
                    suggestionsMenu.classList.add("d-none");
                    selectStation(loc.id);
                }
            });
        });

        suggestionsMenu.classList.remove("d-none");
    }

    function executeSearch() {
        const query = searchInput.value.trim().toLowerCase();
        if (!query) {
            showInlineFeedback("Please enter a station name or location.");
            return;
        }

        const matched = riskLocations.find(loc => 
            loc.name.toLowerCase().includes(query) ||
            (loc.district && loc.district.toLowerCase().includes(query)) ||
            (loc.state && loc.state.toLowerCase().includes(query))
        );

        if (matched) {
            if (suggestionsMenu) suggestionsMenu.classList.add("d-none");
            selectStation(matched.id);
        } else {
            showInlineFeedback("No matching station found. Try Shillong, Guwahati, or Aizawl.");
        }
    }

    searchInput.addEventListener("input", function() {
        if (clearBtn) {
            if (this.value.length > 0) clearBtn.classList.remove("d-none");
            else clearBtn.classList.add("d-none");
        }
        renderSuggestions(this.value);
    });

    searchInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            executeSearch();
        }
    });

    if (searchBtn) searchBtn.addEventListener("click", executeSearch);

    if (clearBtn) {
        clearBtn.addEventListener("click", function() {
            searchInput.value = "";
            clearBtn.classList.add("d-none");
            if (suggestionsMenu) suggestionsMenu.classList.add("d-none");
        });
    }

    // Dismiss suggestions when clicking outside
    document.addEventListener("click", function(e) {
        if (!searchInput.contains(e.target) && suggestionsMenu && !suggestionsMenu.contains(e.target)) {
            suggestionsMenu.classList.add("d-none");
        }
    });
}

/* =========================================================
   SHELTER FOCUS (ACADEMIC PREVIEW)
========================================================= */

function focusShelter(id) {
    const shelter = shelters.find(s => s.id === id);
    if (!shelter) return;

    map.flyTo([shelter.lat, shelter.lng], 13, { animate: true, duration: 0.8 });

    const routeResult = document.getElementById("routeResult");
    if (routeResult) {
        routeResult.innerHTML = `
            <strong>${shelter.name}</strong> (${shelter.type}) centered.
            <div class="small mt-1 text-muted">Shelter location &bull; ${shelter.verification}</div>
        `;
    }

    // If inside modal, dismiss modal smoothly
    const modalEl = document.getElementById("evacModal");
    if (modalEl && window.bootstrap) {
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();
    }
}
window.focusShelter = focusShelter;

/* =========================================================
   POPULATE SHELTER CARDS & MODAL SELECT
========================================================= */

function setupSheltersModal() {
    const shelterCardsContainer = document.getElementById("shelterCards");
    const shelterSelect = document.getElementById("shelterSelect");
    const routeButton = document.getElementById("routeButton");

    if (shelterCardsContainer) {
        shelterCardsContainer.innerHTML = shelters.map(s => `
            <div class="col-12 col-md-6 col-xl-3">
                <div class="card border h-100 shadow-sm">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
                            <h6 class="fw-bold mb-0 text-dark">${s.name}</h6>
                            <span class="badge ${s.availability === 'Available' ? 'bg-success' : 'bg-warning text-dark'}">${s.availability}</span>
                        </div>
                        <div class="small text-secondary mb-2">${s.type} &bull; ${s.state}</div>
                        <div class="small mb-1"><i class="bi bi-people me-1"></i> Capacity: <strong>${s.capacity}</strong></div>
                        <div class="small mb-2"><i class="bi bi-shield-check me-1 text-success"></i> ${s.hazardSafe}</div>
                        <div class="small text-muted mb-3" style="font-size: 0.72rem;">Provenance: ${s.verification}</div>
                        <button class="btn btn-sm btn-outline-success w-100" type="button" onclick="focusShelter('${s.id}')">
                            <i class="bi bi-compass me-1"></i> View on Map
                        </button>
                    </div>
                </div>
            </div>
        `).join("");
    }

    if (shelterSelect) {
        shelters.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s.id;
            opt.textContent = `${s.name} (${s.state})`;
            shelterSelect.appendChild(opt);
        });
    }

    if (routeButton && shelterSelect) {
        routeButton.addEventListener("click", () => {
            const selectedId = shelterSelect.value;
            if (selectedId) {
                focusShelter(selectedId);
            } else {
                const routeResult = document.getElementById("routeResult");
                if (routeResult) {
                    routeResult.className = "alert alert-warning mt-3 mb-0 small";
                    routeResult.textContent = "Please select a destination shelter from the dropdown list.";
                }
            }
        });
    }
}

/* =========================================================
   FIND MY LOCATION (NO NATIVE ALERTS)
========================================================= */

function setupGeolocation() {
    const locBtn = document.getElementById("locationButton");
    if (!locBtn) return;

    locBtn.addEventListener("click", function() {
        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser.");
            return;
        }

        const originalHtml = locBtn.innerHTML;
        locBtn.disabled = true;
        locBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Locating...`;

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude;
                const lng = pos.coords.longitude;
                const isWithinNER = (lat >= 21.5 && lat <= 29.5 && lng >= 89.5 && lng <= 97.5);

                if (userLocationMarker) {
                    map.removeLayer(userLocationMarker);
                }

                userLocationMarker = L.marker([lat, lng], {
                    icon: createUserDivIcon(),
                    title: "Your Location"
                }).addTo(map);

                if (isWithinNER) {
                    userLocationMarker.bindPopup(`
                        <div class="ls-compact-popup">
                            <div class="popup-tag text-info"><i class="bi bi-crosshair me-1"></i> Your Location</div>
                            <div class="small fw-semibold">Within North East India Monitoring Corridor</div>
                            <div class="small text-muted">Coordinates: ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
                        </div>
                    `).openPopup();
                    map.flyTo([lat, lng], 12, { animate: true, duration: 0.8 });
                } else {
                    userLocationMarker.bindPopup(`
                        <div class="ls-compact-popup">
                            <div class="popup-tag text-warning"><i class="bi bi-geo me-1"></i> Remote View</div>
                            <div class="small fw-semibold">Outside NER Monitoring Zone</div>
                            <div class="small text-muted">Detected at ${lat.toFixed(2)}, ${lng.toFixed(2)}. Displaying regional hub Guwahati.</div>
                        </div>
                    `).openPopup();
                    map.flyTo([26.1445, 91.7362], 10, { animate: true, duration: 0.8 });
                }

                locBtn.disabled = false;
                locBtn.innerHTML = `<i class="bi bi-crosshair me-1"></i> Locate Me`;
            },
            () => {
                locBtn.disabled = false;
                locBtn.innerHTML = originalHtml;
                alert("Location access was denied or timed out. Please check browser permissions.");
            },
            { timeout: 10000, enableHighAccuracy: true }
        );
    });
}

/* =========================================================
   NEUTRAL LAYER TOGGLE CONTROLS (NO RISK COLOR CONFUSION)
========================================================= */

function toggleLayer(layer, button) {
    const isVisible = map.hasLayer(layer);
    const checkIcon = button.querySelector(".layer-check-icon");

    if (isVisible) {
        map.removeLayer(layer);
        button.classList.remove("active");
        if (checkIcon) {
            checkIcon.className = "bi bi-square layer-check-icon";
        }
    } else {
        layer.addTo(map);
        button.classList.add("active");
        if (checkIcon) {
            checkIcon.className = "bi bi-check-square-fill layer-check-icon";
        }
    }
}

function setupToolbarListeners() {
    // 1. Monitoring Stations Toggle
    const riskToggle = document.getElementById("riskToggle");
    if (riskToggle) {
        riskToggle.addEventListener("click", function() {
            toggleLayer(riskLayer, this);
        });
    }

    // 2. Emergency Shelters Toggle
    const shelterToggle = document.getElementById("shelterToggle");
    if (shelterToggle) {
        shelterToggle.addEventListener("click", function() {
            toggleLayer(shelterLayer, this);
        });
    }

    // 3. Rescue Points Toggle
    const rescueToggle = document.getElementById("rescueToggle");
    if (rescueToggle) {
        rescueToggle.addEventListener("click", function() {
            toggleLayer(rescueLayer, this);
        });
    }

    // 4. Emergency Operations Centres Toggle
    const eocToggle = document.getElementById("eocToggle");
    if (eocToggle) {
        eocToggle.addEventListener("click", function() {
            toggleLayer(eocLayer, this);
        });
    }

    // 5. State Filter
    const stateFilterSelect = document.getElementById("stateFilterSelect");
    if (stateFilterSelect) {
        stateFilterSelect.addEventListener("change", function() {
            filterByState(this.value);
        });
    }

    // 6. Reset View Action
    const resetViewButton = document.getElementById("resetViewButton");
    if (resetViewButton) {
        resetViewButton.addEventListener("click", function() {
            if (stateFilterSelect) stateFilterSelect.value = "ALL";
            const searchInput = document.getElementById("locationSearch");
            if (searchInput) searchInput.value = "";
            const clearBtn = document.getElementById("searchClearBtn");
            if (clearBtn) clearBtn.classList.add("d-none");
            closeStationDrawer();
            filterByState("ALL");
            map.fitBounds(NER_BOUNDS, { padding: [20, 20] });
        });
    }

    // 7. Mobile Legend Toggle
    const legendToggleBtn = document.getElementById("legendToggleBtn");
    const closeLegendBtn = document.getElementById("closeLegendBtn");
    const mapLegendCard = document.getElementById("mapLegendCard");

    if (legendToggleBtn && mapLegendCard) {
        legendToggleBtn.addEventListener("click", () => {
            mapLegendCard.classList.toggle("show-mobile");
        });
    }
    if (closeLegendBtn && mapLegendCard) {
        closeLegendBtn.addEventListener("click", () => {
            mapLegendCard.classList.remove("show-mobile");
        });
    }
}

/* =========================================================
   PAGE INITIALIZATION
========================================================= */

document.addEventListener("DOMContentLoaded", function() {
    // Initial map bounding to North East India
    map.fitBounds(NER_BOUNDS, { padding: [20, 20] });

    setTimeout(() => {
        map.invalidateSize();
    }, 150);

    // Initialize all controls and modals
    setupSearch();
    setupSheltersModal();
    setupGeolocation();
    setupToolbarListeners();

    // Load asynchronous GIS stations data
    loadRiskLocations();
});