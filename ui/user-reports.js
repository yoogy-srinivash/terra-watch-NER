/* =========================================================
   LANDSAFE CONNECT
   USER REPORTS - ADMIN
   Demo Frontend Functionality
========================================================= */


/* =========================================================
   DEMO REPORT DATA
========================================================= */

let reports = [

    {
        id: "LS-1048",
        user: "Rahul Sharma",
        location: "Guwahati, Assam",
        type: "Flood",
        severity: "Critical",
        status: "Pending",
        submitted: "Today, 10:42 AM",
        description:
            "Water level has increased near the residential area and several roads are becoming difficult to use.",
        coordinates:
            "26.1445, 91.7362",
        evidence:
            "Photo uploaded by user"
    },

    {
        id: "LS-1047",
        user: "Ananya Das",
        location: "Shillong, Meghalaya",
        type: "Landslide",
        severity: "High",
        status: "Verified",
        submitted: "Today, 09:35 AM",
        description:
            "Cracks and loose soil were observed near the hillside road.",
        coordinates:
            "25.5788, 91.8933",
        evidence:
            "2 photos uploaded"
    },

    {
        id: "LS-1046",
        user: "Mizoram Citizen",
        location: "Aizawl, Mizoram",
        type: "Landslide",
        severity: "High",
        status: "Pending",
        submitted: "Today, 08:50 AM",
        description:
            "Rock and soil movement has been observed near a local road.",
        coordinates:
            "23.7271, 92.7176",
        evidence:
            "Photo uploaded by user"
    },

    {
        id: "LS-1045",
        user: "Priya Singh",
        location: "Gangtok, Sikkim",
        type: "Road Blockage",
        severity: "Medium",
        status: "Verified",
        submitted: "Yesterday, 06:20 PM",
        description:
            "Mud and debris have partially blocked the road after heavy rainfall.",
        coordinates:
            "27.3389, 88.6065",
        evidence:
            "Photo uploaded by user"
    },

    {
        id: "LS-1044",
        user: "Arun Kumar",
        location: "Agartala, Tripura",
        type: "Flood",
        severity: "Medium",
        status: "Pending",
        submitted: "Yesterday, 04:15 PM",
        description:
            "Water accumulation has been reported around the main road.",
        coordinates:
            "23.8315, 91.2868",
        evidence:
            "No evidence uploaded"
    },

    {
        id: "LS-1043",
        user: "Neha Verma",
        location: "Kohima, Nagaland",
        type: "Landslide",
        severity: "Low",
        status: "Resolved",
        submitted: "2 days ago",
        description:
            "Minor soil movement was noticed near a roadside slope.",
        coordinates:
            "25.6751, 94.1086",
        evidence:
            "Photo uploaded by user"
    },

    {
        id: "LS-1042",
        user: "Guwahati Resident",
        location: "Guwahati, Assam",
        type: "Flood",
        severity: "High",
        status: "Pending",
        submitted: "2 days ago",
        description:
            "Drainage overflow has caused significant water accumulation.",
        coordinates:
            "26.1500, 91.7400",
        evidence:
            "3 photos uploaded"
    },

    {
        id: "LS-1041",
        user: "Shillong Resident",
        location: "Shillong, Meghalaya",
        type: "Landslide",
        severity: "High",
        status: "Verified",
        submitted: "3 days ago",
        description:
            "Slope cracks have appeared near the residential area.",
        coordinates:
            "25.5900, 91.8800",
        evidence:
            "Photo uploaded by user"
    },

    {
        id: "LS-1040",
        user: "Aizawl Resident",
        location: "Aizawl, Mizoram",
        type: "Road Blockage",
        severity: "Medium",
        status: "Pending",
        submitted: "3 days ago",
        description:
            "A road has been partially blocked by fallen rocks.",
        coordinates:
            "23.7350, 92.7300",
        evidence:
            "Photo uploaded by user"
    },

    {
        id: "LS-1039",
        user: "Gangtok Resident",
        location: "Gangtok, Sikkim",
        type: "Other",
        severity: "Low",
        status: "Resolved",
        submitted: "4 days ago",
        description:
            "Minor drainage issue reported near a local road.",
        coordinates:
            "27.3300, 88.6100",
        evidence:
            "No evidence uploaded"
    },

    {
        id: "LS-1038",
        user: "Imphal Citizen",
        location: "Imphal, Manipur",
        type: "Flood",
        severity: "High",
        status: "Pending",
        submitted: "5 days ago",
        description:
            "Water has accumulated around several houses after heavy rainfall.",
        coordinates:
            "24.8170, 93.9368",
        evidence:
            "Photo uploaded by user"
    },

    {
        id: "LS-1037",
        user: "Itanagar Citizen",
        location: "Itanagar, Arunachal Pradesh",
        type: "Landslide",
        severity: "Medium",
        status: "Rejected",
        submitted: "6 days ago",
        description:
            "Minor soil movement was reported but could not be verified.",
        coordinates:
            "27.0844, 93.6053",
        evidence:
            "No evidence uploaded"
    }

];


