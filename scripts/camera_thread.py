# scripts/camera_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtCore import Qt
import cv2
import time

class CameraThread(QThread):
    frame_updated = pyqtSignal(QImage)
    camera_ready = pyqtSignal()

    def __init__(self, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self.running = False  # 🔁 default เป็น False ก่อน start

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)

        if cap.isOpened():
            self.camera_ready.emit()

        # ✅ บังคับกล้องให้ใช้ความละเอียด Full HD
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            self.frame_updated.emit(qt_image)  # ✅ ไม่ scale
        cap.release()


    def stop(self):
        self.running = False
        self.quit()
        self.wait()

