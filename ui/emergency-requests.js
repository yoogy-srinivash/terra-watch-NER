/* =========================================================
   LANDSAFE CONNECT
   EMERGENCY REQUESTS - ADMIN
   Demo Frontend Functionality
========================================================= */


/* =========================================================
   DEMO EMERGENCY REQUESTS
========================================================= */

let emergencyRequests = [

    {
        id: "ER-3008",
        user: "Rahul Sharma",
        location: "Guwahati, Assam",
        type: "Trapped",
        priority: "Critical",
        status: "Pending",
        submitted: "Today, 11:05 AM",
        description:
            "User reports being trapped inside a flooded residential area and requests immediate rescue assistance.",
        coordinates:
            "26.1445, 91.7362",
        shelter:
            "Guwahati Relief Shelter"
    },

    {
        id: "ER-3007",
        user: "Ananya Das",
        location: "Shillong, Meghalaya",
        type: "Landslide",
        priority: "Critical",
        status: "In Progress",
        submitted: "Today, 10:20 AM",
        description:
            "A landslide has blocked the nearby road and the user reports unsafe conditions around the residence.",
        coordinates:
            "25.5788, 91.8933",
        shelter:
            "Shillong Higher Ground Shelter"
    },

    {
        id: "ER-3006",
        user: "Mizoram Citizen",
        location: "Aizawl, Mizoram",
        type: "Trapped",
        priority: "High",
        status: "Assigned",
        submitted: "Today, 09:45 AM",
        description:
            "User reports being unable to safely leave the affected area because of soil and rock movement.",
        coordinates:
            "23.7271, 92.7176",
        shelter:
            "Aizawl Community Relief Centre"
    },

    {
        id: "ER-3005",
        user: "Priya Singh",
        location: "Gangtok, Sikkim",
        type: "Medical",
        priority: "High",
        status: "In Progress",
        submitted: "Today, 08:30 AM",
        description:
            "Medical assistance requested after a person was injured near a landslide-affected road.",
        coordinates:
            "27.3389, 88.6065",
        shelter:
            "Nearby Emergency Shelter"
    },

    {
        id: "ER-3004",
        user: "Arun Kumar",
        location: "Agartala, Tripura",
        type: "Flood",
        priority: "Medium",
        status: "Pending",
        submitted: "Yesterday, 06:10 PM",
        description:
            "User reports rising water around the residential area and requests assistance with evacuation.",
        coordinates:
            "23.8315, 91.2868",
        shelter:
            "Agartala Emergency Shelter"
    },

    {
        id: "ER-3003",
        user: "Neha Verma",
        location: "Kohima, Nagaland",
        type: "Landslide",
        priority: "Medium",
        status: "Resolved",
        submitted: "2 days ago",
        description:
            "User requested assistance after minor soil movement was observed near the road.",
        coordinates:
            "25.6751, 94.1086",
        shelter:
            "Local Community Shelter"
    },

    {
        id: "ER-3002",
        user: "Imphal Citizen",
        location: "Imphal, Manipur",
        type: "Flood",
        priority: "High",
        status: "Resolved",
        submitted: "3 days ago",
        description:
            "User requested evacuation assistance because of water accumulation near homes.",
        coordinates:
            "24.8170, 93.9368",
        shelter:
            "Community Relief Centre"
    },

    {
        id: "ER-3001",
        user: "Itanagar Citizen",
        location: "Itanagar, Arunachal Pradesh",
        type: "Other",
        priority: "Low",
        status: "Resolved",
        submitted: "4 days ago",
        description:
            "User reported a minor environmental safety concern requiring local assistance.",
        coordinates:
            "27.0844, 93.6053",
        shelter:
            "Local Community Shelter"
    }

];


/* =========================================================
   GLOBAL VARIABLE
========================================================= */

let selectedRequest = null;


/* =========================================================
   DOM HELPER
========================================================= */

function getElement(id) {

    return document.getElementById(id);

}


/* =========================================================
   PRIORITY BADGE
========================================================= */

function getPriorityBadge(priority) {

    if (priority === "Critical") {
        return "text-bg-danger";
    }

    if (priority === "High") {
        return "text-bg-danger";
    }

    if (priority === "Medium") {
        return "text-bg-warning";
    }

    return "text-bg-success";

}


/* =========================================================
   STATUS BADGE
========================================================= */

function getStatusBadge(status) {

    if (status === "Resolved") {
        return "text-bg-success";
    }

    if (status === "In Progress") {
        return "text-bg-warning";
    }

    if (status === "Assigned") {
        return "text-bg-primary";
    }

    return "text-bg-secondary";

}


/* =========================================================
   UPDATE SUMMARY
========================================================= */

