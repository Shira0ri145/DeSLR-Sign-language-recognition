# scripts/camera_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtCore import Qt
import cv2

class CameraThread(QThread):
    frame_updated = pyqtSignal(QImage)
    camera_ready = pyqtSignal()

    def __init__(self, camera_id=0):
        super().__init__()
        self.camera_id = camera_id
        self.running = False  # 🔁 default เป็น False ก่อน start

    def run(self):
        self.running = True  # ✅ เริ่ม run จริง
        cap = cv2.VideoCapture(self.camera_id)
        if cap.isOpened():
            self.camera_ready.emit()
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            scaled = qt_image.scaled(280, 180, Qt.KeepAspectRatio)
            self.frame_updated.emit(scaled)
        cap.release()

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

