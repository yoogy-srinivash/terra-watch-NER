// =========================================
// LANDSAFE CONNECT
// MONITOR LOCATIONS - JAVASCRIPT
// =========================================

// Demo location data
let locations = [
    {
        name: "Guwahati",
        state: "Assam",
        type: "Flood",
        score: 78,
        flood: 76,
        landslide: 54,
        risk: "High"
    },
    {
        name: "Shillong",
        state: "Meghalaya",
        type: "Landslide",
        score: 72,
        flood: 42,
        landslide: 82,
        risk: "High"
    },
    {
        name: "Aizawl",
        state: "Mizoram",
        type: "Landslide",
        score: 65,
        flood: 38,
        landslide: 74,
        risk: "High"
    },
    {
        name: "Gangtok",
        state: "Sikkim",
        type: "Landslide",
        score: 55,
        flood: 35,
        landslide: 61,
        risk: "Moderate"
    },
    {
        name: "Agartala",
        state: "Tripura",
        type: "Flood",
        score: 48,
        flood: 58,
        landslide: 31,
        risk: "Moderate"
    },
    {
        name: "Kohima",
        state: "Nagaland",
        type: "Landslide",
        score: 35,
        flood: 24,
        landslide: 48,
        risk: "Moderate"
    },
    {
        name: "Itanagar",
        state: "Arunachal Pradesh",
        type: "Landslide",
        score: 28,
        flood: 22,
        landslide: 35,
        risk: "Low"
    },
    {
        name: "Imphal",
        state: "Manipur",
        type: "Flood",
        score: 25,
        flood: 28,
        landslide: 18,
        risk: "Low"
    }
];


// =========================================
// GET ELEMENT
// =========================================

function getElement(id) {
    return document.getElementById(id);
}


// =========================================
// UPDATE SUMMARY COUNTS
// =========================================

function updateSummaryCounts() {

    const total = locations.length;

    const high = locations.filter(
        location => location.risk === "High"
    ).length;

    const moderate = locations.filter(
        location => location.risk === "Moderate"
    ).length;

    const low = locations.filter(
        location => location.risk === "Low"
    ).length;


    const totalElement = getElement("totalLocations");
    const highElement = getElement("highRiskLocations");
    const moderateElement = getElement("moderateRiskLocations");
    const lowElement = getElement("lowRiskLocations");


    if (totalElement) {
        totalElement.textContent = total;
    }

    if (highElement) {
        highElement.textContent = high;
    }

    if (moderateElement) {
        moderateElement.textContent = moderate;
    }

    if (lowElement) {
        lowElement.textContent = low;
    }
}


// =========================================
// FILTER LOCATIONS
// =========================================

function filterLocations() {

    const searchInput = getElement("locationSearch");
    const stateFilter = getElement("stateFilter");
    const riskFilter = getElement("riskFilter");

    if (!searchInput || !stateFilter || !riskFilter) {
        return;
    }


    const searchValue =
        searchInput.value.trim().toLowerCase();

    const selectedState =
        stateFilter.value;

    const selectedRisk =
        riskFilter.value;


    const rows =
        document.querySelectorAll(
            "#locationsTable tr"
        );


    let visibleCount = 0;


    rows.forEach(row => {

        const location =
            row.dataset.location || "";

        const state =
            row.dataset.state || "";

        const risk =
            row.dataset.risk || "";


        const locationMatch =
            location.toLowerCase().includes(searchValue) ||
            state.toLowerCase().includes(searchValue);


        const stateMatch =
            selectedState === "all" ||
            state === selectedState;


        const riskMatch =
            selectedRisk === "all" ||
            risk === selectedRisk;


        if (
            locationMatch &&
            stateMatch &&
            riskMatch
        ) {

            row.classList.remove("d-none");

            visibleCount++;

        } else {

            row.classList.add("d-none");

        }

    });


    updateVisibleCount(visibleCount);
}


// =========================================
// UPDATE VISIBLE LOCATION COUNT
// =========================================

function updateVisibleCount(count) {

    const element =
        getElement("visibleLocationCount");

    if (!element) {
        return;
    }


    element.textContent =
        `${count} ${count === 1 ? "location" : "locations"}`;
}


// =========================================
// CLEAR FILTERS
// =========================================

function clearFilters() {

    const searchInput =
        getElement("locationSearch");

    const stateFilter =
        getElement("stateFilter");

    const riskFilter =
        getElement("riskFilter");


    if (searchInput) {
        searchInput.value = "";
    }

    if (stateFilter) {
        stateFilter.value = "all";
    }

    if (riskFilter) {
        riskFilter.value = "all";
    }


    filterLocations();
}


// =========================================
// FIND LOCATION DATA
// =========================================

