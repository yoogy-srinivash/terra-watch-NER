const sirenButton = document.getElementById("sirenButton");
const emergencySirenButton = document.getElementById("emergencySirenButton");

const sirenStatus = document.getElementById("sirenStatus");
const monitoringSirenStatus = document.getElementById("monitoringSirenStatus");

// Create audio object
const sirenAudio = new Audio("siren.mp3");
sirenAudio.loop = true;

// Web Audio API Synthesized Siren Fallback
let audioCtx = null;
let osc1 = null;
let osc2 = null;
let sirenLfo = null;
let isSynthesizedPlaying = false;

function startSyntheticSiren() {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        if (!audioCtx) audioCtx = new AudioContext();
        if (audioCtx.state === "suspended") audioCtx.resume();

        const now = audioCtx.currentTime;
        const masterGain = audioCtx.createGain();
        masterGain.gain.setValueAtTime(0.25, now);
        masterGain.connect(audioCtx.destination);

        // Modulating LFO (warble effect 0.5Hz between 550Hz and 850Hz)
        sirenLfo = audioCtx.createOscillator();
        const lfoGain = audioCtx.createGain();
        sirenLfo.frequency.setValueAtTime(0.45, now);
        lfoGain.gain.setValueAtTime(150, now);

        osc1 = audioCtx.createOscillator();
        osc1.type = "sawtooth";
        osc1.frequency.setValueAtTime(700, now);

        sirenLfo.connect(lfoGain);
        lfoGain.connect(osc1.frequency);

        osc1.connect(masterGain);
        sirenLfo.start();
        osc1.start();
        isSynthesizedPlaying = true;
    } catch (e) {
        console.warn("Could not start Web Audio siren:", e);
    }
}

function stopSyntheticSiren() {
    if (isSynthesizedPlaying) {
        try {
            if (osc1) osc1.stop();
            if (sirenLfo) sirenLfo.stop();
            osc1 = null;
            sirenLfo = null;
            isSynthesizedPlaying = false;
        } catch (e) {}
    }
}

// ===============================
// ACTIVATE / STOP SIREN
// ===============================

function toggleSiren() {
    const isPlaying = !sirenAudio.paused || isSynthesizedPlaying;

    if (!isPlaying) {
        // Trigger backend siren state
        if (window.LandSafeAPI) {
            window.LandSafeAPI.triggerSiren("Guwahati, Assam", 60).catch(() => {});
        }

        sirenAudio.play()
            .then(() => {
                updateSirenUI(true);
            })
            .catch(() => {
                // Fallback to Web Audio synthesized tone
                startSyntheticSiren();
                updateSirenUI(true);
            });
    } else {
        // Stop backend siren state
        if (window.LandSafeAPI) {
            window.LandSafeAPI.stopSiren().catch(() => {});
        }

        sirenAudio.pause();
        sirenAudio.currentTime = 0;
        stopSyntheticSiren();
        updateSirenUI(false);
    }
}

// ===============================
// UPDATE UI
// ===============================

function updateSirenUI(isActive) {
    if (isActive) {
        if (sirenStatus) {
            sirenStatus.textContent = "Siren ON";
            sirenStatus.className = "badge text-bg-danger fs-6 mb-2";
        }
        if (sirenButton) {
            sirenButton.innerHTML = '<i class="bi bi-volume-mute-fill me-2"></i> Stop Siren';
        }
        if (emergencySirenButton) {
            emergencySirenButton.innerHTML = '<i class="bi bi-volume-mute-fill me-2"></i> Stop Emergency Siren';
            emergencySirenButton.className = "btn btn-outline-danger";
        }
        if (monitoringSirenStatus) {
            monitoringSirenStatus.textContent = "ON";
            monitoringSirenStatus.className = "badge text-bg-danger";
        }
    } else {
        if (sirenStatus) {
            sirenStatus.textContent = "Siren OFF";
            sirenStatus.className = "badge text-bg-secondary fs-6 mb-2";
        }
        if (sirenButton) {
            sirenButton.innerHTML = '<i class="bi bi-volume-up-fill me-2"></i> Activate Siren';
        }
        if (emergencySirenButton) {
            emergencySirenButton.innerHTML = '<i class="bi bi-megaphone-fill me-2"></i> Play Emergency Siren';
            emergencySirenButton.className = "btn btn-danger";
        }
        if (monitoringSirenStatus) {
            monitoringSirenStatus.textContent = "OFF";
            monitoringSirenStatus.className = "badge text-bg-secondary";
        }
    }
}

// ===============================
// BUTTON EVENTS
// ===============================

if (sirenButton) sirenButton.addEventListener("click", toggleSiren);
if (emergencySirenButton) emergencySirenButton.addEventListener("click", toggleSiren);

window.addEventListener("beforeunload", () => {
    sirenAudio.pause();
    sirenAudio.currentTime = 0;
    stopSyntheticSiren();
});
