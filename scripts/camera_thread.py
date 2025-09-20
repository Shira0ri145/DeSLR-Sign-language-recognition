# scripts/camera_thread.py
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import cv2
import time
import numpy as np

from scripts.mediapipe_utils import (
    get_holistic_model, mediapipe_detection,
    draw_styled_landmarks, extract_keypoints
)

class CameraThread(QThread):
    frame_updated = pyqtSignal(QImage)     # ส่งเฟรมไป UI
    camera_ready  = pyqtSignal()           # แจ้งกล้องพร้อม
    detected_label = pyqtSignal(str)       # (ยังคงไว้ให้เผื่อ UI ใช้)

    def __init__(self, camera_id=0, draw_landmarks=True, threshold=0.90, seq_len=25):
        super().__init__()
        self.camera_id = camera_id
        self.draw_landmarks = draw_landmarks
        self.threshold = float(threshold)
        self.seq_len = int(seq_len)

        self.running = False
        self.cap = None

        # --- Model & labels ---
        # NOTE: ถ้าโมเดลคุณคาดรูปแบบ keypoints แบบ pose+มือ (258 มิติ)
        # ให้ ensure ว่า extract_keypoints() คืนค่ารูปแบบนั้น
        import tensorflow as tf
        self.model = tf.keras.models.load_model("models/deslr_11cass.h5")
        self.actions = [
            'hello', 'thank','recommended' ,'onenee',
            'iced', 'hot',
            'cocoa', 'greentea', 'thaitea', 'americano', 'latte'
        ]

        # --- Sequence buffer & gating states ---
        self.sequence: list[np.ndarray] = []   # เก็บ keypoints เฟรมล่าสุด
        self.armed = False                     # จะทายได้ก็ต่อเมื่อ "เห็นมือ" เพื่อสั่ง arm
        self.cooldown_until = 0.0              # หยุดทายจนกว่าจะพ้นเวลานี้
        self._countdown_last_tick = 0          # สำหรับพิมพ์ 3..2..1 โดยไม่บล็อค

        # optional: กันเด้งทายซ้ำเดิมถี่ๆ
        self._last_label = None
        self._stable_hits = 0
        self._stable_target = 1   # ถ้าอยากให้เสถียรกว่าเดิม ค่อยเพิ่มเป็น 2

    # ---------------- Core thread ----------------
    def run(self):
        self.running = True

        # เปิดกล้อง
        try:
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_V4L2)
        except Exception:
            self.cap = cv2.VideoCapture(self.camera_id)

        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

        if self.cap is None or not self.cap.isOpened():
            self.running = False
            return

        self.camera_ready.emit()

        # ใช้ mediapipe holistic
        with get_holistic_model() as holistic:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                # ประมวลผล mediapipe
                image_bgr, results = mediapipe_detection(frame, holistic)

                # วาดแลนด์มาร์กถ้าต้องการ
                if self.draw_landmarks:
                    try:
                        draw_styled_landmarks(image_bgr, results)
                    except Exception as e:
                        # กันพลาดเฉยๆ ไม่ให้ล้มทั้งเธรด
                        print("[draw] error:", e)

                # เงื่อนไข "ต้องเห็นมือซ้ายหรือขวา" จึงจะ "arm" สำหรับเริ่ม prediction
                hands_present = bool(results.left_hand_landmarks or results.right_hand_landmarks)
                if hands_present and not self.armed and time.time() >= self.cooldown_until:
                    # arm ใหม่เมื่อเห็นมือ (และไม่อยู่ในช่วง cooldown)
                    self.armed = True
                    self.sequence.clear()
                    self._last_label = None
                    self._stable_hits = 0
                    # print("[STATE] armed")

                # หากไม่เห็นมือ ให้ถอด arm และล้าง sequence
                if not hands_present:
                    self.armed = False
                    self.sequence.clear()

                # สร้าง keypoints (ใส่ศูนย์ให้ส่วนที่ไม่มี)
                try:
                    keypoints = extract_keypoints(results)  # np.ndarray
                except Exception as e:
                    keypoints = None
                    print("[extract_keypoints] error:", e)

                # ระหว่าง cooldown: พิมพ์ countdown 3..2..1 แบบไม่บล็อค
                now = time.time()
                if now < self.cooldown_until:
                    remaining = int(round(self.cooldown_until - now))
                    # พิมพ์แค่เมื่อเลขเปลี่ยน เพื่อลดสแปม
                    if remaining != self._countdown_last_tick and remaining > 0:
                        print(f"[COUNTDOWN] {remaining}…")
                        self._countdown_last_tick = remaining
                    # ยังส่งภาพให้ UI ดู
                    self.send_frame(image_bgr)
                    continue
                else:
                    # พ้น cooldown แล้ว รีเซ็ต tick
                    self._countdown_last_tick = 0

                # ถ้า arm อยู่และมี keypoints: เก็บเข้า sequence
                if self.armed and keypoints is not None:
                    self.sequence.append(keypoints.astype(np.float32))
                    if len(self.sequence) > self.seq_len:
                        self.sequence = self.sequence[-self.seq_len:]

                    # ถ้า sequence ครบตามที่โมเดลต้องการ ให้ทำนาย
                    if len(self.sequence) == self.seq_len:
                        try:
                            inp = np.expand_dims(self.sequence, axis=0)  # (1, T, D)
                            res = self.model.predict(inp, verbose=0)[0]
                            top_idx = int(np.argmax(res))
                            top_label = self.actions[top_idx]
                            conf = float(res[top_idx])
                        except Exception as e:
                            print("[model.predict] error:", e)
                            # ล้างเพื่อเริ่มใหม่ (กันค้าง)
                            self.sequence.clear()
                            self.send_frame(image_bgr)
                            continue

                        # เช็คความเชื่อมั่น
                        if conf >= self.threshold:
                            # เสถียรนิดหน่อย: ต้องติดกันบางจำนวน
                            if top_label == self._last_label:
                                self._stable_hits += 1
                            else:
                                self._last_label = top_label
                                self._stable_hits = 1

                            if self._stable_hits >= self._stable_target:
                                # >>>>>> RESULT ACCEPTED
                                print(f"[PREDICT] {top_label}  (conf={conf:.2f})")

                                # เผื่อ UI อื่นใช้งาน
                                try:
                                    self.detected_label.emit(top_label)
                                except Exception:
                                    pass

                                # เริ่ม cooldown 3 วิ และรอ “เห็นมือใหม่” เพื่อ arm รอบถัดไป
                                self.cooldown_until = time.time() + 3.0
                                self.armed = False
                                self.sequence.clear()
                                self._last_label = None
                                self._stable_hits = 0
                        else:
                            # ความเชื่อมั่นต่ำ: ค่อยๆ slide window ต่อไป
                            pass

                # ส่งภาพให้ UI ทุกลูป
                self.send_frame(image_bgr)
                time.sleep(0.001)

        # cleanup
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        self.cap = None

    # ---------------- utils ----------------
    def send_frame(self, bgr_image):
        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
        self.frame_updated.emit(qimg)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()
