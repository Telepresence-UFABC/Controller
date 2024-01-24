import json, cv2, base64, time, numpy as np
from websockets.sync.client import connect
from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosedError
from os.path import join, abspath
from mediapipe import solutions
from json import dumps

with open(
    abspath(join(__file__, "../../public/server_setup/setup.json")),
    "r",
) as file:
    SETUP: dict = json.load(file)
    SERVER_IP: str = SETUP["SERVER_IP"]
    WIDTH: int = SETUP["WIDTH"]
    HEIGHT: int = SETUP["HEIGHT"]


class Landmark:
    NOSE = 1
    LEFT_EYE = 33
    LEFT_MOUTH = 61
    CHIN = 199
    RIGHT_EYE = 263
    RIGHT_MOUTH = 291

pan = 150
tilt = 150
z = 0
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
mp_face_mesh = solutions.face_mesh
draw = solutions.drawing_utils
drawing_spec = draw.DrawingSpec(color=(0, 255, 0), circle_radius=1, thickness=1)

face_3d = np.array(
    [  # Posição aproximada dos pontos
        (0.0, 0.0, 0.0),  # NOSE
        (0.0, -200.0, -65.0),  # CHIN
        (-150.0, 170.0, -135.0),  # LEFT_EYE
        (150.0, 170.0, -135.0),  # RIGHT_EYE
        (-150.0, -150.0, -125.0),  # LEFT_MOUTH
        (150.0, -150.0, -125.0),  # RIGHT_MOUTH
    ],
    dtype=np.float64,
)

distortion_matrix = np.zeros((4, 1))  # No lens distortion
FOCAL_LENGTH = WIDTH
camera_matrix = np.array(
    [[FOCAL_LENGTH, 0, WIDTH / 2], [0, FOCAL_LENGTH, HEIGHT / 2], [0, 0, 1]],
    dtype=np.float64,
)

while True:
    try:
        with connect(f"ws://{SERVER_IP}:3000") as websocket:
            with mp_face_mesh.FaceMesh() as face_mesh:
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        continue
                    op = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    face_2d = []
                    if op.multi_face_landmarks:
                        for landmarks in op.multi_face_landmarks:
                            for landmark in landmarks.landmark:
                                x, y = int(landmark.x * WIDTH), int(landmark.y * HEIGHT)
                                face_2d.append((x, y))

                            projection = np.array(
                                [
                                    face_2d[Landmark.NOSE],
                                    face_2d[Landmark.CHIN],
                                    face_2d[Landmark.LEFT_EYE],
                                    face_2d[Landmark.RIGHT_EYE],
                                    face_2d[Landmark.LEFT_MOUTH],
                                    face_2d[Landmark.RIGHT_MOUTH],
                                ],
                                dtype=np.float64,
                            )
                            success, rot_vec, trans_vec = cv2.solvePnP(
                                face_3d, projection, camera_matrix, distortion_matrix
                            )
                            rotation_matrix, jacobian = cv2.Rodrigues(rot_vec)
                            angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(
                                rotation_matrix
                            )
                            tilt = int(angles[0] + (330 if angles[0] < 0 else -30))
                            pan = int(angles[1]) + 150
                            z = int(angles[2])

                    websocket.send(
                        dumps({"type": "auto_pose", "pan": pan, "tilt": tilt})
                    )

                    cv2.putText(
                        frame,
                        f"pan: {str(np.round(pan,2))}",
                        (0, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2,
                    )
                    cv2.putText(
                        frame,
                        f"tilt: {str(np.round(tilt,2))}",
                        (0, 100),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2,
                    )
                    cv2.putText(
                        frame,
                        f"yaw: {str(np.round(z,2))}",
                        (0, 150),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2,
                    )
                    draw.draw_landmarks(
                        frame,
                        landmarks,
                        mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=drawing_spec,
                    )
                    ok, video_buffer = cv2.imencode(".jpg", frame)
                    frame = base64.b64encode(video_buffer).decode("utf-8")

                    websocket.send(json.dumps({"type": "video", "media": frame}))

    except (InvalidURI, OSError, InvalidHandshake, ConnectionClosedError) as e:
        print(f"Could not connect to server, error: {e}")
        time.sleep(2)
