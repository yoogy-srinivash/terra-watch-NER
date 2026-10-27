/* =========================================================
   LANDSAFE CONNECT
   ADMIN LIVE RISK MAP
   Demo Frontend Data
========================================================= */


/* =========================================================
   DEMO LOCATION DATA
========================================================= */

let riskLocations = [

    {
        id: "LOC-001",
        city: "Guwahati",
        state: "Assam",
        lat: 26.1445,
        lng: 91.7362,
        hazard: "Flood",
        score: 78,
        flood: 76,
        landslide: 54,
        risk: "High",
        status: "Active monitoring"
    },

    {
        id: "LOC-002",
        city: "Shillong",
        state: "Meghalaya",
        lat: 25.5788,
        lng: 91.8933,
        hazard: "Landslide",
        score: 72,
        flood: 42,
        landslide: 82,
        risk: "High",
        status: "High-risk monitoring"
    },

    {
        id: "LOC-003",
        city: "Aizawl",
        state: "Mizoram",
        lat: 23.7271,
        lng: 92.7176,
        hazard: "Landslide",
        score: 65,
        flood: 38,
        landslide: 74,
        risk: "High",
        status: "High-risk monitoring"
    },

    {
        id: "LOC-004",
        city: "Gangtok",
        state: "Sikkim",
        lat: 27.3389,
        lng: 88.6065,
        hazard: "Landslide",
        score: 55,
        flood: 35,
        landslide: 61,
        risk: "Moderate",
        status: "Moderate monitoring"
    },

    {
        id: "LOC-005",
        city: "Agartala",
        state: "Tripura",
        lat: 23.8315,
        lng: 91.2868,
        hazard: "Flood",
        score: 48,
        flood: 58,
        landslide: 31,
        risk: "Moderate",
        status: "Moderate monitoring"
    },

    {
        id: "LOC-006",
        city: "Kohima",
        state: "Nagaland",
        lat: 25.6751,
        lng: 94.1086,
        hazard: "Landslide",
        score: 35,
        flood: 24,
        landslide: 48,
        risk: "Moderate",
        status: "Moderate monitoring"
    },

    {
        id: "LOC-007",
        city: "Itanagar",
        state: "Arunachal Pradesh",
        lat: 27.0844,
        lng: 93.6053,
        hazard: "Landslide",
        score: 28,
        flood: 22,
        landslide: 35,
        risk: "Low",
        status: "Normal monitoring"
    },

    {
        id: "LOC-008",
        city: "Imphal",
        state: "Manipur",
        lat: 24.8170,
        lng: 93.9368,
        hazard: "Flood",
        score: 25,
        flood: 28,
        landslide: 18,
        risk: "Low",
        status: "Normal monitoring"
    }

];


/* =========================================================
   DEMO SHELTERS
========================================================= */

const shelters = [

    {
        id: "SH-001",
        name: "Guwahati Relief Shelter",
        city: "Guwahati",
        lat: 26.1550,
        lng: 91.7500
    },

    {
        id: "SH-002",
        name: "Shillong Higher Ground Shelter",
        city: "Shillong",
        lat: 25.5900,
        lng: 91.8800
    },

    {
        id: "SH-003",
        name: "Aizawl Community Relief Centre",
        city: "Aizawl",
        lat: 23.7350,
        lng: 92.7300
    },

    {
        id: "SH-004",
        name: "Agartala Emergency Shelter",
        city: "Agartala",
        lat: 23.8400,
        lng: 91.3000
    }

];


/* =========================================================
   DEMO ALERTS
========================================================= */

const activeAlerts = [

    {
        id: "AL-2001",
        city: "Guwahati",
        hazard: "Flood",
        severity: "Critical",
        lat: 26.1445,
        lng: 91.7362
    },

    {
        id: "AL-2002",
        city: "Shillong",
        hazard: "Landslide",
        severity: "High",
        lat: 25.5788,
        lng: 91.8933
    },

    {
        id: "AL-2003",
        city: "Aizawl",
        hazard: "Landslide",
        severity: "High",
        lat: 23.7271,
        lng: 92.7176
    },

    {
        id: "AL-2004",
        city: "Agartala",
        hazard: "Flood",
        severity: "Medium",
        lat: 23.8315,
        lng: 91.2868
    }

];