function updateSummary() {

    const total =
        emergencyRequests.length;


    const critical =
        emergencyRequests.filter(
            request =>
                request.priority === "Critical"
        ).length;


    const inProgress =
        emergencyRequests.filter(
            request =>
                request.status === "In Progress"
        ).length;


    const resolved =
        emergencyRequests.filter(
            request =>
                request.status === "Resolved"
        ).length;


    getElement("totalRequests")
        .textContent =
        total;


    getElement("criticalRequests")
        .textContent =
        critical;


    getElement("inProgressRequests")
        .textContent =
        inProgress;


    getElement("resolvedRequests")
        .textContent =
        resolved;

}


/* =========================================================
   RENDER REQUEST TABLE
========================================================= */

function renderRequests(requestList) {

    const table =
        getElement("requestsTable");


    table.innerHTML = "";


    if (requestList.length === 0) {

        table.innerHTML = `

            <tr>

                <td colspan="8"
                    class="text-center text-secondary py-4">

                    <i class="bi bi-search fs-3 d-block mb-2"></i>

                    No emergency requests found.

                </td>

            </tr>

        `;


        updateVisibleCount(0);

        return;

    }


    requestList.forEach(function (request) {

        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                <strong>${request.id}</strong>
            </td>

            <td>
                ${request.user}
            </td>

            <td>
                ${request.location}
            </td>

            <td>
                ${request.type}
            </td>

            <td>

                <span class="badge
                    ${getPriorityBadge(request.priority)}">

                    ${request.priority}

                </span>

            </td>

            <td>

                <span class="badge
                    ${getStatusBadge(request.status)}">

                    ${request.status}

                </span>

            </td>

            <td>
                <small>${request.submitted}</small>
            </td>

            <td>

                <button
                    class="btn btn-sm btn-outline-danger"
                    data-request-id="${request.id}">

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

                showRequestDetails(
                    request.id
                );

            }
        );


        table.appendChild(row);

    });


    updateVisibleCount(
        requestList.length
    );

}


/* =========================================================
   UPDATE VISIBLE COUNT
========================================================= */

function updateVisibleCount(count) {

    const element =
        getElement("visibleRequestCount");


    element.textContent =
        `${count} request${count === 1 ? "" : "s"}`;

}


/* =========================================================
   FILTER REQUESTS
========================================================= */

function filterRequests() {

    const search =
        getElement("requestSearch")
            .value
            .trim()
            .toLowerCase();


    const type =
        getElement("typeFilter")
            .value;


    const priority =
        getElement("priorityFilter")
            .value;


    const status =
        getElement("statusFilter")
            .value;


    const filtered =
        emergencyRequests.filter(
            function (request) {

                const matchesSearch =
                    !search ||

                    request.id
                        .toLowerCase()
                        .includes(search) ||

                    request.user
                        .toLowerCase()
                        .includes(search) ||

                    request.location
                        .toLowerCase()
                        .includes(search);


                const matchesType =
                    type === "all" ||
                    request.type === type;


                const matchesPriority =
                    priority === "all" ||
                    request.priority === priority;


                const matchesStatus =
                    status === "all" ||
                    request.status === status;


                return (
                    matchesSearch &&
                    matchesType &&
                    matchesPriority &&
                    matchesStatus
                );

            }
        );


    renderRequests(filtered);

}


/* =========================================================
   CLEAR FILTERS
========================================================= */

function clearFilters() {

    getElement("requestSearch").value =
        "";

    getElement("typeFilter").value =
        "all";

    getElement("priorityFilter").value =
        "all";

    getElement("statusFilter").value =
        "all";


    renderRequests(
        emergencyRequests
    );

}


/* =========================================================
   FIND REQUEST
========================================================= */

function findRequest(requestId) {

    return emergencyRequests.find(
        request =>
            request.id === requestId
    );

}


/* =========================================================
   SHOW REQUEST DETAILS
========================================================= */

function showRequestDetails(requestId) {

    const request =
        findRequest(requestId);


    if (!request) {
        return;
    }


    selectedRequest =
        request;


    const details =
        getElement("requestDetails");


    details.classList.remove(
        "d-none"
    );


    getElement("detailRequestId")
        .textContent =
        request.id;


    getElement("detailUser")
        .textContent =
        `Emergency request submitted by ${request.user}`;


    getElement("detailPriority")
        .textContent =
        request.priority;


    getElement("detailPriority")
        .className =
        `badge ${getPriorityBadge(request.priority)}`;


    getElement("detailLocation")
        .textContent =
        request.location;


    getElement("detailType")
        .textContent =
        request.type;


    getElement("detailStatus")
        .textContent =
        request.status;


    getElement("detailSubmitted")
        .textContent =
        request.submitted;


    getElement("detailDescription")
        .textContent =
        request.description;


    getElement("detailCoordinates")
        .textContent =
        request.coordinates;


    getElement("detailShelter")
        .textContent =
        request.shelter;


    getElement("responseTeam")
        .value =
        "";


    updateActionButtons();

}


