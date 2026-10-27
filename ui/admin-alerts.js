// =========================================
// LANDSAFE CONNECT
// ADMIN ALERTS - JAVASCRIPT
// =========================================


// =========================================
// DEMO ALERT DATA
// =========================================

let alerts = [

    {
        id: "AL-2001",
        location: "Guwahati, Assam",
        type: "Flood",
        severity: "Critical",
        status: "Active",
        time: "10:30 AM"
    },

    {
        id: "AL-2002",
        location: "Shillong, Meghalaya",
        type: "Landslide",
        severity: "High",
        status: "Active",
        time: "09:45 AM"
    },

    {
        id: "AL-2003",
        location: "Aizawl, Mizoram",
        type: "Landslide",
        severity: "High",
        status: "Active",
        time: "08:20 AM"
    },

    {
        id: "AL-2004",
        location: "Agartala, Tripura",
        type: "Flood",
        severity: "Medium",
        status: "Active",
        time: "Yesterday"
    },

    {
        id: "AL-2005",
        location: "Imphal, Manipur",
        type: "Flood",
        severity: "Medium",
        status: "Resolved",
        time: "2 days ago"
    },

    {
        id: "AL-2006",
        location: "Kohima, Nagaland",
        type: "Landslide",
        severity: "Low",
        status: "Resolved",
        time: "3 days ago"
    },

    {
        id: "AL-2007",
        location: "Itanagar, Arunachal Pradesh",
        type: "Flood",
        severity: "Low",
        status: "Resolved",
        time: "4 days ago"
    }

];


// =========================================
// GET ELEMENT
// =========================================

function getElement(id) {

    return document.getElementById(id);

}


// =========================================
// UPDATE SUMMARY
// =========================================

function updateSummary() {

    const active =
        alerts.filter(
            alert => alert.status === "Active"
        ).length;


    const critical =
        alerts.filter(
            alert => alert.severity === "Critical"
        ).length;


    const high =
        alerts.filter(
            alert => alert.severity === "High"
        ).length;


    const resolved =
        alerts.filter(
            alert => alert.status === "Resolved"
        ).length;


    const activeElement =
        getElement("activeAlerts");

    const criticalElement =
        getElement("criticalAlerts");

    const highElement =
        getElement("highAlerts");

    const resolvedElement =
        getElement("resolvedAlerts");


    if (activeElement) {
        activeElement.textContent = active;
    }

    if (criticalElement) {
        criticalElement.textContent = critical;
    }

    if (highElement) {
        highElement.textContent = high;
    }

    if (resolvedElement) {
        resolvedElement.textContent = resolved;
    }

}


// =========================================
// FILTER ALERTS
// =========================================

