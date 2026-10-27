// =========================================
// LANDSAFE CONNECT
// ANALYSE REPORTS - JAVASCRIPT
// =========================================

// Demo report data
let reports = [
    {
        id: "LS-1042",
        location: "Guwahati, Assam",
        type: "Flood",
        severity: "High",
        status: "Pending",
        description: "Water level has increased near the residential area."
    },
    {
        id: "LS-1041",
        location: "Shillong, Meghalaya",
        type: "Landslide",
        severity: "High",
        status: "Verified",
        description: "Large cracks observed on the hillside near the road."
    },
    {
        id: "LS-1040",
        location: "Aizawl, Mizoram",
        type: "Road Blockage",
        severity: "Medium",
        status: "Pending",
        description: "Road partially blocked because of fallen soil and rocks."
    },
    {
        id: "LS-1039",
        location: "Gangtok, Sikkim",
        type: "Drainage",
        severity: "Low",
        status: "Reviewed",
        description: "Drainage blockage reported near the local market."
    }
];


// =========================================
// GET ELEMENT
// =========================================

function getElement(id) {
    return document.getElementById(id);
}


// =========================================
// FILTER REPORTS
// =========================================

function filterReports() {

    const typeFilter = getElement("reportType");
    const severityFilter = getElement("reportSeverity");
    const statusFilter = getElement("reportStatus");

    if (!typeFilter || !severityFilter || !statusFilter) {
        return;
    }

    const selectedType = typeFilter.value;
    const selectedSeverity = severityFilter.value;
    const selectedStatus = statusFilter.value;

    const rows = document.querySelectorAll("#reportsTable tbody tr");

    rows.forEach((row) => {

        const type = row.dataset.type;
        const severity = row.dataset.severity;
        const status = row.dataset.status;

        const typeMatch =
            selectedType === "all" || type === selectedType;

        const severityMatch =
            selectedSeverity === "all" || severity === selectedSeverity;

        const statusMatch =
            selectedStatus === "all" || status === selectedStatus;

        if (typeMatch && severityMatch && statusMatch) {
            row.classList.remove("d-none");
        } else {
            row.classList.add("d-none");
        }
    });
}


// =========================================
// REPORT DETAILS
// =========================================

function showReportDetails(reportId) {

    const report = reports.find(
        item => item.id === reportId
    );

    if (!report) {
        return;
    }

    const message =
        `Report ID: ${report.id}\n\n` +
        `Location: ${report.location}\n` +
        `Type: ${report.type}\n` +
        `Severity: ${report.severity}\n` +
        `Status: ${report.status}\n\n` +
        `Description:\n${report.description}`;

    alert(message);
}


// =========================================
// UPDATE REPORT STATUS
// =========================================

function updateReportStatus(reportId, newStatus) {

    const report = reports.find(
        item => item.id === reportId
    );

    if (!report) {
        return;
    }

    report.status = newStatus;

    alert(
        `${reportId} has been marked as ${newStatus}.`
    );

    updateSummaryCards();
}


// =========================================
// UPDATE SUMMARY CARDS
// =========================================

function updateSummaryCards() {

    const totalReports = reports.length;

    const pendingReports = reports.filter(
        report => report.status === "Pending"
    ).length;

    const highSeverityReports = reports.filter(
        report => report.severity === "High"
    ).length;

    const verifiedReports = reports.filter(
        report => report.status === "Verified"
    ).length;

    const totalElement = getElement("totalReports");
    const pendingElement = getElement("pendingReports");
    const highElement = getElement("highReports");
    const verifiedElement = getElement("verifiedReports");

    if (totalElement) {
        totalElement.textContent = totalReports;
    }

    if (pendingElement) {
        pendingElement.textContent = pendingReports;
    }

    if (highElement) {
        highElement.textContent = highSeverityReports;
    }

    if (verifiedElement) {
        verifiedElement.textContent = verifiedReports;
    }
}


// =========================================
// FILTER EVENTS
// =========================================

function setupFilters() {

    const filters = [
        "reportType",
        "reportSeverity",
        "reportStatus"
    ];

    filters.forEach(id => {

        const element = getElement(id);

        if (element) {
            element.addEventListener(
                "change",
                filterReports
            );
        }
    });
}


// =========================================
// REPORT BUTTON EVENTS
// =========================================

function setupReportActions() {

    const detailButtons =
        document.querySelectorAll("[data-report-id]");

    detailButtons.forEach(button => {

        button.addEventListener("click", function () {

            const reportId =
                this.dataset.reportId;

            showReportDetails(reportId);

        });

    });
}


// =========================================
// INITIALIZE PAGE
// =========================================

async function initializeAnalyseReports() {
    if (window.LandSafeAPI) {
        try {
            const apiReports = await window.LandSafeAPI.getReports();
            if (apiReports && apiReports.length > 0) {
                reports = apiReports.map(r => ({
                    id: r.id,
                    location: `${r.location_name}, ${r.state}`,
                    type: r.issue_type.charAt(0).toUpperCase() + r.issue_type.slice(1),
                    severity: r.severity.charAt(0).toUpperCase() + r.severity.slice(1),
                    status: r.status,
                    description: r.description
                }));
            }
        } catch (e) {
            console.warn("[AnalyzeReports] Using fallback static reports:", e.message);
        }
    }

    setupFilters();

    setupReportActions();

    updateSummaryCards();

}


// =========================================
// PAGE LOAD
// =========================================

document.addEventListener(
    "DOMContentLoaded",
    initializeAnalyseReports
);