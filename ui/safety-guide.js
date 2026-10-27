const shelters = [
    {
        name: "Emergency Relief Shelter - Guwahati",
        lat: 26.1445,
        lng: 91.7362,
        type: "Emergency Shelter",
        capacity: "Available"
    },

    {
        name: "Community Relief Centre",
        lat: 26.1510,
        lng: 91.7500,
        type: "Relief Centre",
        capacity: "Available"
    },

    {
        name: "Safe Evacuation Centre",
        lat: 26.1350,
        lng: 91.7200,
        type: "Evacuation Centre",
        capacity: "Limited"
    }
];


// -------------------------------------------------
// MAP
// -------------------------------------------------

const map = L.map("shelterMap").setView(
    [26.1445, 91.7362],
    12
);


L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }
).addTo(map);


// -------------------------------------------------
// SHELTER MARKERS
// -------------------------------------------------

shelters.forEach((shelter) => {

    const marker = L.marker([
        shelter.lat,
        shelter.lng
    ]).addTo(map);


    marker.bindPopup(`

        <strong>${shelter.name}</strong>

        <br>

        <small>
            ${shelter.type}
        </small>

        <br>

        <small>
            Capacity: ${shelter.capacity}
        </small>

        <br><br>

        <button
            class="btn btn-success btn-sm"
            onclick="findSafeRouteTo(
                ${shelter.lat},
                ${shelter.lng}
            )">

            Get Route

        </button>

    `);

});


// -------------------------------------------------
// FIND SHELTER
// -------------------------------------------------

function findShelter() {

    alert(
        "Finding nearby safe shelters..."
    );

    map.setView(
        [26.1445, 91.7362],
        13
    );

}


// -------------------------------------------------
// FIND SAFE ROUTE
// -------------------------------------------------

function findSafeRoute() {

    alert(
        "Route calculation will use your location, " +
        "available shelter locations and hazard information."
    );

}


// -------------------------------------------------
// ROUTE TO SELECTED SHELTER
// -------------------------------------------------

function findSafeRouteTo(lat, lng) {

    alert(
        "Recommended route calculation started."
    );

    map.setView(
        [lat, lng],
        15
    );

}


// -------------------------------------------------
// RESCUE REQUEST
// -------------------------------------------------

function requestRescue() {

    const confirmed = confirm(

        "Do you need emergency rescue assistance?"

    );


    if (!confirmed) {

        return;

    }


    if (!navigator.geolocation) {

        alert(
            "Location services are not supported by this browser."
        );

        return;

    }


    navigator.geolocation.getCurrentPosition(

        (position) => {

            const latitude =
                position.coords.latitude;

            const longitude =
                position.coords.longitude;


            console.log(
                "Rescue Location:",
                latitude,
                longitude
            );


            alert(
                "Rescue request prepared with your location."
            );


            /*
                Later this will send the request
                to the LandSafe backend:

                POST /api/rescue/request

                {
                    latitude,
                    longitude,
                    riskLevel,
                    hazardType
                }
            */

        },


        () => {

            alert(
                "Please allow location access to send " +
                "your rescue location."
            );

        }

    );

}