import express from "express";
import { WebSocket, WebSocketServer } from "ws";
import { v4 } from "uuid";
import { spawn } from "child_process";
import { writeFileSync } from "fs";
import { networkInterfaces } from "os";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const interfaces = networkInterfaces();
const ip = Object.keys(interfaces).reduce((result, name) => {
    const addresses = interfaces[name]
        .filter((net) => net.family === "IPv4" && !net.internal)
        .map((net) => net.address);
    return addresses.length ? addresses[0] : result;
});

const app = express();
const port = 3000;

const SETUP = {
    SERVER_IP: ip,
    POSE_ESTIMATION_PROGRAM: join(__dirname, "pose_estimation/pose_estimation.py"),
    WIDTH: 640,
    HEIGHT: 480,
};

const state = {
    pan: 0,
    tilt: 0,
    auto: true,
};

// writes to setup.json
writeFileSync(join(__dirname, "public/server_setup/setup.json"), JSON.stringify(SETUP, null, 4));

// updates setup.js
writeFileSync(
    join(__dirname, "public/frontend_setup/setup.js"),
    Object.entries(SETUP).reduce(
        (acc, [k, v]) => acc + `const ${k} = ${typeof v === "number" ? String(v) : `"${v}"`} \n`,
        ""
    )
);

// Middleware
app.set("view engine", "ejs");
app.use([express.json(), express.static("public")]);

// Configuracao de servidor websocket na mesma porta do servidor web
const wsServer = new WebSocketServer({ noServer: true });

const server = app.listen(port);

// Handling de request do servidor soquete
wsServer.on("connection", function (connection) {
    const userId = v4();
    clients[userId] = connection;
    console.log("Server: Connection established");

    connection.on("close", () => handleDisconnect(userId));

    connection.on("message", function (message) {
        message = JSON.parse(message.toString());
        switch (message.type) {
            case "auto_pose":
                if (state.auto) {
                    console.log(message);

                    state.pan = message.pan;
                    state.tilt = message.tilt;

                    distributeData(message);
                }
                break;
            case "manual_pose":
                if (!state.auto) {
                    console.log(message);

                    state.pan = message.pan;
                    state.tilt = message.tilt;

                    distributeData(message);
                }
                break;
            case "auto_state":
                console.log(message);

                state.auto = message.auto;

                distributeData(message);
                break;
            case "video":
                distributeData(message);
                break;
            default:
                console.log(`Unsupported message type: ${message.type}`);
                break;
        }
    });

    distributeData({ type: "pose", pan: state.pan, tilt: state.tilt });
    distributeData({ type: "auto_state", auto: state.auto });
});

// Mudanca de protocolo de http para ws
server.on("upgrade", (req, socket, head) => {
    wsServer.handleUpgrade(req, socket, head, (ws) => {
        wsServer.emit("connection", ws, req);
    });
});

// clients = todos usuarios conectados ao servidor ws
const clients = {};

// envia um arquivo json para todos os usuarios conectados ao servidor ws
function distributeData(json) {
    const data = JSON.stringify(json);
    Object.values(clients).forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(data);
        }
    });
}

function handleDisconnect(userId) {
    console.log(`${userId} disconnected.`);
    delete clients[userId];
}

// GET

// Homepage
app.get("/", function (req, res) {
    res.render("pages/index");
});

const poseEstimation = spawn("python3", [SETUP.POSE_ESTIMATION_PROGRAM]);

process.on("SIGINT", () => {
    console.log("Server is killing subprocesses before terminating");
    poseEstimation.kill();
    process.exit();
});
