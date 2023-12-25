import cv2, numpy as np
from mediapipe import solutions

class Landmark:
    NOSE = 1
    LEFT_EYE = 33
    LEFT_MOUTH = 61
    CHIN = 199
    RIGHT_EYE = 263
    RIGHT_MOUTH = 291

cap = cv2.VideoCapture(0)
WIDTH, HEIGHT, CHANNELS = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT), 3
mp_face_mesh = solutions.face_mesh
draw = solutions.drawing_utils
drawing_spec = draw.DrawingSpec(color=(0, 255, 0), circle_radius=1, thickness=1)

# Estima os ângulos nos eixos de rotação x, y e z
# adaptado de https://github.com/niconielsen32/ComputerVision/blob/master/headPoseEstimation.py e de https://stackoverflow.com/questions/69039324/head-pose-estimation-using-facial-landmarks

face_3d = np.array([            # Posição aproximada dos pontos
    (0.0, 0.0, 0.0),            # NOSE
    (0.0, -200.0, -65.0),       # CHIN
    (-150.0, 170.0, -135.0),    # LEFT_EYE
    (150.0, 170.0, -135.0),     # RIGHT_EYE
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
dist = []
with mp_face_mesh.FaceMesh() as face_mesh:
    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        op = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)) # modelo treinado com imagens no formato RGB
        face_2d = []
        if op.multi_face_landmarks:
            for landmarks in op.multi_face_landmarks: # op.multi_face_landmarks é uma lista que contém n listas de pontos (para n pessoas detectadas)
                for id, landmark in enumerate(landmarks.landmark):
                    # if id == Landmark.NOSE:
                    #     nose_2d = landmark.x*WIDTH, landmark.y*HEIGHT
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

                # max_XY = max(face_2d, key=lambda p: p[0])[0], max(face_2d, key=lambda p: p[1])[1]
                # min_XY = min(face_2d, key=lambda p: p[0])[0], min(face_2d, key=lambda p: p[1])[1]

                # xcenter = (max_XY[0] + min_XY[0]) / 2
                # ycenter = (max_XY[1] + min_XY[1]) / 2

                # dist.append((int(((xcenter-WIDTH/2)**2+(ycenter-HEIGHT/2)**2)**0.4), max_XY, min_XY))
                
                success, rot_vec, trans_vec = cv2.solvePnP(face_3d, points_of_interest, camera_matrix, distortion_matrix)
                rotation_matrix, jacobian = cv2.Rodrigues(rot_vec)
                angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rotation_matrix)
                x = angles[0]-np.sign(angles[0])*180
                y = angles[1]
                z = angles[2]
                
                cv2.putText(frame, f"x: {str(np.round(x,2))}", (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(frame, f"y: {str(np.round(y,2))}", (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(frame, f"z: {str(np.round(z,2))}", (0, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                draw.draw_landmarks(frame, landmarks, mp_face_mesh.FACEMESH_CONTOURS, landmark_drawing_spec=drawing_spec)
        cv2.imshow("Video", frame)
        if cv2.waitKey(1) == 27:
            cv2.destroyAllWindows()
            break