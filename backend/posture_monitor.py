import cv2
import time
import math as m
import mediapipe as mp  # RPI3 FIX
import argparse
import json  # JSON FIX
import os    # JSON FIX
import datetime
from api.database import SessionLocal
from api.models import MetricaPostural
import logging
logger = logging.getLogger(__name__)
class PostureMonitor:
    def __init__(self,  session_id: str):
        self.mp_drawing = mp.solutions.drawing_utils
        self.session_id = session_id
        self.mp_pose = mp.solutions.pose  # RPI3 FIX
        self.args = self.parse_arguments()

        if os.path.exists("calibration.json"):
            with open("calibration.json", "r") as f:
                data = json.load(f)
                self.args.offset_threshold = data.get("offset_threshold", self.args.offset_threshold)
                self.args.neck_angle_threshold = data.get("neck_angle_threshold", self.args.neck_angle_threshold)
                self.args.torso_angle_threshold = data.get("torso_angle_threshold", self.args.torso_angle_threshold)
                self.args.time_threshold = data.get("time_threshold", self.args.time_threshold)
            print("\U0001F4E5 Umbrales cargados desde calibration.json:")  # JSON FIX
            print(f"Offset: {self.args.offset_threshold}, Neck: {self.args.neck_angle_threshold}, Torso: {self.args.torso_angle_threshold}, Tiempo: {self.args.time_threshold}")  # JSON FIX
        else:
            print("⚠️  calibration.json no encontrado. Usando valores por defecto o línea de comandos.")  # JSON FIX

        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.pose = self.mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.good_frames = 0
        self.bad_frames = 0

    def findDistance(self, x1, y1, x2, y2):
        dist = m.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return dist

    def findAngle(self, x1, y1, x2, y2):
        theta = m.acos((y2 - y1) * (-y1) / (m.sqrt((x2 - x1)**2 + (y2 - y1)**2) * y1))
        degree = int(180/m.pi) * theta
        return degree

    def sendWarning(self):
        pass

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description='Posture Monitor with MediaPipe')
        parser.add_argument('--video', type=str, default=0, help='Path to the input video file. If not provided, the webcam will be used.')
        parser.add_argument('--offset-threshold', type=float, default=100, help='Threshold value for shoulder alignment.')  # JSON FIX
        parser.add_argument('--neck-angle-threshold', type=float, default=25, help='Threshold value for neck inclination angle.')  # JSON FIX
        parser.add_argument('--torso-angle-threshold', type=float, default=10, help='Threshold value for torso inclination angle.')  # JSON FIX
        parser.add_argument('--time-threshold', type=int, default=180, help='Time threshold for triggering a posture alert.')
        return parser.parse_args()


    def emit_metrics(self, fps: float, postura: str):
            logger.debug("emit_metrics() called – fps=%s, postura=%r", fps, postura)
            total = self.good_frames + self.bad_frames or 1
            datos = {
                "actual": postura,
                "porcentaje_correcta": round(self.good_frames / total * 100, 1),
                "porcentaje_incorrecta": round(self.bad_frames / total * 100, 1),
                "transiciones_malas": self.transitions,
                "tiempo_sentado": round(self.bad_frames / fps, 1),
                "tiempo_parado": round(self.good_frames / fps, 1),
                "alertas_enviadas": self.alerts_sent,
            }
            logger.debug("Calculated metrics payload: %s", datos)

            db = SessionLocal()
            try:
                logger.debug("Opening DB session to insert metric for session_id=%s", self.sesion_id)
                nueva = MetricaPostural(
                    sesion_id=self.sesion_id,
                    timestamp=datetime.utcnow(),
                    datos=datos
                )
                db.add(nueva)
                logger.debug("Added MetricaPostural ORM object: %r", nueva)
                db.commit()
                logger.info("Committed metrics for session_id=%s", self.sesion_id)
            except Exception:
                logger.exception("Failed to emit metrics for session_id=%s", self.sesion_id)
                db.rollback()
            finally:
                db.close()
                logger.debug("Closed DB session")
    
    def process_frame(self, image):
        h, w = image.shape[:2]
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        keypoints = self.pose.process(image_rgb)
        image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        lm = keypoints.pose_landmarks
        lmPose = self.mp_pose.PoseLandmark

        if lm is None:
            return image

        r_shldr_x = int(lm.landmark[lmPose.RIGHT_SHOULDER].x * w)
        r_shldr_y = int(lm.landmark[lmPose.RIGHT_SHOULDER].y * h)
        r_ear_x = int(lm.landmark[lmPose.RIGHT_EAR].x * w)
        r_ear_y = int(lm.landmark[lmPose.RIGHT_EAR].y * h)
        r_hip_x = int(lm.landmark[lmPose.RIGHT_HIP].x * w)
        r_hip_y = int(lm.landmark[lmPose.RIGHT_HIP].y * h)

        neck_inclination = self.findAngle(r_shldr_x, r_shldr_y, r_ear_x, r_ear_y)
        torso_inclination = self.findAngle(r_hip_x, r_hip_y, r_shldr_x, r_shldr_y)

        angle_text_string_neck = 'Neck inclination: ' + str(int(neck_inclination))
        angle_text_string_torso = 'Torso inclination: ' + str(int(torso_inclination))

        if neck_inclination < self.args.neck_angle_threshold and torso_inclination < self.args.torso_angle_threshold:
            self.bad_frames = 0
            self.good_frames += 1

            color = (127, 233, 100)
        else:
            self.good_frames = 0
            self.bad_frames += 1
            color = (50, 50, 255)

        cv2.putText(image, angle_text_string_neck, (10, 30), self.font, 0.6, color, 2)
        cv2.putText(image, angle_text_string_torso, (10, 60), self.font, 0.6, color, 2)
        cv2.putText(image, str(int(neck_inclination)), (r_shldr_x + 10, r_shldr_y), self.font, 0.9, color, 2)
        cv2.putText(image, str(int(torso_inclination)), (r_hip_x + 10, r_hip_y), self.font, 0.9, color, 2)

        cv2.circle(image, (r_shldr_x, r_shldr_y), 7, (255, 255, 255), 2)
        cv2.circle(image, (r_ear_x, r_ear_y), 7, (255, 255, 255), 2)
        cv2.circle(image, (r_shldr_x, r_shldr_y - 100), 7, (255, 255, 255), 2)
        cv2.circle(image, (r_hip_x, r_hip_y), 7, (0, 255, 255), -1)
        cv2.circle(image, (r_hip_x, r_hip_y - 100), 7, (0, 255, 255), -1)

        cv2.line(image, (r_shldr_x, r_shldr_y), (r_ear_x, r_ear_y), color, 2)
        cv2.line(image, (r_shldr_x, r_shldr_y), (r_shldr_x, r_shldr_y - 100), color, 2)
        cv2.line(image, (r_hip_x, r_hip_y), (r_shldr_x, r_shldr_y), color, 2)
        cv2.line(image, (r_hip_x, r_hip_y), (r_hip_x, r_hip_y - 100), color, 2)

        fps = 15
        good_time = (1 / fps) * self.good_frames
        bad_time = (1 / fps) * self.bad_frames

        if good_time > 0:
            time_string_good = 'Good Posture Time : ' + str(round(good_time, 1)) + 's'
            cv2.putText(image, time_string_good, (10, h - 20), self.font, 0.9, (127, 255, 0), 2)
        else:
            time_string_bad = 'Bad Posture Time : ' + str(round(bad_time, 1)) + 's'
            cv2.putText(image, time_string_bad, (10, h - 20), self.font, 0.9, (50, 50, 255), 2)

        if bad_time > self.args.time_threshold:
            self.sendWarning()
        # self.emit_metrics(fps, "menton_en_mano")
        return image

    def run(self):
        cap = cv2.VideoCapture(self.args.video) if self.args.video else cv2.VideoCapture(0)

        while True:
            success, image = cap.read()
            if not success:
                print("Null.Frames")
                break

            image = self.process_frame(image)
            cv2.imshow('MediaPipe Pose', image)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()