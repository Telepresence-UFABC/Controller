const state = {
        pan: 0,
        tilt: 0,
        fex: "N",
        auto: false,
        mic: true,
        video: true,
        volume: true,
    },
    peerConnectionConfig = {
        iceServers: [{ urls: "stun:stun.stunprotocol.org:3478" }, { urls: "stun:stun.l.google.com:19302" }],
    },
    remoteVideoPlayer = document.querySelector("#remote-video-player"),
    audioPlayer = document.querySelector("#remote-audio");
(videoPlayer = document.querySelector("#video-player")),
    (websocket = new WebSocket(`ws://${SERVER_IP}:3000`));

let localStream, peerConnection;

websocket.addEventListener("open", async (event) => {
    websocket.send(
        JSON.stringify({
            type: "messages",
            messages: ["fex", "pose", "interface_video", "remote_video", "auto_state", "rtc"],
        })
    );
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    localStream = stream;
    startConnection(true);
});

websocket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    switch (message.type) {
        case "fex":
            state.fex = message.fex;
            updateFacialExpression(message);
            break;
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
        case "rtc":
            if (!peerConnection) startConnection(false);
            const signal = message.data;
            if (signal.sdp) {
                peerConnection.setRemoteDescription(new RTCSessionDescription(signal.sdp)).then(() => {
                    if (signal.sdp.type !== "offer") return;
                    peerConnection.createAnswer().then(createdDescription);
                });
            } else if (signal.ice) {
                peerConnection.addIceCandidate(new RTCIceCandidate(signal.ice));
            }
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

function startConnection(isCaller) {
    peerConnection = new RTCPeerConnection(peerConnectionConfig);
    peerConnection.onicecandidate = (event) => {
        if (event.candidate != null) {
            websocket.send(JSON.stringify({ type: "rtc", data: { ice: event.candidate } }));
        }
    };
    peerConnection.ontrack = (event) => {
        audioPlayer.srcObject = event.streams[0];
    };

    for (const track of localStream.getTracks()) {
        peerConnection.addTrack(track, localStream);
    }

    if (isCaller) {
        peerConnection.createOffer().then(createdDescription);
    }
}

function createdDescription(description) {
    peerConnection.setLocalDescription(description).then(() => {
        websocket.send(
            JSON.stringify({
                type: "rtc",
                data: { sdp: peerConnection.localDescription },
            })
        );
    });
}

// Call buttons
const mic = document.querySelector("#mic");
mic.addEventListener("change", (event) => {
    state.mic = event.target.checked;
    localStream.getAudioTracks()[0].enabled = state.mic;
});

const auto = document.querySelector("#auto");
auto.addEventListener("change", (event) => {
    state.auto = event.target.checked;
    sendAutoState(state.auto);
});

const volume = document.querySelector("#volume");
volume.addEventListener("change", (event) => {
    state.volume = event.target.checked;
    audioPlayer.muted = !state.volume;
});

// Expression buttons
const expressionButtons = document.querySelectorAll('input[name="expression"]');
expressionButtons.forEach((button) => {
    button.addEventListener("change", () => {
        state.fex = button.value;
        sendFex();
    });
});

// Updates expression to the last value sent
function updateFacialExpression(message) {
    document.getElementById(message.fex).checked = true;
}

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
    expressionButtons.forEach((button) => {
        button.disabled = state.auto;
    });
    panInput.disabled = state.auto;
    tiltInput.disabled = state.auto;
}

async function sendFex() {
    websocket.send(
        JSON.stringify({
            type: "manual_fex",
            fex: state.fex,
        })
    );
}

async function sendPose() {
    const message = {
        type: "manual_pose",
        pan: state.pan,
        tilt: state.tilt,
    };
    websocket.send(JSON.stringify(message));
    updateSliders(message);
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
