// --------Codigo--------
// Felicidade = F
// Neutro = N
// Duvida = D
// Surpresa = S

const state = {
        volume: false,
        prevExpression: "N",
    },
    peerConnectionConfig = {
        iceServers: [{ urls: "stun:stun.stunprotocol.org:3478" }, { urls: "stun:stun.l.google.com:19302" }],
    },
    videoPlayer = document.querySelector("#video-player"),
    audioPlayer = document.querySelector("#audio-player"),
    websocket = new WebSocket(`ws://${SERVER_IP}:3000`);

websocket.addEventListener("open", async (event) => {
    websocket.send(
        JSON.stringify({
            type: "messages",
            messages: ["fex", "rtc"],
        })
    );
    const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
    });

    localStream = stream;
    startConnection(true);
});

websocket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    switch (message.type) {
        case "fex":
            if (message.fex != state.prevExpression) {
                videoPlayer.src = `/videos/cut/${state.prevExpression}${message.fex}.mp4`;
                console.log(state.prevExpression + message.fex);
                state.prevExpression = message.fex;
                videoPlayer.play();
            }
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

const audio = document.querySelector("#audio-toggle");
audio.addEventListener("click", (event) => {
    state.volume = !state.volume;
    audioPlayer.muted = !state.volume;
    audio.src = state.volume ? "/img/volume_off.svg" : "/img/volume_on.svg";
});