/* =========================================================
   GLOBAL VARIABLE
========================================================= */

let selectedReport = null;


/* =========================================================
   DOM HELPER
========================================================= */

function getElement(id) {

    return document.getElementById(id);

}


/* =========================================================
   STATUS BADGE
========================================================= */

function getStatusBadge(status) {

    if (status === "Verified") {
        return "text-bg-success";
    }

    if (status === "Rejected") {
        return "text-bg-danger";
    }

    if (status === "Resolved") {
        return "text-bg-primary";
    }

    return "text-bg-warning";

}


/* =========================================================
   SEVERITY BADGE
========================================================= */

function getSeverityBadge(severity) {

    if (severity === "Critical") {
        return "text-bg-danger";
    }

    if (severity === "High") {
        return "text-bg-danger";
    }

    if (severity === "Medium") {
        return "text-bg-warning";
    }

    return "text-bg-success";

}


/* =========================================================
   UPDATE SUMMARY
========================================================= */

function updateSummary() {

    const total =
        reports.length;


    const pending =
        reports.filter(
            report => report.status === "Pending"
        ).length;


    const high =
        reports.filter(
            report =>
                report.severity === "High" ||
                report.severity === "Critical"
        ).length;


    const verified =
        reports.filter(
            report => report.status === "Verified"
        ).length;


    getElement("totalReports").textContent =
        total;


    getElement("pendingReports").textContent =
        pending;


    getElement("highReports").textContent =
        high;


    getElement("verifiedReports").textContent =
        verified;

}


/* =========================================================
   RENDER REPORT TABLE
========================================================= */

