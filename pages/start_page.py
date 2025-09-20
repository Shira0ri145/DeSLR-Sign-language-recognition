# pages/start_page.py

from PyQt5.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QSizePolicy, QLineEdit, QScrollArea, QMessageBox, QMenu
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import qtawesome as qta
import sip  # type: ignore

from concurrent.futures import ThreadPoolExecutor  # ⬅️ เพิ่มสำหรับงาน TTS แบบไม่บล็อก
from scripts.camera_thread import CameraThread
from scripts.order_generator import generate_order, validate_tokens
# from scripts.pyttsx import speak as tts_speak  # ⬅️ ย้ายไปใช้ generate_tts แทน
from scripts.generate_tts import generate_tts_from_text  # ⬅️ ใช้ F5-TTS ผ่าน playsound

# ⬇️ ป๊อปอัปเมนู
from pages.menu_dialog import MenuDialog


class StartPage(QWidget):
    def __init__(self, on_back):
        super().__init__()
        self.on_back = on_back

        self.is_camera_on = False
        self.camera_thread = None
        self._bubbles = []
        self._last_sender = None

        # เก็บลิสต์คำที่ตรวจพบ จากสัญญาณ CameraThread.detected_label
        self._detected_tokens = []

        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop)

        # --- Header + Back ---
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignLeft)
        header_layout.setSpacing(10)

        title_label = QLabel('<span style="color: white;">De</span><span style="color: #C2FCEA;">SLR</span>')
        title_label.setObjectName("mainTitle")
        title_label.setTextFormat(Qt.RichText)

        subtitle_label = QLabel(
            '<span style="color: white;">ยินดีต้อนรับเข้าสู่ </span>'
            '<span style="color: #C2FCEA;">ร้านคาเฟ่ที่เงียบ แต่ล้นไปด้วยสุข !</span>'
        )
        subtitle_label.setObjectName("subTitle")
        subtitle_label.setTextFormat(Qt.RichText)
        subtitle_label.setAlignment(Qt.AlignCenter)

        back_btn = QPushButton(qta.icon("fa5s.arrow-left"), "ย้อนกลับ")
        back_btn.setObjectName("backButton")
        back_btn.setFixedHeight(36)
        back_btn.setToolTip("กลับไปหน้าแรก")
        back_btn.clicked.connect(self.on_back_button_click)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.addStretch(1)
        header_layout.addWidget(back_btn, 0, Qt.AlignRight)
        main_layout.addLayout(header_layout)

        # --- Content split (Left: Chat / Right: Camera) ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 20, 0, 0)
        content_layout.setSpacing(20)

        # ===================== Left: Chat frame =====================
        chat_frame = QFrame()
        chat_frame.setObjectName("chatFrame")
        chat_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        chat_outer = QVBoxLayout(chat_frame)
        chat_outer.setContentsMargins(16, 16, 16, 12)
        chat_outer.setSpacing(12)

        # แถวหัวข้อ + ปุ่มเมนู
        chat_title_row = QHBoxLayout()
        chat_title = QLabel("แชท")
        chat_title.setObjectName("chatTitle")

        self.menu_btn = QPushButton(qta.icon("fa5s.bars"), "เมนู")
        self.menu_btn.setObjectName("menuButton")
        self.menu_btn.setFixedHeight(32)
        self.menu_btn.setToolTip("เปิดเมนูเครื่องดื่ม")
        self.menu_btn.clicked.connect(self.open_menu_popup)

        chat_title_row.addWidget(chat_title)
        chat_title_row.addStretch(1)
        chat_title_row.addWidget(self.menu_btn)
        chat_outer.addLayout(chat_title_row)

        # Scrollable chat area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setObjectName("chatScroll")
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_vbox = QVBoxLayout(self.chat_container)
        self.chat_vbox.setContentsMargins(8, 8, 8, 8)
        self.chat_vbox.setSpacing(10)
        self.chat_vbox.addStretch(1)

        self.chat_scroll.setWidget(self.chat_container)
        chat_outer.addWidget(self.chat_scroll)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_edit = QLineEdit()
        self.input_edit.setObjectName("chatInput")
        self.input_edit.setPlaceholderText("พิมพ์ข้อความที่นี่…")
        # Enter -> ส่งเป็นฝั่ง "ลูกค้า"
        self.input_edit.returnPressed.connect(lambda: self.send_message(sender="user"))

        # ปุ่ม "ถามด่วน" (Quick ask) -> popup เมนูคำถามสำเร็จรูป
        self.quick_btn = QPushButton(qta.icon("fa5s.comment-dots"), "")
        self.quick_btn.setObjectName("quickAskButton")
        self.quick_btn.setToolTip("คำถามสำเร็จรูป (user)")
        self.quick_btn.setFixedSize(44, 44)
        self.quick_btn.clicked.connect(self.show_quick_menu)

        # ปุ่มส่ง (ลูกค้า)
        btn_send_left = QPushButton(qta.icon("fa5s.reply"), "")
        btn_send_left.setObjectName("sendLeftButton")
        btn_send_left.setToolTip("ส่ง (ลูกค้า)")
        btn_send_left.setFixedSize(44, 44)
        btn_send_left.clicked.connect(lambda: self.send_message(sender="user"))

        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(self.quick_btn)
        input_row.addWidget(btn_send_left)
        chat_outer.addLayout(input_row)

        # ===================== Right: Camera frame =====================
        camera_frame = QFrame()
        camera_frame.setObjectName("cameraFrame")
        camera_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        camera_frame.setMaximumWidth(700)
        camera_outer = QVBoxLayout(camera_frame)
        camera_outer.setContentsMargins(16, 16, 16, 16)
        camera_outer.setSpacing(12)

        # >>> แถว "ภาษามือที่พบ : ..." + ปุ่มล้าง + ปุ่มส่ง <<<
        detected_row = QHBoxLayout()
        detected_row.setSpacing(8)

        lbl_detect_title = QLabel("ภาษามือที่พบ :")
        lbl_detect_title.setObjectName("detectTitle")

        self.lbl_detect_value = QLabel("-")
        self.lbl_detect_value.setObjectName("detectValue")
        self.lbl_detect_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.btn_detect_delete = QPushButton(qta.icon("fa5s.backspace"), "ลบ")
        self.btn_detect_delete.setObjectName("detectDeleteButton")
        self.btn_detect_delete.setFixedHeight(28)
        self.btn_detect_delete.setToolTip("ลบคำสุดท้ายที่ตรวจพบ")
        self.btn_detect_delete.clicked.connect(self.delete_last_detected_token)

        # ปุ่มส่งของฝั่งบาริสต้า (ส่งจาก label ภาษามือที่พบ -> validate_tokens -> generate_order)
        self.btn_detect_send = QPushButton(qta.icon("fa5s.paper-plane"), "ส่ง")
        self.btn_detect_send.setObjectName("detectSendButton")
        self.btn_detect_send.setFixedHeight(28)
        self.btn_detect_send.setToolTip("ส่งคำที่ตรวจพบไปยังฝั่งบาริสต้า (แปลงเป็นประโยคอัตโนมัติ)")
        self.btn_detect_send.clicked.connect(self.send_detected_as_barista)

        detected_row.addWidget(lbl_detect_title)
        detected_row.addWidget(self.lbl_detect_value, 1)
        detected_row.addWidget(self.btn_detect_delete)
        detected_row.addWidget(self.btn_detect_send)

        # กรอบกล้อง
        self.camera_label = QLabel("Loading camera...")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setFixedSize(560, 315)
        self.camera_label.setStyleSheet("color: gray; background-color: #111; border-radius: 8px;")

        control_row = QHBoxLayout()
        control_row.setSpacing(8)

        mic_button = QPushButton(qta.icon("fa5s.microphone", color="black"), "")
        mic_button.setObjectName("micButton")
        mic_button.setFixedSize(44, 44)

        self.camera_button = QPushButton(qta.icon("fa5s.video", color="black"), "")
        self.camera_button.setObjectName("cameraButton")
        self.camera_button.setFixedSize(44, 44)
        self.camera_button.clicked.connect(self.toggle_camera)

        control_row.addStretch(1)
        control_row.addWidget(mic_button)
        control_row.addWidget(self.camera_button)

        # ใส่ลำดับ: แถวผลภาษามือ -> ภาพจากกล้อง -> ปุ่มควบคุม
        camera_outer.addLayout(detected_row)
        camera_outer.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        camera_outer.addLayout(control_row)

        # สัดส่วน 45:55
        content_layout.addWidget(chat_frame)
        content_layout.addWidget(camera_frame)
        content_layout.setStretch(0, 45)
        content_layout.setStretch(1, 55)

        main_layout.addLayout(content_layout)

        # >>> Executor สำหรับ TTS (ให้เล่นทีละงาน ป้องกันเสียงทับกัน)
        self._tts_executor = ThreadPoolExecutor(max_workers=1)

    # ------------------------------------------------ Menu popup
    def open_menu_popup(self):
        dlg = MenuDialog(self)  # จะโหลดภาพจาก assets/menu.png
        dlg.selected.connect(self._on_menu_selected)
        dlg.exec_()

    def _on_menu_selected(self, item_name: str):
        # ส่งเป็นข้อความฝั่ง "ลูกค้า"
        self._add_chat_bubble(item_name, sender="user")

    # ---------------- Chat helpers ----------------
    def _bubble_max_width(self) -> int:
        vp = self.chat_scroll.viewport()
        if vp is None:
            return 520
        return max(280, int(vp.width() * 0.85))

    def _scroll_to_bottom(self):
        bar = self.chat_scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    # ใช้ช่อง input เฉพาะฝั่ง "ลูกค้า"
    def send_message(self, sender: str):
        text = self.input_edit.text().strip()
        if not text:
            return

        if sender != "user":
            # กันพลาดหากมีที่เรียกผิด
            sender = "user"

        self._add_chat_bubble(text, sender)
        self.input_edit.clear()

    # เมนูคำถามสำเร็จรูป (ไม่มีคีย์บอร์ดก็ถามได้)
    def show_quick_menu(self):
        phrases = [
            "มีเครื่องดื่มแนะนำไหม",
            "ทั้งหมดเท่าใหร่ครับ/ค่ะ",
            "จ่ายเป็นสแกนจ่าย",
            "จ่ายเป็นเงินสด",
            "จ่ายเป็นบัตรเครดิต",
        ]
        menu = QMenu(self)
        for p in phrases:
            act = menu.addAction(p)
            # ใช้ default arg ใน lambda เพื่อจับค่า p ณ ตอนสร้าง action
            act.triggered.connect(lambda _checked=False, text=p: self._add_chat_bubble(text, sender="user"))

        # โชว์เมนูใต้ปุ่ม quick
        pos = self.quick_btn.mapToGlobal(self.quick_btn.rect().bottomLeft())
        menu.exec_(pos)

    # ส่งจาก `_detected_tokens` เป็นฝั่งบาริสต้า (validate -> generate_order) แล้วล้างค่า
    def send_detected_as_barista(self):
        """ส่งคำที่อยู่หลัง 'ภาษามือที่พบ :' เป็นข้อความฝั่งบาริสต้า
        โดยแปลงลิสต์โทเค็นผ่าน order_generator แล้วล้างค่า"""
        if not self._detected_tokens:
            QMessageBox.information(self, "ว่างเปล่า", "ยังไม่มีคำภาษามือให้ส่ง")
            return

        # เตรียมคำแบบตัวพิมพ์เล็ก
        words = [t.strip().lower() for t in self._detected_tokens if t.strip()]
        if not words:
            QMessageBox.information(self, "ว่างเปล่า", "ยังไม่มีคำภาษามือให้ส่ง")
            return

        # ตรวจคำที่ไม่รองรับ
        bad = validate_tokens(words)
        if bad:
            QMessageBox.warning(
                self, "คำไม่รองรับ",
                "พบคำที่ไม่อยู่ใน order generator:\n\n- " + "\n- ".join(bad)
            )
            return

        # แปลงเป็นประโยค
        try:
            sentence = generate_order(words).strip()
        except Exception as e:
            QMessageBox.critical(self, "ผิดพลาด", f"ไม่สามารถแปลงคำสั่งได้:\n{e}")
            return

        if not sentence:
            QMessageBox.warning(self, "ว่างเปล่า", "ไม่สามารถสร้างประโยคจากคำที่ให้มา")
            return

        # แสดงในแชทฝั่งบาริสต้า + พูด TTS (ไม่บล็อก UI)
        self._add_chat_bubble(sentence, sender="barista")
        try:
            self._speak_async(sentence, wav_path="output.wav")
        except Exception as e:
            print(f"[TTS] error: {e}")

        # ล้างรายการและอัปเดต label
        self._detected_tokens = []
        self._update_detect_label_text()

    # ======= TTS helpers =======
    def _speak_async(self, text: str, wav_path: str = "output.wav"):
        """
        เรียก F5-TTS ผ่าน worker thread เพื่อไม่ให้บล็อก GUI
        ใช้ executor แบบคิวเดียว (max_workers=1) เพื่อให้พูดทีละข้อความ
        """
        try:
            self._tts_executor.submit(generate_tts_from_text, text, wav_path)
        except Exception as e:
            print(f"[TTS] submit error: {e}")

    def _add_chat_bubble(self, text: str, sender: str):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)

        if sender != self._last_sender:
            name_label = QLabel("Barista" if sender == "barista" else "ลูกค้า")
            name_label.setObjectName("chatNameBarista" if sender == "barista" else "chatNameUser")
            v.addWidget(name_label, 0, Qt.AlignRight if sender == "barista" else Qt.AlignLeft)

        bubble = QLabel(text)
        bubble.setObjectName("chatBubbleUser" if sender == "barista" else "chatBubbleBarista")
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        bubble.setMaximumWidth(self._bubble_max_width())

        v.addWidget(bubble, 0, Qt.AlignRight if sender == "barista" else Qt.AlignLeft)

        if sender == "barista":
            row.addStretch(1)
            row.addLayout(v)
        else:
            row.addLayout(v)
            row.addStretch(1)

        idx = self.chat_vbox.count() - 1
        self.chat_vbox.insertLayout(idx, row)
        self._bubbles.append(bubble)

        self._last_sender = sender

        self.chat_container.adjustSize()
        QTimer.singleShot(0, self._scroll_to_bottom)
        QTimer.singleShot(30, self._scroll_to_bottom)

    def resizeEvent(self, event):
        maxw = self._bubble_max_width()
        for b in self._bubbles:
            b.setMaximumWidth(maxw)
        super().resizeEvent(event)

    # ---------------- Camera handlers ----------------
    def ensure_camera_running(self):
        if not self.is_camera_on:
            self.start_camera()

    def start_camera(self, camera_id=0):
        if self.camera_thread is not None:
            try:
                self.camera_thread.frame_updated.disconnect()
            except Exception:
                pass
            try:
                # ถ้ามีต่อสัญญาณไว้ก่อนหน้า ให้ถอดก่อน
                self.camera_thread.detected_label.disconnect()
            except Exception:
                pass
            try:
                self.camera_thread.stop()
            except Exception:
                pass

        self._detected_tokens = []
        self._update_detect_label_text()

        self.camera_thread = CameraThread(camera_id=camera_id)
        self.camera_thread.frame_updated.connect(self.update_camera_frame)
        self.camera_thread.camera_ready.connect(self.clear_loading_text)

        # <<< ต่อสัญญาณทำนายคำจากกล้อง
        self.camera_thread.detected_label.connect(self.on_detected_label)

        self.camera_thread.start()
        self.is_camera_on = True
        try:
            self.camera_button.setIcon(qta.icon("fa5s.video", color="black"))
        except Exception:
            pass

    def stop_camera(self):
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
        try:
            self.camera_thread.frame_updated.disconnect()
        except Exception:
            pass
        try:
            self.camera_thread.detected_label.disconnect()
        except Exception:
            pass

        self.camera_label.clear()
        self.camera_label.setText("Loading camera...")
        self.camera_label.setStyleSheet("color: gray; background-color: #111; border-radius: 8px;")
        self.is_camera_on = False
        try:
            self.camera_button.setIcon(qta.icon("fa5s.video-slash", color="red"))
        except Exception:
            pass

    def update_camera_frame(self, image: QImage):
        if not image.isNull():
            self.camera_label.setScaledContents(True)
            self.camera_label.setPixmap(QPixmap.fromImage(image))

    def clear_loading_text(self):
        self.camera_label.setText("")

    def toggle_camera(self):
        if self.is_camera_on:
            self.stop_camera()
        else:
            self.start_camera()

    # --------- ภาษามือที่พบ : … ----------
    def on_detected_label(self, label: str):
        """รับคำที่ทายได้จาก CameraThread แล้วต่อท้ายในแถบ 'ภาษามือที่พบ :'"""
        token = (label or "").strip()
        if not token:
            return
        self._detected_tokens.append(token)
        self._update_detect_label_text()

    def _update_detect_label_text(self):
        text = " ".join(self._detected_tokens) if self._detected_tokens else "-"
        self.lbl_detect_value.setText(text)

    def delete_last_detected_token(self):
        """ลบคำสุดท้ายออกจากลิสต์ภาษามือที่พบ"""
        if not self._detected_tokens:
            return
        self._detected_tokens.pop()   # ลบคำท้าย
        self._update_detect_label_text()

    # helper ล้าง layout
    def _clear_layout(self, layout: QVBoxLayout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            child_layout = item.layout()
            w = item.widget()
            if child_layout is not None:
                self._clear_layout(child_layout)
                layout.removeItem(item)
                sip.delete(child_layout)
            elif w is not None:
                layout.removeWidget(w)
                w.deleteLater()
            else:
                layout.removeItem(item)  # spacer

    def _reset_chat(self):
        self._clear_layout(self.chat_vbox)
        self.chat_vbox.addStretch(1)
        self._bubbles = []
        self._last_sender = None
        self.input_edit.clear()
        QTimer.singleShot(0, self._scroll_to_bottom)

    def on_back_button_click(self):
        reply = QMessageBox.question(
            self,
            "ยืนยันการย้อนกลับ",
            "ต้องการกลับไปหน้าแรกหรือไม่?\n(กล้องจะถูกปิดและข้อความบนหน้าปัจจุบันจะถูกล้าง)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.stop_camera()
            finally:
                # >>> ปิดคิวงาน TTS เพื่อไม่ให้มีงานค้าง
                try:
                    self._tts_executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass
                self._reset_chat()
                self.on_back()

    # ป้องกัน resource ค้างในกรณีปิดหน้าต่าง
    def closeEvent(self, e):
        try:
            self._tts_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        super().closeEvent(e)