/* =========================================================
   GLOBAL VARIABLES
========================================================= */

let adminMap;

let riskLayerGroup;
let shelterLayerGroup;
let alertLayerGroup;

let selectedLocation = null;


/* =========================================================
   DOM HELPER
========================================================= */

function getElement(id) {
    return document.getElementById(id);
}


/* =========================================================
   RISK COLORS
========================================================= */

function getRiskColor(risk) {

    if (risk === "High") {
        return "#dc3545";
    }

    if (risk === "Moderate") {
        return "#ffc107";
    }

    return "#198754";
}


/* =========================================================
   INITIALIZE MAP
========================================================= */

function initializeMap() {

    adminMap = L.map("adminRiskMap").setView(
        [25.8, 92.5],
        6
    );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 18,
            attribution:
                "&copy; OpenStreetMap contributors"
        }
    ).addTo(adminMap);


    riskLayerGroup = L.layerGroup().addTo(adminMap);

    shelterLayerGroup = L.layerGroup().addTo(adminMap);

    alertLayerGroup = L.layerGroup().addTo(adminMap);


    addRiskLocations();

    addShelters();

    addAlerts();


    setTimeout(function () {
        adminMap.invalidateSize();
    }, 300);

}


/* =========================================================
   ADD RISK LOCATIONS
========================================================= */

function addRiskLocations() {

    riskLayerGroup.clearLayers();

    riskLocations.forEach(function (location) {

        const marker = L.circleMarker(
            [location.lat, location.lng],
            {
                radius: 10,
                fillColor: getRiskColor(location.risk),
                color: "#ffffff",
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }
        );


        marker.bindPopup(`

            <div>

                <strong>${location.city}, ${location.state}</strong>

                <hr class="my-2">

                <div>
                    Hazard:
                    <strong>${location.hazard}</strong>
                </div>

                <div>
                    Risk Score:
                    <strong>${location.score}/100</strong>
                </div>

                <div>
                    Risk Level:
                    <strong>${location.risk}</strong>
                </div>

                <button
                    class="btn btn-sm btn-success mt-2"
                    onclick="showLocationDetails('${location.id}')">

                    View Details

                </button>

            </div>

        `);


        marker.on("click", function () {
            showLocationDetails(location.id);
        });


        riskLayerGroup.addLayer(marker);

    });

}


/* =========================================================
   ADD SHELTERS
========================================================= */

function addShelters() {

    shelterLayerGroup.clearLayers();


    shelters.forEach(function (shelter) {

        const marker = L.marker(
            [shelter.lat, shelter.lng]
        );


        marker.bindPopup(`

            <div>

                <strong>
                    <i class="bi bi-house-heart"></i>
                    ${shelter.name}
                </strong>

                <hr class="my-2">

                <div>
                    Location:
                    ${shelter.city}
                </div>

                <div class="text-success mt-1">
                    Available for emergency response
                </div>

            </div>

        `);


        shelterLayerGroup.addLayer(marker);

    });

}


/* =========================================================
   ADD ACTIVE ALERTS
========================================================= */

function addAlerts() {

    alertLayerGroup.clearLayers();


    activeAlerts.forEach(function (alertItem) {

        const marker = L.marker(
            [alertItem.lat, alertItem.lng]
        );


        marker.bindPopup(`

            <div>

                <strong>
                    <i class="bi bi-bell-fill"></i>
                    Active Alert
                </strong>

                <hr class="my-2">

                <div>
                    Alert ID:
                    <strong>${alertItem.id}</strong>
                </div>

                <div>
                    Location:
                    <strong>${alertItem.city}</strong>
                </div>

                <div>
                    Hazard:
                    <strong>${alertItem.hazard}</strong>
                </div>

                <div>
                    Severity:
                    <strong>${alertItem.severity}</strong>
                </div>

            </div>

        `);


        alertLayerGroup.addLayer(marker);

    });

}


