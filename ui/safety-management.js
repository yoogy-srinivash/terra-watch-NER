/* =========================================================
   LANDSAFE CONNECT
   SAFETY MANAGEMENT - ADMIN
   Demo Frontend Functionality
========================================================= */


/* =========================================================
   DEMO SAFETY GUIDES
========================================================= */

const safetyGuides = [

    {
        id: "SG-1001",
        title: "Flood Safety Guide",
        category: "Flood",
        audience: "All Users",
        status: "Active",
        updated: "Today",
        priority: "High",
        description:
            "Basic safety instructions for users during flood conditions and water-level rise.",
        instructions: [
            "Move to higher and safer ground when instructed.",
            "Avoid walking or driving through moving flood water.",
            "Keep emergency documents, medicines and essential supplies ready.",
            "Follow official evacuation instructions."
        ]
    },

    {
        id: "SG-1002",
        title: "Landslide Safety Guide",
        category: "Landslide",
        audience: "All Users",
        status: "Active",
        updated: "Today",
        priority: "Critical",
        description:
            "Safety instructions for areas affected by landslide risk, unstable slopes and falling debris.",
        instructions: [
            "Move away from unstable slopes and steep areas.",
            "Watch for cracks, falling rocks and unusual ground movement.",
            "Do not enter roads blocked by landslide debris.",
            "Follow evacuation instructions from authorities."
        ]
    },

    {
        id: "SG-1003",
        title: "Emergency Evacuation Checklist",
        category: "Evacuation",
        audience: "All Users",
        status: "Active",
        updated: "Yesterday",
        priority: "High",
        description:
            "Checklist to help users prepare for and follow an emergency evacuation.",
        instructions: [
            "Carry essential medicines and emergency supplies.",
            "Keep identification and important documents accessible.",
            "Follow designated evacuation routes.",
            "Inform family members before leaving when safe to do so."
        ]
    },

    {
        id: "SG-1004",
        title: "Emergency Kit Guide",
        category: "Emergency",
        audience: "All Users",
        status: "Active",
        updated: "Yesterday",
        priority: "Medium",
        description:
            "Recommended items for a basic emergency preparedness kit.",
        instructions: [
            "Keep drinking water and ready-to-eat food.",
            "Keep a first-aid kit and required medicines.",
            "Keep a flashlight and spare batteries.",
            "Keep a power bank and emergency contact information."
        ]
    },

    {
        id: "SG-1005",
        title: "Safe Shelter Guidance",
        category: "Shelter",
        audience: "All Users",
        status: "Active",
        updated: "2 days ago",
        priority: "High",
        description:
            "Guidance for selecting and reaching an available emergency shelter.",
        instructions: [
            "Use designated shelters whenever possible.",
            "Check the latest shelter availability before travelling.",
            "Avoid routes affected by active hazards.",
            "Follow instructions from shelter and emergency authorities."
        ]
    },

    {
        id: "SG-1006",
        title: "Flood Water Warning",
        category: "Flood",
        audience: "All Users",
        status: "Active",
        updated: "3 days ago",
        priority: "Critical",
        description:
            "Important precautions for contaminated, deep or rapidly moving flood water.",
        instructions: [
            "Do not enter rapidly moving water.",
            "Avoid contact with potentially contaminated water.",
            "Stay away from electrical equipment in flooded areas.",
            "Report dangerous conditions when communication is available."
        ]
    },

    {
        id: "SG-1007",
        title: "Landslide Warning Signs",
        category: "Landslide",
        audience: "Field Officials",
        status: "Active",
        updated: "4 days ago",
        priority: "High",
        description:
            "Reference information about environmental signs that may indicate slope instability.",
        instructions: [
            "Monitor newly developed ground cracks.",
            "Observe unusual movement of soil, rocks or structures.",
            "Monitor blocked drainage and sudden water changes.",
            "Report significant changes to responsible authorities."
        ]
    },

    {
        id: "SG-1008",
        title: "Emergency Response Instructions",
        category: "Emergency",
        audience: "Field Officials",
        status: "Inactive",
        updated: "5 days ago",
        priority: "High",
        description:
            "General response guidance for handling emergency reports and coordinating assistance.",
        instructions: [
            "Review emergency location and request details.",
            "Assess priority before assigning response resources.",
            "Coordinate with appropriate emergency teams.",
            "Update the request status after action is taken."
        ]
    }

];


