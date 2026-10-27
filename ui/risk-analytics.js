/* =========================================================
   LANDSAFE CONNECT
   RISK ANALYTICS - ADMIN
   Demo Frontend Functionality
========================================================= */


/* =========================================================
   DEMO LOCATION DATA
========================================================= */

let analyticsLocations = [

    {
        location: "Guwahati",
        state: "Assam",
        flood: 76,
        landslide: 54,
        overall: 78,
        level: "High",
        hazard: "Flood"
    },

    {
        location: "Shillong",
        state: "Meghalaya",
        flood: 42,
        landslide: 82,
        overall: 72,
        level: "High",
        hazard: "Landslide"
    },

    {
        location: "Aizawl",
        state: "Mizoram",
        flood: 38,
        landslide: 74,
        overall: 65,
        level: "High",
        hazard: "Landslide"
    },

    {
        location: "Gangtok",
        state: "Sikkim",
        flood: 35,
        landslide: 61,
        overall: 55,
        level: "Moderate",
        hazard: "Landslide"
    },

    {
        location: "Agartala",
        state: "Tripura",
        flood: 58,
        landslide: 31,
        overall: 48,
        level: "Moderate",
        hazard: "Flood"
    },

    {
        location: "Kohima",
        state: "Nagaland",
        flood: 24,
        landslide: 48,
        overall: 35,
        level: "Moderate",
        hazard: "Landslide"
    },

    {
        location: "Itanagar",
        state: "Arunachal Pradesh",
        flood: 22,
        landslide: 35,
        overall: 28,
        level: "Low",
        hazard: "Landslide"
    },

    {
        location: "Imphal",
        state: "Manipur",
        flood: 28,
        landslide: 18,
        overall: 25,
        level: "Low",
        hazard: "Flood"
    }

];


/* =========================================================
   DEMO RISK TREND
========================================================= */

const riskTrend = {

    labels: [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun"
    ],

    values: [
        42,
        47,
        51,
        56,
        63,
        70,
        78
    ]

};


/* =========================================================
   RISK FACTORS
========================================================= */

const riskFactors = {

    rainfall: 72,

    soil: 84,

    slope: 61,

    water: 55

};


/* =========================================================
   DOM HELPER
========================================================= */

function getElement(id) {

    return document.getElementById(id);

}


/* =========================================================
   RISK LEVEL BADGE
========================================================= */

function getRiskBadge(level) {

    if (level === "High") {

        return "text-bg-danger";

    }

    if (level === "Moderate") {

        return "text-bg-warning";

    }

    return "text-bg-success";

}


/* =========================================================
   UPDATE SUMMARY
========================================================= */

function updateSummary() {

    const locations =
        analyticsLocations.length;


    const totalRisk =
        analyticsLocations.reduce(
            function (sum, location) {

                return sum + location.overall;

            },
            0
        );


    const average =
        Math.round(
            totalRisk / locations
        );


    const highRisk =
        analyticsLocations.filter(
            location =>
                location.level === "High"
        ).length;


    getElement("locationsAnalysed")
        .textContent =
        locations;


    getElement("averageRisk")
        .textContent =
        average;


    getElement("highRiskLocations")
        .textContent =
        highRisk;


    getElement("activeAlerts")
        .textContent =
        "4";

}


/* =========================================================
   UPDATE RISK FACTORS
========================================================= */

function updateRiskFactors() {

    getElement("rainfallValue")
        .textContent =
        `${riskFactors.rainfall}%`;


    getElement("soilValue")
        .textContent =
        `${riskFactors.soil}%`;


    getElement("slopeValue")
        .textContent =
        `${riskFactors.slope}%`;


    getElement("waterValue")
        .textContent =
        `${riskFactors.water}%`;


    getElement("rainfallProgress")
        .style.width =
        `${riskFactors.rainfall}%`;


    getElement("soilProgress")
        .style.width =
        `${riskFactors.soil}%`;


    getElement("slopeProgress")
        .style.width =
        `${riskFactors.slope}%`;


    getElement("waterProgress")
        .style.width =
        `${riskFactors.water}%`;

}


/* =========================================================
   RENDER TOP LOCATIONS
========================================================= */

function renderTopLocations() {

    const table =
        getElement("topLocationsTable");


    table.innerHTML = "";


    const sortedLocations =
        [...analyticsLocations]
            .sort(
                (a, b) =>
                    b.overall - a.overall
            )
            .slice(0, 5);


    sortedLocations.forEach(
        function (location) {

            const row =
                document.createElement("tr");


            row.innerHTML = `

                <td>
                    <strong>
                        ${location.location}
                    </strong>
                </td>

                <td>
                    ${location.state}
                </td>

                <td>
                    <strong>
                        ${location.overall}/100
                    </strong>
                </td>

                <td>
                    ${location.hazard}
                </td>

                <td>

                    <span class="badge
                        ${getRiskBadge(location.level)}">

                        ${location.level}

                    </span>

                </td>

            `;


            table.appendChild(row);

        }
    );

}