/* =========================================================
   SUMMARY COUNTS
========================================================= */

function updateSummary() {

    const locationCount =
        getElement("locationCount");

    const highRiskCount =
        getElement("highRiskCount");

    const activeAlertCount =
        getElement("activeAlertCount");

    const shelterCount =
        getElement("shelterCount");


    if (locationCount) {
        locationCount.textContent =
            riskLocations.length;
    }


    if (highRiskCount) {

        highRiskCount.textContent =
            riskLocations.filter(
                location => location.risk === "High"
            ).length;

    }


    if (activeAlertCount) {

        activeAlertCount.textContent =
            activeAlerts.length;

    }


    if (shelterCount) {

        shelterCount.textContent =
            shelters.length;

    }

}


/* =========================================================
   SHOW LOCATION DETAILS
========================================================= */

function showLocationDetails(locationId) {

    const location =
        riskLocations.find(
            item => item.id === locationId
        );


    if (!location) {
        return;
    }


    selectedLocation = location;


    const detailsCard =
        getElement("locationDetails");


    detailsCard.classList.remove("d-none");


    getElement("selectedLocationName")
        .textContent =
        location.city;


    getElement("selectedLocationState")
        .textContent =
        `${location.state} • ${location.hazard}`;


    const riskBadge =
        getElement("selectedRiskBadge");


    riskBadge.textContent =
        `${location.risk} Risk`;


    riskBadge.className =
        "badge";


    if (location.risk === "High") {
        riskBadge.classList.add("text-bg-danger");
    }
    else if (location.risk === "Moderate") {
        riskBadge.classList.add("text-bg-warning");
    }
    else {
        riskBadge.classList.add("text-bg-success");
    }


    getElement("selectedRiskScore")
        .textContent =
        `${location.score}/100`;


    getElement("selectedHazard")
        .textContent =
        location.hazard;


    updateProgress(
        "selectedFloodProgress",
        "selectedFloodText",
        location.flood
    );


    updateProgress(
        "selectedLandslideProgress",
        "selectedLandslideText",
        location.landslide
    );


    getElement("selectedStatus")
        .textContent =
        location.status;


    const viewAlertsBtn =
        getElement("viewAlertsBtn");


    if (viewAlertsBtn) {
        viewAlertsBtn.dataset.city =
            location.city;
    }


    const openReportsBtn =
        getElement("openReportsBtn");


    if (openReportsBtn) {
        openReportsBtn.dataset.city =
            location.city;
    }


    const createAlertBtn =
        getElement("createAlertBtn");


    if (createAlertBtn) {
        createAlertBtn.dataset.city =
            location.city;
    }

}


/* =========================================================
   PROGRESS BAR
========================================================= */

function updateProgress(
    progressId,
    textId,
    value
) {

    const progress =
        getElement(progressId);

    const text =
        getElement(textId);


    if (progress) {

        progress.style.width =
            `${value}%`;

        progress.setAttribute(
            "aria-valuenow",
            value
        );

    }


    if (text) {

        text.textContent =
            `${value}%`;

    }

}


/* =========================================================
   CLOSE DETAILS
========================================================= */

function closeLocationDetails() {

    const detailsCard =
        getElement("locationDetails");


    if (detailsCard) {
        detailsCard.classList.add("d-none");
    }


    selectedLocation = null;

}


/* =========================================================
   POPULATE LOCATION TABLE
========================================================= */

