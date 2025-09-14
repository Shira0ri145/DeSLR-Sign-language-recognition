from PyQt5.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QSizePolicy, QLineEdit, QScrollArea, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import qtawesome as qta
import sip  # type: ignore

from scripts.camera_thread import CameraThread
from scripts.order_generator import generate_order, validate_tokens
from scripts.pyttsx import speak as tts_speak

# ⬇️ เพิ่ม: ป๊อปอัปเมนู
from pages.menu_dialog import MenuDialog


class StartPage(QWidget):
    def __init__(self, on_back):
        super().__init__()
        self.on_back = on_back

        self.is_camera_on = False
        self.camera_thread = None
        self._bubbles = []
        self._last_sender = None

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
        self.input_edit.returnPressed.connect(lambda: self.send_message(sender="barista"))

        btn_send_right = QPushButton(qta.icon("fa5s.paper-plane"), "")
        btn_send_right.setObjectName("sendRightButton")
        btn_send_right.setToolTip("ส่งเป็นฝั่งขวา (Barista)")
        btn_send_right.setFixedSize(44, 44)
        btn_send_right.clicked.connect(lambda: self.send_message(sender="barista"))

        btn_send_left = QPushButton(qta.icon("fa5s.reply"), "")
        btn_send_left.setObjectName("sendLeftButton")
        btn_send_left.setToolTip("ส่งเป็นฝั่งซ้าย (ลูกค้า)")
        btn_send_left.setFixedSize(44, 44)
        btn_send_left.clicked.connect(lambda: self.send_message(sender="user"))

        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(btn_send_right)
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

        camera_outer.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        camera_outer.addLayout(control_row)

        # สัดส่วน 45:55
        content_layout.addWidget(chat_frame)
        content_layout.addWidget(camera_frame)
        content_layout.setStretch(0, 45)
        content_layout.setStretch(1, 55)

        main_layout.addLayout(content_layout)

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

    def send_message(self, sender: str):
        text = self.input_edit.text().strip()
        if not text:
            return

        if sender == "barista":
            words = [t.strip().lower() for t in text.split() if t.strip()]

            bad = validate_tokens(words)
            if bad:
                QMessageBox.warning(
                    self, "คำไม่รองรับ",
                    "พบคำที่ไม่อยู่ใน order generator:\n\n- " + "\n- ".join(bad)
                )
                return
            try:
                sentence = generate_order(words).strip()
            except Exception as e:
                QMessageBox.critical(self, "ผิดพลาด", f"ไม่สามารถแปลงคำสั่งได้:\n{e}")
                return

            if not sentence:
                QMessageBox.warning(self, "ว่างเปล่า", "ไม่สามารถสร้างประโยคจากคำที่ให้มา")
                return

            self._add_chat_bubble(sentence, sender)
            self.input_edit.clear()
            try:
                tts_speak(sentence)
            except Exception as e:
                print(f"[TTS] error: {e}")
            return

        self._add_chat_bubble(text, sender)
        self.input_edit.clear()

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
                self.camera_thread.stop()
            except Exception:
                pass
        self.camera_thread = CameraThread(camera_id=camera_id)
        self.camera_thread.frame_updated.connect(self.update_camera_frame)
        self.camera_thread.camera_ready.connect(self.clear_loading_text)
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
                self._reset_chat()
                self.on_back()