function filterAlerts() {

    const typeFilter =
        getElement("alertTypeFilter");

    const severityFilter =
        getElement("alertSeverityFilter");

    const statusFilter =
        getElement("alertStatusFilter");


    if (
        !typeFilter ||
        !severityFilter ||
        !statusFilter
    ) {
        return;
    }


    const selectedType =
        typeFilter.value;

    const selectedSeverity =
        severityFilter.value;

    const selectedStatus =
        statusFilter.value;


    const rows =
        document.querySelectorAll(
            "#alertsTable tr"
        );


    let visibleCount = 0;


    rows.forEach(row => {

        const type =
            row.dataset.type;

        const severity =
            row.dataset.severity;

        const status =
            row.dataset.status;


        const typeMatch =
            selectedType === "all" ||
            type === selectedType;


        const severityMatch =
            selectedSeverity === "all" ||
            severity === selectedSeverity;


        const statusMatch =
            selectedStatus === "all" ||
            status === selectedStatus;


        if (
            typeMatch &&
            severityMatch &&
            statusMatch
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
// UPDATE VISIBLE COUNT
// =========================================

function updateVisibleCount(count) {

    const element =
        getElement("visibleAlertCount");


    if (!element) {
        return;
    }


    element.textContent =
        `${count} ${count === 1 ? "alert" : "alerts"}`;

}


// =========================================
// CLEAR FILTERS
// =========================================

function clearFilters() {

    const typeFilter =
        getElement("alertTypeFilter");

    const severityFilter =
        getElement("alertSeverityFilter");

    const statusFilter =
        getElement("alertStatusFilter");


    if (typeFilter) {
        typeFilter.value = "all";
    }

    if (severityFilter) {
        severityFilter.value = "all";
    }

    if (statusFilter) {
        statusFilter.value = "all";
    }


    filterAlerts();

}


// =========================================
// FIND ALERT
// =========================================

function findAlert(alertId) {

    return alerts.find(
        alert => alert.id === alertId
    );

}


// =========================================
// SHOW ALERT DETAILS
// =========================================

function showAlertDetails(alertId) {

    const alert =
        findAlert(alertId);


    if (!alert) {
        return;
    }


    const detailsCard =
        getElement("alertDetails");


    if (!detailsCard) {
        return;
    }


    const idElement =
        getElement("detailAlertId");

    const locationElement =
        getElement("detailAlertLocation");

    const typeElement =
        getElement("detailAlertType");

    const severityElement =
        getElement("detailAlertSeverity");

    const statusElement =
        getElement("detailAlertStatus");

    const timeElement =
        getElement("detailAlertTime");


    if (idElement) {
        idElement.textContent =
            alert.id;
    }


    if (locationElement) {
        locationElement.textContent =
            alert.location;
    }


    if (typeElement) {
        typeElement.textContent =
            alert.type;
    }


    if (severityElement) {
        severityElement.textContent =
            alert.severity;
    }


    if (statusElement) {
        statusElement.textContent =
            alert.status;
    }


    if (timeElement) {
        timeElement.textContent =
            alert.time;
    }


    // Store selected alert ID
    detailsCard.dataset.alertId =
        alert.id;


    detailsCard.classList.remove("d-none");


    detailsCard.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


// =========================================
// CLOSE DETAILS
// =========================================

function closeAlertDetails() {

    const detailsCard =
        getElement("alertDetails");


    if (!detailsCard) {
        return;
    }


    detailsCard.classList.add("d-none");

}


// =========================================
// RESOLVE ALERT
// =========================================

function resolveSelectedAlert() {

    const detailsCard =
        getElement("alertDetails");


    if (!detailsCard) {
        return;
    }


    const alertId =
        detailsCard.dataset.alertId;


    const alert =
        findAlert(alertId);


    if (!alert) {
        return;
    }


    if (alert.status === "Resolved") {

        alert(
            "This alert is already resolved."
        );

        return;
    }


    const confirmed =
        confirm(
            `Resolve alert ${alert.id}?`
        );


    if (!confirmed) {
        return;
    }


    alert.status = "Resolved";


    // Update table row
    const row =
        document.querySelector(
            `#alertsTable tr[data-alert-id="${alert.id}"]`
        );


    if (row) {

        row.dataset.status =
            "Resolved";

    }


    alert(
        `${alert.id} has been resolved successfully.`
    );


    updateSummary();

    filterAlerts();

    closeAlertDetails();

}


// =========================================
// CREATE ALERT
// =========================================

function createNewAlert() {

    const location =
        prompt(
            "Enter affected location:"
        );


    if (!location) {
        return;
    }


    const type =
        prompt(
            "Enter alert type: Flood or Landslide"
        );


    if (!type) {
        return;
    }


    const severity =
        prompt(
            "Enter severity: Critical, High, Medium or Low"
        );


    if (!severity) {
        return;
    }


    const newId =
        `AL-${2001 + alerts.length}`;


    const newAlert = {

        id: newId,

        location: location,

        type: type,

        severity: severity,

        status: "Active",

        time: new Date().toLocaleTimeString(
            "en-IN",
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        )

    };


    alerts.unshift(newAlert);


    alert(
        `Alert bulletin ${newId} created and dispatched.`
    );


    updateSummary();

    window.location.reload();

}


// =========================================
// SETUP FILTER EVENTS
// =========================================

function setupFilters() {

    const filters = [

        "alertTypeFilter",

        "alertSeverityFilter",

        "alertStatusFilter"

    ];


    filters.forEach(id => {

        const element =
            getElement(id);


        if (element) {

            element.addEventListener(
                "change",
                filterAlerts
            );

        }

    });


    const clearButton =
        getElement("clearAlertFilters");


    if (clearButton) {

        clearButton.addEventListener(
            "click",
            clearFilters
        );

    }

}


// =========================================
// SETUP VIEW BUTTONS
// =========================================

function setupViewButtons() {

    const buttons =
        document.querySelectorAll(
            ".view-alert"
        );


    buttons.forEach(button => {

        button.addEventListener(
            "click",
            function () {

                const alertId =
                    this.dataset.alertId;


                showAlertDetails(
                    alertId
                );

            }
        );

    });

}


// =========================================
// ADD ALERT IDs TO TABLE ROWS
// =========================================

function setupRowIds() {

    const buttons =
        document.querySelectorAll(
            ".view-alert"
        );


    buttons.forEach(button => {

        const alertId =
            button.dataset.alertId;


        const row =
            button.closest("tr");


        if (row) {

            row.dataset.alertId =
                alertId;

        }

    });

}


// =========================================
// INITIALIZE
// =========================================

async function initializeAdminAlerts() {
    if (window.LandSafeAPI) {
        try {
            const apiAlerts = await window.LandSafeAPI.getAlerts();
            if (apiAlerts && apiAlerts.length > 0) {
                alerts = apiAlerts.map(a => ({
                    id: a.id,
                    location: a.location,
                    type: a.hazard_type,
                    severity: a.severity,
                    status: a.status,
                    time: a.time
                }));
            }
        } catch (e) {
            console.warn("[AdminAlerts] Using fallback static alerts:", e.message);
        }
    }

    setupRowIds();

    updateSummary();

    setupFilters();

    setupViewButtons();

    updateVisibleCount(
        alerts.length
    );


    const closeButton =
        getElement("closeAlertDetails");


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeAlertDetails
        );

    }


    const resolveButton =
        getElement("resolveAlertButton");


    if (resolveButton) {

        resolveButton.addEventListener(
            "click",
            resolveSelectedAlert
        );

    }


    const createButton =
        getElement("createAlertButton");


    if (createButton) {

        createButton.addEventListener(
            "click",
            createNewAlert
        );

    }

}


// =========================================
// PAGE LOAD
// =========================================

document.addEventListener(
    "DOMContentLoaded",
    initializeAdminAlerts
);