function renderLocationTable(
    filteredLocations = riskLocations
) {

    const table =
        getElement("locationsTable");


    if (!table) {
        return;
    }


    table.innerHTML = "";


    if (filteredLocations.length === 0) {

        table.innerHTML = `

            <tr>

                <td colspan="6"
                    class="text-center text-secondary py-4">

                    No locations found.

                </td>

            </tr>

        `;

        return;

    }


    filteredLocations.forEach(function (location) {

        let badgeClass =
            "text-bg-success";


        if (location.risk === "High") {
            badgeClass = "text-bg-danger";
        }
        else if (location.risk === "Moderate") {
            badgeClass = "text-bg-warning";
        }


        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                <strong>${location.city}</strong>
            </td>

            <td>
                ${location.state}
            </td>

            <td>
                ${location.hazard}
            </td>

            <td>
                <strong>
                    ${location.score}/100
                </strong>
            </td>

            <td>
                <span class="badge ${badgeClass}">
                    ${location.risk}
                </span>
            </td>

            <td>

                <button
                    class="btn btn-sm btn-outline-success"
                    data-location-id="${location.id}">

                    View

                </button>

            </td>

        `;


        const button =
            row.querySelector("button");


        button.addEventListener(
            "click",
            function () {

                showLocationDetails(
                    location.id
                );


                adminMap.setView(
                    [location.lat, location.lng],
                    9
                );

            }
        );


        table.appendChild(row);

    });

}


/* =========================================================
   FILTER LOCATIONS
========================================================= */

function filterLocations() {

    const searchInput =
        getElement("locationSearch");


    const riskFilter =
        getElement("riskFilter");


    const search =
        searchInput
            ? searchInput.value
                .trim()
                .toLowerCase()
            : "";


    const selectedRisk =
        riskFilter
            ? riskFilter.value
            : "all";


    const filtered =
        riskLocations.filter(
            function (location) {

                const matchesSearch =
                    location.city
                        .toLowerCase()
                        .includes(search) ||

                    location.state
                        .toLowerCase()
                        .includes(search);


                const matchesRisk =
                    selectedRisk === "all" ||
                    location.risk === selectedRisk;


                return (
                    matchesSearch &&
                    matchesRisk
                );

            }
        );


    renderLocationTable(filtered);

}


/* =========================================================
   SEARCH LOCATION ON MAP
========================================================= */

function searchLocation() {

    const searchInput =
        getElement("locationSearch");


    if (!searchInput) {
        return;
    }


    const search =
        searchInput.value
            .trim()
            .toLowerCase();


    if (!search) {

        window.alert(
            "Please enter a location to search."
        );

        return;

    }


    const location =
        riskLocations.find(
            function (item) {

                return (
                    item.city
                        .toLowerCase()
                        .includes(search) ||

                    item.state
                        .toLowerCase()
                        .includes(search)
                );

            }
        );


    if (!location) {

        window.alert(
            "Location not found. Try Guwahati, Shillong, Aizawl or another monitored station."
        );

        return;

    }


    adminMap.setView(
        [location.lat, location.lng],
        10
    );


    showLocationDetails(
        location.id
    );

}


/* =========================================================
   FIT NORTH-EAST REGION
========================================================= */

function fitNorthEastRegion() {

    const bounds =
        L.latLngBounds(
            riskLocations.map(
                location =>
                    [location.lat, location.lng]
            )
        );


    adminMap.fitBounds(
        bounds,
        {
            padding: [30, 30]
        }
    );

}


/* =========================================================
   LAYER TOGGLES
========================================================= */

function toggleLayer(
    checkboxId,
    layerGroup
) {

    const checkbox =
        getElement(checkboxId);


    if (!checkbox) {
        return;
    }


    checkbox.addEventListener(
        "change",
        function () {

            if (checkbox.checked) {

                layerGroup.addTo(
                    adminMap
                );

            }
            else {

                adminMap.removeLayer(
                    layerGroup
                );

            }

        }
    );

}


/* =========================================================
   VIEW ALERTS
========================================================= */

function viewSelectedLocationAlerts() {

    if (!selectedLocation) {
        return;
    }


    window.alert(
        `Active alerts for ${selectedLocation.city}.\n\nOperational alerts are currently monitored on the Admin Live Risk Map.`
    );

}


/* =========================================================
   OPEN REPORTS
========================================================= */

function openSelectedLocationReports() {

    if (!selectedLocation) {
        return;
    }


    window.location.href =
        `report-issue.html?location=${encodeURIComponent(
            selectedLocation.city
        )}`;

}


/* =========================================================
   CREATE ALERT
========================================================= */

function createLocationAlert() {

    if (!selectedLocation) {
        return;
    }


    const confirmed =
        window.confirm(
            `Issue an official emergency alert for ${selectedLocation.city}?`
        );


    if (!confirmed) {
        return;
    }


    window.alert(
        `Emergency alert bulletin issued for ${selectedLocation.city}.`
    );

}


/* =========================================================
   EVENT LISTENERS
========================================================= */

function setupEventListeners() {

    const searchBtn =
        getElement("searchBtn");


    if (searchBtn) {

        searchBtn.addEventListener(
            "click",
            searchLocation
        );

    }


    const searchInput =
        getElement("locationSearch");


    if (searchInput) {

        searchInput.addEventListener(
            "input",
            filterLocations
        );


        searchInput.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {
                    searchLocation();
                }

            }
        );

    }


    const riskFilter =
        getElement("riskFilter");


    if (riskFilter) {

        riskFilter.addEventListener(
            "change",
            filterLocations
        );

    }


    const fitMapBtn =
        getElement("fitMapBtn");


    if (fitMapBtn) {

        fitMapBtn.addEventListener(
            "click",
            fitNorthEastRegion
        );

    }


    const closeDetailsBtn =
        getElement("closeDetailsBtn");


    if (closeDetailsBtn) {

        closeDetailsBtn.addEventListener(
            "click",
            closeLocationDetails
        );

    }


    const viewAlertsBtn =
        getElement("viewAlertsBtn");


    if (viewAlertsBtn) {

        viewAlertsBtn.addEventListener(
            "click",
            viewSelectedLocationAlerts
        );

    }


    const openReportsBtn =
        getElement("openReportsBtn");


    if (openReportsBtn) {

        openReportsBtn.addEventListener(
            "click",
            openSelectedLocationReports
        );

    }


    const createAlertBtn =
        getElement("createAlertBtn");


    if (createAlertBtn) {

        createAlertBtn.addEventListener(
            "click",
            createLocationAlert
        );

    }


    toggleLayer(
        "riskZonesToggle",
        riskLayerGroup
    );


    toggleLayer(
        "sheltersToggle",
        shelterLayerGroup
    );


    toggleLayer(
        "alertsToggle",
        alertLayerGroup
    );

}


/* =========================================================
   INITIALIZE PAGE
========================================================= */

async function initializeAdminLiveMap() {
    if (window.LandSafeAPI) {
        try {
            const geojson = await window.LandSafeAPI.getLocationsGeoJSON();
            if (geojson && geojson.features && geojson.features.length > 0) {
                riskLocations = geojson.features.map((f, i) => ({
                    id: f.properties.id || `LOC-${i + 1}`,
                    city: f.properties.name,
                    state: f.properties.state,
                    lat: f.geometry.coordinates[1],
                    lng: f.geometry.coordinates[0],
                    hazard: f.properties.primary_hazard || "Landslide",
                    score: Math.round(f.properties.risk_score || 65),
                    flood: Math.round(f.properties.flood_risk_pct || 45),
                    landslide: Math.round(f.properties.landslide_risk_pct || 65),
                    risk: f.properties.risk_level ? (f.properties.risk_level.charAt(0).toUpperCase() + f.properties.risk_level.slice(1).toLowerCase()) : "High",
                    status: `${f.properties.risk_level || "Active"} monitoring`
                }));
            }
        } catch (e) {
            console.warn("[AdminLiveMap] Using fallback static locations:", e.message);
        }
    }

    initializeMap();

    updateSummary();

    renderLocationTable();

    setupEventListeners();

}


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initializeAdminLiveMap
);