/* =========================================================
   UPDATE ACTION BUTTONS
========================================================= */

function updateActionButtons() {

    if (!selectedRequest) {
        return;
    }


    const assignButton =
        getElement("assignRequestBtn");


    const progressButton =
        getElement("progressRequestBtn");


    const resolveButton =
        getElement("resolveRequestBtn");


    assignButton.disabled =
        selectedRequest.status ===
        "Resolved";


    progressButton.disabled =
        selectedRequest.status ===
        "Resolved";


    resolveButton.disabled =
        selectedRequest.status ===
        "Resolved";

}


/* =========================================================
   ASSIGN REQUEST
========================================================= */

function assignRequest() {

    if (!selectedRequest) {

        window.alert(
            "Please select an emergency request first."
        );

        return;

    }


    const team =
        getElement("responseTeam")
            .value;


    if (!team) {

        window.alert(
            "Please select a response team."
        );

        return;

    }


    if (
        selectedRequest.status ===
        "Resolved"
    ) {

        window.alert(
            "This request is already resolved."
        );

        return;

    }


    selectedRequest.status =
        "Assigned";


    showRequestDetails(
        selectedRequest.id
    );


    filterRequests();

    updateSummary();


    window.alert(
        `${selectedRequest.id} assigned to ${team}. Dispatch confirmed.`
    );

}


/* =========================================================
   MARK IN PROGRESS
========================================================= */

function markRequestInProgress() {

    if (!selectedRequest) {

        window.alert(
            "Please select an emergency request first."
        );

        return;

    }


    if (
        selectedRequest.status ===
        "Resolved"
    ) {

        window.alert(
            "This request is already resolved."
        );

        return;

    }


    selectedRequest.status =
        "In Progress";


    showRequestDetails(
        selectedRequest.id
    );


    filterRequests();

    updateSummary();


    window.alert(
        `${selectedRequest.id} is now marked as In Progress.`
    );

}


/* =========================================================
   MARK RESOLVED
========================================================= */

function resolveRequest() {

    if (!selectedRequest) {

        window.alert(
            "Please select an emergency request first."
        );

        return;

    }


    if (
        selectedRequest.status ===
        "Resolved"
    ) {

        window.alert(
            "This request is already resolved."
        );

        return;

    }


    const confirmed =
        window.confirm(
            `Mark emergency request ${selectedRequest.id} as resolved?`
        );


    if (!confirmed) {
        return;
    }


    selectedRequest.status =
        "Resolved";


    showRequestDetails(
        selectedRequest.id
    );


    filterRequests();

    updateSummary();


    window.alert(
        `${selectedRequest.id} has been resolved successfully.`
    );

}


/* =========================================================
   CLOSE DETAILS
========================================================= */

function closeRequestDetails() {

    const details =
        getElement("requestDetails");


    details.classList.add(
        "d-none"
    );


    selectedRequest = null;

}


/* =========================================================
   EVENT LISTENERS
========================================================= */

function setupEventListeners() {

    const search =
        getElement("requestSearch");


    if (search) {

        search.addEventListener(
            "input",
            filterRequests
        );

    }


    const typeFilter =
        getElement("typeFilter");


    if (typeFilter) {

        typeFilter.addEventListener(
            "change",
            filterRequests
        );

    }


    const priorityFilter =
        getElement("priorityFilter");


    if (priorityFilter) {

        priorityFilter.addEventListener(
            "change",
            filterRequests
        );

    }


    const statusFilter =
        getElement("statusFilter");


    if (statusFilter) {

        statusFilter.addEventListener(
            "change",
            filterRequests
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
            closeRequestDetails
        );

    }


    const assignButton =
        getElement("assignRequestBtn");


    if (assignButton) {

        assignButton.addEventListener(
            "click",
            assignRequest
        );

    }


    const progressButton =
        getElement("progressRequestBtn");


    if (progressButton) {

        progressButton.addEventListener(
            "click",
            markRequestInProgress
        );

    }


    const resolveButton =
        getElement("resolveRequestBtn");


    if (resolveButton) {

        resolveButton.addEventListener(
            "click",
            resolveRequest
        );

    }

}


/* =========================================================
   INITIALIZE
========================================================= */

async function initializeEmergencyRequests() {
    if (window.LandSafeAPI) {
        try {
            const apiReqs = await window.LandSafeAPI.getEmergencyRequests();
            if (apiReqs && apiReqs.length > 0) {
                emergencyRequests = apiReqs;
            }
        } catch (e) {
            console.warn("[Emergency] Using fallback static requests:", e.message);
        }
    }

    updateSummary();

    renderRequests(
        emergencyRequests
    );

    setupEventListeners();

}


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initializeEmergencyRequests
);