/* =========================================================
   RENDER LOCATION ANALYTICS
========================================================= */

function renderLocationAnalytics() {

    const table =
        getElement("locationAnalyticsTable");


    table.innerHTML = "";


    analyticsLocations.forEach(
        function (location) {

            const row =
                document.createElement("tr");


            row.innerHTML = `

                <td>

                    <strong>
                        ${location.location}
                    </strong>

                    <small class="d-block text-secondary">
                        ${location.state}
                    </small>

                </td>


                <td>
                    ${location.flood}%
                </td>


                <td>
                    ${location.landslide}%
                </td>


                <td>

                    <strong>
                        ${location.overall}/100
                    </strong>

                </td>


                <td>

                    <span class="badge
                        ${getRiskBadge(location.level)}">

                        ${location.level}

                    </span>

                </td>

            `;


            table.appendChild(row);

        }
    );

}


/* =========================================================
   CREATE RISK TREND CHART
========================================================= */

function createRiskTrendChart() {

    const canvas =
        getElement("riskTrendChart");


    if (!canvas) {
        return;
    }


    new Chart(
        canvas,
        {

            type: "line",

            data: {

                labels:
                    riskTrend.labels,

                datasets: [

                    {
                        label: "Risk Score",

                        data:
                            riskTrend.values,

                        tension: 0.35,

                        fill: false,

                        borderWidth: 2,

                        pointRadius: 3

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: true,

                aspectRatio: 2.4,

                scales: {

                    y: {

                        min: 0,

                        max: 100,

                        ticks: {

                            callback:
                                function (value) {

                                    return value + "%";

                                }

                        }

                    }

                },

                plugins: {

                    legend: {

                        display: true

                    },

                    tooltip: {

                        callbacks: {

                            label:
                                function (context) {

                                    return
                                        `Risk Score: ${context.parsed.y}%`;

                                }

                        }

                    }

                }

            }

        }
    );

}


/* =========================================================
   CREATE HAZARD CHART
========================================================= */

function createHazardChart() {

    const canvas =
        getElement("hazardChart");


    if (!canvas) {
        return;
    }


    const averageFlood =
        Math.round(
            analyticsLocations.reduce(
                (sum, location) =>
                    sum + location.flood,
                0
            ) /
            analyticsLocations.length
        );


    const averageLandslide =
        Math.round(
            analyticsLocations.reduce(
                (sum, location) =>
                    sum + location.landslide,
                0
            ) /
            analyticsLocations.length
        );


    new Chart(
        canvas,
        {

            type: "bar",

            data: {

                labels: [
                    "Flood",
                    "Landslide"
                ],

                datasets: [

                    {
                        label: "Average Risk",

                        data: [
                            averageFlood,
                            averageLandslide
                        ],

                        borderWidth: 1

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: true,

                aspectRatio: 1.5,

                scales: {

                    y: {

                        min: 0,

                        max: 100,

                        ticks: {

                            callback:
                                function (value) {

                                    return value + "%";

                                }

                        }

                    }

                }

            }

        }
    );

}


/* =========================================================
   CREATE RISK DISTRIBUTION CHART
========================================================= */

function createRiskDistributionChart() {

    const canvas =
        getElement("riskDistributionChart");


    if (!canvas) {
        return;
    }


    const high =
        analyticsLocations.filter(
            location =>
                location.level === "High"
        ).length;


    const moderate =
        analyticsLocations.filter(
            location =>
                location.level === "Moderate"
        ).length;


    const low =
        analyticsLocations.filter(
            location =>
                location.level === "Low"
        ).length;


    new Chart(
        canvas,
        {

            type: "doughnut",

            data: {

                labels: [
                    "High",
                    "Moderate",
                    "Low"
                ],

                datasets: [

                    {
                        data: [
                            high,
                            moderate,
                            low
                        ],

                        borderWidth: 1

                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: true,

                aspectRatio: 1.4,

                plugins: {

                    legend: {

                        position: "bottom"

                    }

                }

            }

        }

    );

}


/* =========================================================
   INITIALIZE PAGE
========================================================= */

async function initializeRiskAnalytics() {
    if (window.LandSafeAPI) {
        try {
            const apiLocs = await window.LandSafeAPI.getAnalyticsLocations();
            if (apiLocs && apiLocs.length > 0) {
                analyticsLocations = apiLocs;
            }
        } catch (e) {
            console.warn("[RiskAnalytics] Using fallback static analytics locations:", e.message);
        }
    }

    updateSummary();

    updateRiskFactors();

    renderTopLocations();

    renderLocationAnalytics();

    createRiskTrendChart();

    createHazardChart();

    createRiskDistributionChart();

}


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initializeRiskAnalytics
);