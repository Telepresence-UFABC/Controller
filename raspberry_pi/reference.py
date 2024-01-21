import os, cv2, numpy as np
from threading import Thread
from flask import Flask, request
from mediapipe import solutions
from json import loads
from os.path import join, abspath

app = Flask(__name__)
ref_pan = 150
ref_tilt = 0


def get_reference_from_face():
    global ref_pan
    global ref_tilt

    class Landmark:
        NOSE = 1
        LEFT_EYE = 33
        LEFT_MOUTH = 61
        CHIN = 199
        RIGHT_EYE = 263
        RIGHT_MOUTH = 291

    cap = cv2.VideoCapture(0)
    WIDTH, HEIGHT = (
        cap.get(cv2.CAP_PROP_FRAME_WIDTH),
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
    )

    mp_face_mesh = solutions.face_mesh

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

    with mp_face_mesh.FaceMesh() as face_mesh:
        while True:
            ok, frame = cap.read()
            if not ok:
                return {"ref_pan": y}
            op = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            face_2d = []
            if op.multi_face_landmarks:
                for landmarks in op.multi_face_landmarks:
                    for id, landmark in enumerate(landmarks.landmark):
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
                    angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rotation_matrix)
                    ref_tilt = angles[0] if angles[0] >= 0 else angles[0] + 360
                    ref_pan = angles[1] + 150
                    z = angles[2]


@app.route("/reference")
def reference() -> dict[str, float]:
    print(ref_pan)
    return {"ref_pan": ref_pan}


@app.route("/log", methods=["POST"])
def log():
    try:
        body: dict[str, float] = loads(request.data)
        file_name = abspath(join(__file__, f"../../logs/{body['id']}.csv"))
        header = ",".join([key for key in body.keys() if key != "id"]) + "\n"
        data = ",".join([str(v) for k, v in body.items() if k != "id"]) + "\n"
        if not os.path.isfile(file_name):
            with open(file_name, "w+") as file:
                file.write(header)
        with open(file_name, "a") as file:
            file.write(data)
        return {"status": "ok"}
    except Exception as e:
        print(e)
        return {"status": "nok"}


if __name__ == "__main__":
    reference_thread = Thread(target=get_reference_from_face)
    reference_thread.start()
    app.run(host="192.168.0.100", port=8080)
