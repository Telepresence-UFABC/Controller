const state = {
        pan: 0,
        tilt: 0,
        auto: false,
    },
    remoteVideoPlayer = document.querySelector("#remote-video-player"),
    videoPlayer = document.querySelector("#video-player"),
    websocket = new WebSocket(`ws://${SERVER_IP}:3000`);

websocket.addEventListener("open", (event) => {
    websocket.send(
        JSON.stringify({
            type: "messages",
            messages: ["pose", "interface_video", "remote_video", "auto_state"],
        })
    );
});

websocket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    switch (message.type) {
        case "pose":
            state.pan = message.pan;
            state.tilt = message.tilt;
            updateSliders(message);
            break;
        case "auto_state":
            state.auto = message.auto;
            updateAutoButton(message);
            break;
        case "remote_video":
            const remoteImg = new Image();
            remoteImg.src = "data:image/jpg;base64," + message.media;
            remoteImg.onload = function () {
                const ctx = remoteVideoPlayer.getContext("2d");
                ctx.drawImage(remoteImg, 0, 0, remoteVideoPlayer.width, remoteVideoPlayer.height);
                drawGrid(ctx, remoteVideoPlayer.width, remoteVideoPlayer.height, 32);
            };
            break;
        case "interface_video":
            const localImg = new Image();
            localImg.src = "data:image/jpg;base64," + message.media;
            localImg.onload = function () {
                const ctx = videoPlayer.getContext("2d");
                ctx.drawImage(localImg, 0, 0, videoPlayer.width, videoPlayer.height);
            };
            break;
    }
});

function drawGrid(ctx, width, height, gridSize) {
    ctx.beginPath();
    for (var x = 0; x <= width; x += gridSize) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
    }
    for (var y = 0; y <= height; y += gridSize) {
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
    }
    ctx.strokeStyle = "rgba(0, 0, 0, 0.5)";
    ctx.stroke();
}

function base64ToBlob(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/\-/g, "+").replace(/_/g, "/");
    const binaryString = window.atob(base64);
    const byteArrays = [];
    for (let i = 0; i < binaryString.length; i++) {
        byteArrays.push(binaryString.charCodeAt(i));
    }
    const byteArray = new Uint8Array(byteArrays);
    return new Blob([byteArray]);
}

// Call buttons
const auto = document.querySelector("#auto");
auto.addEventListener("change", (event) => {
    state.auto = event.target.checked;
    sendAutoState(state.auto);
});

// Servo sliders
const sliders = document.querySelectorAll('input[type="range"]');

// Event listener changes slider labels visually
sliders.forEach((slider) => {
    slider.addEventListener("input", () => {
        const label = document.getElementById(`${slider.id}-label`);
        label.innerHTML = `${slider.value}°`;
        state[slider.id] = Number(slider.value);
        sendPose();
    });
});

// Control inputs
const panInput = document.querySelector("#pan-input");
const tiltInput = document.querySelector("#tilt-input");

const confirmButton = document.querySelector("button");
confirmButton.addEventListener("click", () => {
    state.pan = panInput.value === "" ? state.pan : Number(panInput.value);
    state.tilt = tiltInput.value === "" ? state.tilt : Number(tiltInput.value);
    sendPose();
});

// Update sliders with server state
function updateSliders(message) {
    sliders.forEach((slider) => {
        slider.value = message[slider.id];
        document.getElementById(`${slider.id}-label`).innerHTML = `${slider.value}°`;
    });
}

// Update auto button with server state
function updateAutoButton(message) {
    auto.checked = message.auto;
    state.auto = message.auto;
    toggleEnable();
}

function toggleEnable() {
    sliders.forEach((slider) => {
        slider.disabled = state.auto;
    });
    panInput.disabled = state.auto;
    tiltInput.disabled = state.auto;
}

async function sendPose() {
    websocket.send(
        JSON.stringify({
            type: "manual_pose",
            pan: state.pan,
            tilt: state.tilt,
        })
    );
}

async function sendAutoState() {
    websocket.send(
        JSON.stringify({
            type: "auto_state",
            auto: state.auto,
        })
    );
    toggleEnable();
}
