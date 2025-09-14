# scripts/camera_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import cv2
import time


class CameraThread(QThread):
    frame_updated = pyqtSignal(QImage)  # ส่งเฟรมรูปภาพไปให้ UI
    camera_ready = pyqtSignal()         # แจ้งว่าเปิดกล้องพร้อมแล้ว

    def __init__(self, camera_id=0):
        """
        เหลือแค่เปิดกล้อง/ส่งเฟรมเท่านั้น
        พารามิเตอร์ use_mediapipe ยังรับไว้แต่ 'ไม่ถูกใช้' เพื่อไม่ให้โค้ดเดิมพัง
        """
        super().__init__()
        self.camera_id = camera_id
        self.running = False
        self.cap = None

    def run(self):
        self.running = True

        # พยายามเปิดกล้อง
        # ถ้าอยู่บน Windows แนะนำ CAP_DSHOW จะติดง่ายขึ้น
        # ถ้าไม่ใช้ Windows สามารถปล่อยเป็นค่าเริ่มต้นได้ก็ได้
        try:
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        except Exception:
            self.cap = cv2.VideoCapture(self.camera_id)

        # ตั้งความละเอียดพื้นฐาน (ปรับได้ตามต้องการ)
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

        if self.cap is not None and self.cap.isOpened():
            self.camera_ready.emit()
        else:
            # เปิดไม่ติด ก็จบเงียบ ๆ (ป้องกันแอปค้าง)
            self.running = False
            return

        # วนอ่านเฟรมจนกว่าจะถูกสั่ง stop()
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            self.send_frame(frame)
            # ผ่อน CPU นิดนึง
            time.sleep(0.001)

        # ออกจากลูป: ปล่อยกล้อง
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        self.cap = None

    def send_frame(self, bgr_image):
        """แปลง BGR -> QImage แล้ว emit ออกไป"""
        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        # copy() เพื่อกัน data pointer หายเมื่อออกจากฟังก์ชัน
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        self.frame_updated.emit(qimg)

    def stop(self):
        """เรียกจาก UI ตอนต้องการปิดกล้อง"""
        self.running = False
        self.quit()
        self.wait()