/* =========================================================
   SELECTED GUIDE
========================================================= */

let selectedGuide = null;


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

    if (status === "Active") {

        return "text-bg-success";

    }

    return "text-bg-secondary";

}


/* =========================================================
   PRIORITY BADGE
========================================================= */

function getPriorityBadge(priority) {

    if (priority === "Critical") {

        return "text-bg-danger";

    }

    if (priority === "High") {

        return "text-bg-warning";

    }

    if (priority === "Medium") {

        return "text-bg-primary";

    }

    return "text-bg-secondary";

}


/* =========================================================
   CATEGORY BADGE
========================================================= */

function getCategoryBadge(category) {

    if (category === "Flood") {

        return "text-bg-primary";

    }

    if (category === "Landslide") {

        return "text-bg-danger";

    }

    if (category === "Emergency") {

        return "text-bg-warning";

    }

    if (category === "Shelter") {

        return "text-bg-success";

    }

    return "text-bg-secondary";

}


/* =========================================================
   UPDATE SUMMARY
========================================================= */

function updateSummary() {

    const total =
        safetyGuides.length;


    const active =
        safetyGuides.filter(
            guide =>
                guide.status === "Active"
        ).length;


    const flood =
        safetyGuides.filter(
            guide =>
                guide.category === "Flood"
        ).length;


    const landslide =
        safetyGuides.filter(
            guide =>
                guide.category === "Landslide"
        ).length;


    getElement("totalGuides")
        .textContent =
        total;


    getElement("activeGuides")
        .textContent =
        active;


    getElement("floodGuides")
        .textContent =
        flood;


    getElement("landslideGuides")
        .textContent =
        landslide;

}


/* =========================================================
   RENDER TABLE
========================================================= */

function renderGuides(guideList) {

    const table =
        getElement("guidesTable");


    table.innerHTML = "";


    if (guideList.length === 0) {

        table.innerHTML = `

            <tr>

                <td colspan="7"
                    class="text-center text-secondary py-4">

                    <i class="bi bi-search fs-3 d-block mb-2"></i>

                    No safety guides found.

                </td>

            </tr>

        `;


        updateVisibleCount(0);

        return;

    }


    guideList.forEach(function (guide) {

        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>

                <strong>
                    ${guide.id}
                </strong>

            </td>


            <td>

                <strong>
                    ${guide.title}
                </strong>

            </td>


            <td>

                <span class="badge
                    ${getCategoryBadge(guide.category)}">

                    ${guide.category}

                </span>

            </td>


            <td>
                ${guide.audience}
            </td>


            <td>

                <span class="badge
                    ${getStatusBadge(guide.status)}">

                    ${guide.status}

                </span>

            </td>


            <td>

                <small>
                    ${guide.updated}
                </small>

            </td>


            <td>

                <button
                    class="btn btn-sm btn-outline-primary">

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

                showGuideDetails(
                    guide.id
                );

            }
        );


        table.appendChild(row);

    });


    updateVisibleCount(
        guideList.length
    );

}


/* =========================================================
   VISIBLE COUNT
========================================================= */

function updateVisibleCount(count) {

    const element =
        getElement("visibleGuideCount");


    element.textContent =
        `${count} guide${count === 1 ? "" : "s"}`;

}


/* =========================================================
   FILTER GUIDES
========================================================= */

