import express from "express";
import { WebSocket, WebSocketServer } from "ws";
import { v4 } from "uuid";
import { spawn } from "child_process";
import { appendFileSync, existsSync, writeFileSync, readdir, readFile } from "fs";
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
    LOG_PATH: join(__dirname, "../logs"),
    WIDTH: 640,
    HEIGHT: 480,
    RPI_WIDTH: 320,
    RPI_HEIGHT: 240,
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
    clients[userId] = { connection, messages: [] };
    console.log("Server: Connection established");

    connection.on("close", () => handleDisconnect(userId));

    connection.on("message", function (message) {
        message = JSON.parse(message.toString());
        switch (message.type) {
            case "messages":
                clients[userId].messages = message.messages;

                distributeData({ type: "pose", pan: state.pan, tilt: state.tilt });
                distributeData({ type: "auto_state", auto: state.auto });
                break;
            case "auto_pose":
                if (state.auto) {
                    state.pan = message.pan;
                    state.tilt = message.tilt;

                    distributeData({
                        type: "pose",
                        pan: state.pan,
                        tilt: state.tilt,
                    });
                }
                break;
            case "manual_pose":
                if (!state.auto) {
                    state.pan = message.pan;
                    state.tilt = message.tilt;

                    distributeData({
                        type: "pose",
                        pan: state.pan,
                        tilt: state.tilt,
                    });
                }
                break;
            case "auto_state":
                state.auto = message.auto;

                distributeData(message);
                break;
            case "log":
                logToFile(message);
            case "video":
            case "remote_video":
                distributeData(message);
                break;
            default:
                console.log(`Unsupported message type: ${message.type}`);
                break;
        }
    });
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
function distributeData(message) {
    const data = JSON.stringify(message);
    Object.values(clients).forEach((client) => {
        if (client.connection.readyState === WebSocket.OPEN && client.messages.includes(message.type)) {
            client.connection.send(data);
        }
    });
}

function handleDisconnect(userId) {
    console.log(`${userId} disconnected.`);
    delete clients[userId];
}

function logToFile(message) {
    const path = join(SETUP.LOG_PATH, `${message.data.id}.csv`);
    const header = Object.keys(message.data).filter((k) => k !== "id");

    if (!existsSync(path)) {
        try {
            appendFileSync(path, header.join(",") + "\n");
        } catch (err) {
            console.log("Couldn't log to file");
            return;
        }
    }
    appendFile(path, header.map((k) => message.data[k]).join(",") + "\n", (err) => {
        if (err) console.log("Couldn't log to file");
    });
}

// GET

// Homepage
app.get("/", function (req, res) {
    res.render("pages/index");
});

// DataViz
app.get("/dataviz", function (req, res) {
    res.render("pages/dataviz");
});

// Log file names
app.get("/log_names", function (req, res) {
    let fileNames;
    readdir(SETUP.LOG_PATH, (err, files) => {
        fileNames = files.filter((file) => file.endsWith("csv"));
        res.json(fileNames);
    });
});

// Data from çpg file
app.get("/get_log", function (req, res) {
    const fileName = req.query.file;
    readFile(join(SETUP.LOG_PATH, fileName), (err, data) => {
        const csv = data.toString().split("\n");
        const header = csv[0].split(",");
        const parsedCsv = [];
        for (const line of csv.slice(1)) {
            const splitLine = line.split(",");
            parsedCsv.push(
                splitLine.reduce((acc, curr, i) => {
                    return { ...acc, [header[i]]: Number(curr) };
                }, {})
            );
        }
        res.json({ data: parsedCsv });
    });
});

const poseEstimation = spawn("python3", [SETUP.POSE_ESTIMATION_PROGRAM]);

poseEstimation.stderr.on("data", (data) => {
    console.log(`[POSE_ESTIMATION]: ${data}`);
});

process.on("SIGINT", () => {
    console.log("Server is killing subprocesses before terminating");
    poseEstimation.kill();
    process.exit();
});
