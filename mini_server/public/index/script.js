const state = {
    pan: 0,
    tilt: 0,
    auto: false,
},
    remoteVideoPlayer = document.querySelector("#remote-video-player"),
    videoPlayer = document.querySelector("#video-player"),
    websocket = new WebSocket(`ws://${SERVER_IP}:3000`);

websocket.addEventListener("open", (event) => {
    websocket.send(JSON.stringify(
        {
            type: "messages",
            messages: ["pose", "video", "remote_video", "auto_state"]
        }))
})

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
            const remoteVideoBlob = base64ToBlob(message.media);
            const remoteFrameURL = URL.createObjectURL(remoteVideoBlob);
            remoteVideoPlayer.src = remoteFrameURL;
            break;
        case "video":
            const videoBlob = base64ToBlob(message.media);
            const frameURL = URL.createObjectURL(videoBlob);
            videoPlayer.src = frameURL;
            break;
    }
});

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
}