function filterGuides() {

    const search =
        getElement("guideSearch")
            .value
            .trim()
            .toLowerCase();


    const category =
        getElement("categoryFilter")
            .value;


    const status =
        getElement("statusFilter")
            .value;


    const filtered =
        safetyGuides.filter(
            function (guide) {

                const matchesSearch =
                    !search ||

                    guide.id
                        .toLowerCase()
                        .includes(search) ||

                    guide.title
                        .toLowerCase()
                        .includes(search) ||

                    guide.description
                        .toLowerCase()
                        .includes(search);


                const matchesCategory =
                    category === "all" ||
                    guide.category === category;


                const matchesStatus =
                    status === "all" ||
                    guide.status === status;


                return (
                    matchesSearch &&
                    matchesCategory &&
                    matchesStatus
                );

            }
        );


    renderGuides(filtered);

}


/* =========================================================
   CLEAR FILTERS
========================================================= */

function clearFilters() {

    getElement("guideSearch")
        .value = "";


    getElement("categoryFilter")
        .value = "all";


    getElement("statusFilter")
        .value = "all";


    renderGuides(
        safetyGuides
    );

}


/* =========================================================
   FIND GUIDE
========================================================= */

function findGuide(guideId) {

    return safetyGuides.find(
        guide =>
            guide.id === guideId
    );

}


/* =========================================================
   SHOW GUIDE DETAILS
========================================================= */

function showGuideDetails(guideId) {

    const guide =
        findGuide(guideId);


    if (!guide) {
        return;
    }


    selectedGuide =
        guide;


    const details =
        getElement("guideDetails");


    details.classList.remove(
        "d-none"
    );


    getElement("detailGuideTitle")
        .textContent =
        guide.title;


    getElement("detailGuideId")
        .textContent =
        guide.id;


    getElement("detailGuideStatus")
        .textContent =
        guide.status;


    getElement("detailGuideStatus")
        .className =
        `badge ${getStatusBadge(guide.status)}`;


    getElement("detailCategory")
        .textContent =
        guide.category;


    getElement("detailAudience")
        .textContent =
        guide.audience;


    getElement("detailUpdated")
        .textContent =
        guide.updated;


    getElement("detailPriority")
        .textContent =
        guide.priority;


    getElement("detailDescription")
        .textContent =
        guide.description;


    const instructionList =
        getElement("detailInstructions");


    instructionList.innerHTML = "";


    guide.instructions.forEach(
        function (instruction) {

            const item =
                document.createElement("li");


            item.textContent =
                instruction;


            instructionList.appendChild(
                item
            );

        }
    );


    updateManagementButtons();

}


/* =========================================================
   UPDATE MANAGEMENT BUTTONS
========================================================= */

function updateManagementButtons() {

    if (!selectedGuide) {
        return;
    }


    const toggleButton =
        getElement("toggleGuideBtn");


    if (
        selectedGuide.status ===
        "Active"
    ) {

        toggleButton.innerHTML =
            `<i class="bi bi-toggle-off me-1"></i>
             Deactivate Guide`;

    } else {

        toggleButton.innerHTML =
            `<i class="bi bi-toggle-on me-1"></i>
             Activate Guide`;

    }

}


/* =========================================================
   TOGGLE GUIDE STATUS
========================================================= */

function toggleGuideStatus() {

    if (!selectedGuide) {

        window.alert(
            "Please select a safety guide first."
        );

        return;

    }


    if (
        selectedGuide.status ===
        "Active"
    ) {

        selectedGuide.status =
            "Inactive";

    } else {

        selectedGuide.status =
            "Active";

    }


    showGuideDetails(
        selectedGuide.id
    );


    updateSummary();

    filterGuides();


    window.alert(
        `${selectedGuide.id} status changed to ${selectedGuide.status}.`
    );

}


/* =========================================================
   EDIT GUIDE
========================================================= */

function editGuide() {

    if (!selectedGuide) {

        window.alert(
            "Please select a safety guide first."
        );

        return;

    }


    const newDescription =
        window.prompt(
            "Update guide description:",
            selectedGuide.description
        );


    if (
        newDescription === null ||
        newDescription.trim() === ""
    ) {

        return;

    }


    selectedGuide.description =
        newDescription.trim();


    selectedGuide.updated =
        "Just now";


    showGuideDetails(
        selectedGuide.id
    );


    filterGuides();


    window.alert(
        `${selectedGuide.id} updated successfully.`
    );

}


