import cv2, numpy as np
from flask import Flask, Response
from mediapipe import solutions

class Landmark:
    NOSE = 1
    LEFT_EYE = 33
    LEFT_MOUTH = 61
    CHIN = 199
    RIGHT_EYE = 263
    RIGHT_MOUTH = 291

app = Flask(__name__)

cap = cv2.VideoCapture(0)
WIDTH, HEIGHT, CHANNELS = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT), 3

mp_face_mesh = solutions.face_mesh

face_3d = np.array([            # Posição aproximada dos pontos
    (0.0, 0.0, 0.0),            # NOSE
    (0.0, -330.0, -65.0),       # CHIN
    (-225.0, 170.0, -135.0),    # LEFT_EYE
    (225.0, 170.0, -135.0),     # RIGHT_EYE
    (-150.0, -150.0, -125.0),   # LEFT_MOUTH
    (150.0, -150.0, -125.0)     # RIGHT_MOUTH
    ], dtype=np.float64)

distortion_matrix = np.zeros((4, 1 )) # No lens distortion
FOCAL_LENGTH = WIDTH
camera_matrix = np.array(
    [[FOCAL_LENGTH, 0, WIDTH/2],
     [0, FOCAL_LENGTH, HEIGHT/2],
     [0, 0, 1]], dtype=np.float64
)

@app.route("/reference")
def reference() -> dict[str, float]:
    y = 0
    with mp_face_mesh.FaceMesh() as face_mesh:
        ok, frame = cap.read()
        if not ok:
            return {"ref_pan": y}
        op = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        face_2d = []
        if op.multi_face_landmarks:
            for landmarks in op.multi_face_landmarks:
                for id, landmark in enumerate(landmarks.landmark):
                    x, y = int(landmark.x*WIDTH), int(landmark.y*HEIGHT)

                    face_2d.append((x, y))

                points_of_interest = np.array([
                    face_2d[Landmark.NOSE],
                    face_2d[Landmark.CHIN],
                    face_2d[Landmark.LEFT_EYE],
                    face_2d[Landmark.RIGHT_EYE],
                    face_2d[Landmark.LEFT_MOUTH],
                    face_2d[Landmark.RIGHT_MOUTH]
                ], dtype=np.float64)
                success, rot_vec, trans_vec = cv2.solvePnP(face_3d, points_of_interest, camera_matrix, distortion_matrix)
                rotation_matrix, jacobian = cv2.Rodrigues(rot_vec)
                angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rotation_matrix)
                x = angles[0]-np.sign(angles[0])*180
                y = angles[1]
                z = angles[2]
        return {"ref_pan": y}


if __name__ == "__main__":
    app.run(port=8080)