function findLocation(locationName) {

    return locations.find(
        location =>
            location.name.toLowerCase() ===
            locationName.toLowerCase()
    );
}


// =========================================
// SHOW LOCATION DETAILS
// =========================================

function showLocationDetails(locationName) {

    const location =
        findLocation(locationName);


    if (!location) {
        return;
    }


    const detailsCard =
        getElement("locationDetails");


    if (!detailsCard) {
        return;
    }


    const detailLocation =
        getElement("detailLocation");

    const detailRisk =
        getElement("detailRisk");

    const detailScore =
        getElement("detailScore");

    const detailFlood =
        getElement("detailFlood");

    const detailLandslide =
        getElement("detailLandslide");

    const detailType =
        getElement("detailType");


    if (detailLocation) {
        detailLocation.textContent =
            `${location.name}, ${location.state}`;
    }


    if (detailRisk) {
        detailRisk.textContent =
            location.risk;
    }


    if (detailScore) {
        detailScore.textContent =
            `${location.score}/100`;
    }


    if (detailFlood) {
        detailFlood.textContent =
            `${location.flood}%`;
    }


    if (detailLandslide) {
        detailLandslide.textContent =
            `${location.landslide}%`;
    }


    if (detailType) {
        detailType.textContent =
            location.type;
    }


    detailsCard.classList.remove("d-none");


    // Scroll to details
    detailsCard.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// =========================================
// CLOSE LOCATION DETAILS
// =========================================

function closeLocationDetails() {

    const detailsCard =
        getElement("locationDetails");


    if (!detailsCard) {
        return;
    }


    detailsCard.classList.add("d-none");
}


// =========================================
// CREATE ALERT
// =========================================

function createLocationAlert() {

    const locationName =
        getElement("detailLocation");


    if (!locationName) {
        return;
    }


    const locationText =
        locationName.textContent;


    if (
        !locationText ||
        locationText === "--"
    ) {

        alert(
            "Please select a location first."
        );

        return;
    }


    const confirmed =
        confirm(
            `Create an alert for ${locationText}?`
        );


    if (!confirmed) {
        return;
    }


    alert(
        `Emergency alert bulletin dispatched for ${locationText}.`
    );
}


// =========================================
// FILTER EVENT LISTENERS
// =========================================

function setupFilters() {

    const searchInput =
        getElement("locationSearch");

    const stateFilter =
        getElement("stateFilter");

    const riskFilter =
        getElement("riskFilter");

    const clearButton =
        getElement("clearFilters");


    if (searchInput) {

        searchInput.addEventListener(
            "input",
            filterLocations
        );

    }


    if (stateFilter) {

        stateFilter.addEventListener(
            "change",
            filterLocations
        );

    }


    if (riskFilter) {

        riskFilter.addEventListener(
            "change",
            filterLocations
        );

    }


    if (clearButton) {

        clearButton.addEventListener(
            "click",
            clearFilters
        );

    }
}


// =========================================
// VIEW BUTTONS
// =========================================

function setupViewButtons() {

    const buttons =
        document.querySelectorAll(
            ".view-location"
        );


    buttons.forEach(button => {

        button.addEventListener(
            "click",
            function () {

                const locationName =
                    this.dataset.location;

                showLocationDetails(
                    locationName
                );

            }
        );

    });
}


// =========================================
// CLOSE BUTTON
// =========================================

function setupCloseButton() {

    const button =
        getElement("closeDetails");


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        closeLocationDetails
    );
}


// =========================================
// CREATE ALERT BUTTON
// =========================================

function setupAlertButton() {

    const button =
        getElement("createAlertButton");


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        createLocationAlert
    );
}


// =========================================
// LAST UPDATED
// =========================================

function updateLastUpdated() {

    const element =
        getElement("lastUpdated");


    if (!element) {
        return;
    }


    const now = new Date();


    element.textContent =
        now.toLocaleString(
            "en-IN",
            {
                dateStyle: "medium",
                timeStyle: "short"
            }
        );
}


// =========================================
// INITIALIZE PAGE
// =========================================

async function initializeMonitorLocations() {
    if (window.LandSafeAPI) {
        try {
            const apiLocs = await window.LandSafeAPI.getMonitorLocations();
            if (apiLocs && apiLocs.length > 0) {
                locations = apiLocs;
            }
        } catch (e) {
            console.warn("[MonitorLocations] Using fallback static locations:", e.message);
        }
    }

    updateSummaryCounts();

    setupFilters();

    setupViewButtons();

    setupCloseButton();

    setupAlertButton();

    updateLastUpdated();

    updateVisibleCount(
        locations.length
    );
}


// =========================================
// PAGE LOAD
// =========================================

document.addEventListener(
    "DOMContentLoaded",
    initializeMonitorLocations
);