/* =========================================================
   DELETE GUIDE
========================================================= */

function deleteGuide() {

    if (!selectedGuide) {

        window.alert(
            "Please select a safety guide first."
        );

        return;

    }


    const confirmed =
        window.confirm(
            `Delete ${selectedGuide.id} - ${selectedGuide.title}?`
        );


    if (!confirmed) {
        return;
    }


    const index =
        safetyGuides.indexOf(
            selectedGuide
        );


    if (index !== -1) {

        safetyGuides.splice(
            index,
            1
        );

    }


    const deletedId =
        selectedGuide.id;


    selectedGuide =
        null;


    getElement("guideDetails")
        .classList.add("d-none");


    updateSummary();

    filterGuides();


    window.alert(
        `${deletedId} removed from active advisories.`
    );

}


/* =========================================================
   ADD SAFETY GUIDE
========================================================= */

function addSafetyGuide() {

    const title =
        window.prompt(
            "Enter safety guide title:"
        );


    if (!title || !title.trim()) {
        return;
    }


    const category =
        window.prompt(
            "Enter category: Flood / Landslide / Emergency / Shelter / Evacuation"
        );


    if (!category || !category.trim()) {
        return;
    }


    const description =
        window.prompt(
            "Enter guide description:"
        );


    if (!description || !description.trim()) {
        return;
    }


    const newId =
        `SG-${1001 + safetyGuides.length}`;


    const newGuide = {

        id: newId,

        title: title.trim(),

        category: category.trim(),

        audience: "All Users",

        status: "Active",

        updated: "Just now",

        priority: "Medium",

        description:
            description.trim(),

        instructions: [
            "Follow official emergency instructions.",
            "Move to a safer location when required.",
            "Keep essential emergency supplies ready."
        ]

    };


    safetyGuides.unshift(
        newGuide
    );


    updateSummary();

    filterGuides();


    window.alert(
        `${newId} added successfully.`
    );

}


/* =========================================================
   CLOSE DETAILS
========================================================= */

function closeGuideDetails() {

    getElement("guideDetails")
        .classList.add("d-none");


    selectedGuide =
        null;

}


/* =========================================================
   EVENT LISTENERS
========================================================= */

function setupEventListeners() {

    const search =
        getElement("guideSearch");


    if (search) {

        search.addEventListener(
            "input",
            filterGuides
        );

    }


    const categoryFilter =
        getElement("categoryFilter");


    if (categoryFilter) {

        categoryFilter.addEventListener(
            "change",
            filterGuides
        );

    }


    const statusFilter =
        getElement("statusFilter");


    if (statusFilter) {

        statusFilter.addEventListener(
            "change",
            filterGuides
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


    const addButton =
        getElement("addGuideBtn");


    if (addButton) {

        addButton.addEventListener(
            "click",
            addSafetyGuide
        );

    }


    const closeButton =
        getElement("closeDetailsBtn");


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeGuideDetails
        );

    }


    const editButton =
        getElement("editGuideBtn");


    if (editButton) {

        editButton.addEventListener(
            "click",
            editGuide
        );

    }


    const toggleButton =
        getElement("toggleGuideBtn");


    if (toggleButton) {

        toggleButton.addEventListener(
            "click",
            toggleGuideStatus
        );

    }


    const deleteButton =
        getElement("deleteGuideBtn");


    if (deleteButton) {

        deleteButton.addEventListener(
            "click",
            deleteGuide
        );

    }

}


/* =========================================================
   INITIALIZE
========================================================= */

function initializeSafetyManagement() {

    updateSummary();

    renderGuides(
        safetyGuides
    );

    setupEventListeners();

}


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initializeSafetyManagement
);