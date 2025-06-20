# scripts/camera_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import cv2
import numpy as np
import tensorflow as tf
import time

from scripts.mediapipe_utils import (
    get_holistic_model, mediapipe_detection,
    draw_styled_landmarks, extract_keypoints
)

class CameraThread(QThread):
    frame_updated = pyqtSignal(QImage)
    camera_ready = pyqtSignal()
    detected_label = pyqtSignal(str)

    def __init__(self, camera_id, use_mediapipe=True):
        super().__init__()
        self.camera_id = camera_id
        self.use_mediapipe = use_mediapipe
        self.running = False

        self.sequence = []
        if self.use_mediapipe:
            self.model = tf.keras.models.load_model("models/deslr_18c.h5")
            self.actions = [
                'hello', 'thank', 'recommended', 'one', 'nee', 'tangmod', 'tawlai',
                'sweet', 'no', 'less', 'normal', 'zero', 'cocoa', 'tea',
                'green', 'thai', 'americano', 'latte'
            ]
            self.threshold = 0.9
            self.last_prediction = None
            self.repeat_count = 0
            self.repeat_target = 5
            self.cooldown_start = None
            self.cooldown_seconds = 5

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(self.camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

        if cap.isOpened():
            self.camera_ready.emit()

        if self.use_mediapipe:
            with get_holistic_model() as holistic:
                while self.running:
                    ret, frame = cap.read()
                    if not ret:
                        continue

                    image, results = mediapipe_detection(frame, holistic)
                    draw_styled_landmarks(image, results)

                    if results.face_landmarks and (results.left_hand_landmarks or results.right_hand_landmarks):
                        keypoints = extract_keypoints(results)
                        self.sequence.append(keypoints)
                        self.sequence = self.sequence[-30:]
                    else:
                        self.send_frame(image)
                        continue

                    if len(self.sequence) == 30:
                        res = self.model.predict(np.expand_dims(self.sequence, axis=0), verbose=0)[0]
                        top_idx = np.argmax(res)
                        top_label = self.actions[top_idx]
                        confidence = res[top_idx]

                        if confidence > self.threshold:
                            if top_label == self.last_prediction:
                                self.repeat_count += 1
                            else:
                                self.repeat_count = 1
                                self.last_prediction = top_label

                            current_time = time.time()
                            if self.cooldown_start and current_time - self.cooldown_start < self.cooldown_seconds:
                                self.send_frame(image)
                                continue
                            else:
                                self.cooldown_start = None

                            if self.repeat_count == self.repeat_target:
                                print(f"Detected: {top_label}")
                                self.detected_label.emit(top_label)
                                self.cooldown_start = time.time()
                                self.repeat_count = 0
                                self.last_prediction = None
                                self.sequence = []

                    self.send_frame(image)
        else:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    continue
                self.send_frame(frame)

        cap.release()

    def send_frame(self, image):
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.frame_updated.emit(qt_image)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()