function renderReports(reportList) {

    const table =
        getElement("reportsTable");


    table.innerHTML = "";


    if (reportList.length === 0) {

        table.innerHTML = `

            <tr>

                <td colspan="8"
                    class="text-center text-secondary py-4">

                    <i class="bi bi-search fs-3 d-block mb-2"></i>

                    No reports found.

                </td>

            </tr>

        `;


        updateVisibleCount(0);

        return;

    }


    reportList.forEach(function (report) {

        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                <strong>${report.id}</strong>
            </td>

            <td>
                ${report.user}
            </td>

            <td>
                ${report.location}
            </td>

            <td>
                ${report.type}
            </td>

            <td>

                <span class="badge
                    ${getSeverityBadge(report.severity)}">

                    ${report.severity}

                </span>

            </td>

            <td>

                <span class="badge
                    ${getStatusBadge(report.status)}">

                    ${report.status}

                </span>

            </td>

            <td>
                <small>${report.submitted}</small>
            </td>

            <td>

                <button
                    class="btn btn-sm btn-outline-success"
                    data-report-id="${report.id}">

                    <i class="bi bi-eye me-1"></i>
                    View

                </button>

            </td>

        `;


        const viewButton =
            row.querySelector("button");


        viewButton.addEventListener(
            "click",
            function () {

                showReportDetails(
                    report.id
                );

            }
        );


        table.appendChild(row);

    });


    updateVisibleCount(
        reportList.length
    );

}


/* =========================================================
   UPDATE VISIBLE COUNT
========================================================= */

function updateVisibleCount(count) {

    const element =
        getElement("visibleReportCount");


    element.textContent =
        `${count} report${count === 1 ? "" : "s"}`;

}


/* =========================================================
   FILTER REPORTS
========================================================= */

function filterReports() {

    const search =
        getElement("reportSearch")
            .value
            .trim()
            .toLowerCase();


    const type =
        getElement("typeFilter")
            .value;


    const severity =
        getElement("severityFilter")
            .value;


    const status =
        getElement("statusFilter")
            .value;


    const filtered =
        reports.filter(
            function (report) {

                const matchesSearch =
                    !search ||

                    report.id
                        .toLowerCase()
                        .includes(search) ||

                    report.user
                        .toLowerCase()
                        .includes(search) ||

                    report.location
                        .toLowerCase()
                        .includes(search);


                const matchesType =
                    type === "all" ||
                    report.type === type;


                const matchesSeverity =
                    severity === "all" ||
                    report.severity === severity;


                const matchesStatus =
                    status === "all" ||
                    report.status === status;


                return (
                    matchesSearch &&
                    matchesType &&
                    matchesSeverity &&
                    matchesStatus
                );

            }
        );


    renderReports(filtered);

}


/* =========================================================
   CLEAR FILTERS
========================================================= */

function clearFilters() {

    getElement("reportSearch").value =
        "";

    getElement("typeFilter").value =
        "all";

    getElement("severityFilter").value =
        "all";

    getElement("statusFilter").value =
        "all";


    renderReports(reports);

}


/* =========================================================
   FIND REPORT
========================================================= */

function findReport(reportId) {

    return reports.find(
        report => report.id === reportId
    );

}


/* =========================================================
   SHOW REPORT DETAILS
========================================================= */

function showReportDetails(reportId) {

    const report =
        findReport(reportId);


    if (!report) {
        return;
    }


    selectedReport = report;


    const details =
        getElement("reportDetails");


    details.classList.remove(
        "d-none"
    );


    getElement("detailReportId")
        .textContent =
        report.id;


    getElement("detailUser")
        .textContent =
        `Submitted by ${report.user}`;


    getElement("detailStatus")
        .textContent =
        report.status;


    getElement("detailStatus")
        .className =
        `badge ${getStatusBadge(report.status)}`;


    getElement("detailLocation")
        .textContent =
        report.location;


    getElement("detailType")
        .textContent =
        report.type;


    getElement("detailSeverity")
        .textContent =
        report.severity;


    getElement("detailSubmitted")
        .textContent =
        report.submitted;


    getElement("detailDescription")
        .textContent =
        report.description;


    getElement("detailCoordinates")
        .textContent =
        report.coordinates;


    getElement("detailEvidence")
        .textContent =
        report.evidence;


    updateActionButtons();

}


/* =========================================================
   UPDATE ACTION BUTTONS
========================================================= */

function updateActionButtons() {

    if (!selectedReport) {
        return;
    }


    const verifyButton =
        getElement("verifyReportBtn");


    const rejectButton =
        getElement("rejectReportBtn");


    const resolveButton =
        getElement("resolveReportBtn");


    verifyButton.disabled =
        selectedReport.status === "Verified" ||
        selectedReport.status === "Resolved";


    rejectButton.disabled =
        selectedReport.status === "Rejected" ||
        selectedReport.status === "Resolved";


    resolveButton.disabled =
        selectedReport.status === "Resolved";

}


/* =========================================================
   UPDATE REPORT STATUS
========================================================= */

function updateReportStatus(
    newStatus
) {

    if (!selectedReport) {
        return;
    }


    if (
        selectedReport.status ===
        "Resolved"
    ) {

        window.alert(
            "This report is already resolved."
        );

        return;

    }


    selectedReport.status =
        newStatus;


    showReportDetails(
        selectedReport.id
    );


    filterReports();

    updateSummary();


    window.alert(
        `${selectedReport.id} status updated to ${newStatus}.`
    );

}


/* =========================================================
   VERIFY REPORT
========================================================= */

function verifySelectedReport() {

    if (!selectedReport) {

        window.alert(
            "Please select a report first."
        );

        return;

    }


    const confirmed =
        window.confirm(
            `Verify report ${selectedReport.id}?`
        );


    if (!confirmed) {
        return;
    }


    updateReportStatus(
        "Verified"
    );

}


/* =========================================================
   REJECT REPORT
========================================================= */

function rejectSelectedReport() {

    if (!selectedReport) {

        window.alert(
            "Please select a report first."
        );

        return;

    }


    const confirmed =
        window.confirm(
            `Reject report ${selectedReport.id}?`
        );


    if (!confirmed) {
        return;
    }


    updateReportStatus(
        "Rejected"
    );

}


/* =========================================================
   RESOLVE REPORT
========================================================= */

function resolveSelectedReport() {

    if (!selectedReport) {

        window.alert(
            "Please select a report first."
        );

        return;

    }


    const confirmed =
        window.confirm(
            `Mark report ${selectedReport.id} as resolved?`
        );


    if (!confirmed) {
        return;
    }


    updateReportStatus(
        "Resolved"
    );

}


/* =========================================================
   CLOSE DETAILS
========================================================= */

function closeReportDetails() {

    const details =
        getElement("reportDetails");


    details.classList.add(
        "d-none"
    );


    selectedReport = null;

}


/* =========================================================
   EVENT LISTENERS
========================================================= */

function setupEventListeners() {

    const search =
        getElement("reportSearch");


    if (search) {

        search.addEventListener(
            "input",
            filterReports
        );

    }


    const typeFilter =
        getElement("typeFilter");


    if (typeFilter) {

        typeFilter.addEventListener(
            "change",
            filterReports
        );

    }


    const severityFilter =
        getElement("severityFilter");


    if (severityFilter) {

        severityFilter.addEventListener(
            "change",
            filterReports
        );

    }


    const statusFilter =
        getElement("statusFilter");


    if (statusFilter) {

        statusFilter.addEventListener(
            "change",
            filterReports
        );

    }


    const clearButton =
        getElement("clearFiltersBtn");


    if (clearButton) {

        clearButton.addEventListener(
            "click",
            clearFilters
        );

    }


    const closeButton =
        getElement("closeDetailsBtn");


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeReportDetails
        );

    }


    const verifyButton =
        getElement("verifyReportBtn");


    if (verifyButton) {

        verifyButton.addEventListener(
            "click",
            verifySelectedReport
        );

    }


    const rejectButton =
        getElement("rejectReportBtn");


    if (rejectButton) {

        rejectButton.addEventListener(
            "click",
            rejectSelectedReport
        );

    }


    const resolveButton =
        getElement("resolveReportBtn");


    if (resolveButton) {

        resolveButton.addEventListener(
            "click",
            resolveSelectedReport
        );

    }

}


/* =========================================================
   INITIALIZE
========================================================= */

async function initializeUserReports() {
    if (window.LandSafeAPI) {
        try {
            const apiReports = await window.LandSafeAPI.getReports();
            if (apiReports && apiReports.length > 0) {
                reports = apiReports.map(r => ({
                    id: r.id,
                    user: r.user_name,
                    location: `${r.location_name}, ${r.state}`,
                    type: r.issue_type.charAt(0).toUpperCase() + r.issue_type.slice(1),
                    severity: r.severity.charAt(0).toUpperCase() + r.severity.slice(1),
                    status: r.status,
                    submitted: "Recent submission",
                    description: r.description,
                    coordinates: (r.latitude && r.longitude) ? `${r.latitude}, ${r.longitude}` : "26.1445, 91.7362",
                    evidence: r.evidence_desc || "Photo uploaded by user"
                }));
            }
        } catch (e) {
            console.warn("[UserReports] Using fallback static reports:", e.message);
        }
    }

    updateSummary();

    renderReports(reports);

    setupEventListeners();

}


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initializeUserReports
);