# pages/start_page.py

from PyQt5.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QSizePolicy, QLineEdit, QScrollArea, QMessageBox, QMenu,
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer, QSize
import qtawesome as qta
import sip  # type: ignore
import re

from concurrent.futures import ThreadPoolExecutor
from scripts.camera_thread import CameraThread
from scripts.order_generator import generate_order, validate_tokens
from scripts.generate_tts import generate_tts_from_text
from pages.menu_dialog import MenuDialog


class StartPage(QWidget):
    def __init__(self, on_back):
        super().__init__()
        self.on_back = on_back

        self.is_camera_on = False
        self.camera_thread = None
        self._bubbles = []
        self._last_sender = None

        # กันซ้ำคำภาษามือจนกว่าจะกดส่ง
        self._detected_tokens = []
        self._detected_set = set()

        # ยอดสรุปเมนู
        self._order_total = 0
        self._has_order = False

        # เก็บรายการเมนูสำหรับยกเลิก: [{"name": str, "price": int, "bubble": QLabel}, ...]
        self._orders = []

        # ===== Layout =====
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop)

        # Header
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
        back_btn.setFixedHeight(48)
        back_btn.setToolTip("กลับไปหน้าแรก")
        back_btn.clicked.connect(self.on_back_button_click)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.addStretch(1)
        header_layout.addWidget(back_btn, 0, Qt.AlignRight)
        main_layout.addLayout(header_layout)

        # Content split
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 20, 0, 0)
        content_layout.setSpacing(20)

        # ===== Left: Chat frame =====
        chat_frame = QFrame()
        chat_frame.setObjectName("chatFrame")
        chat_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        chat_outer = QVBoxLayout(chat_frame)
        chat_outer.setContentsMargins(16, 16, 16, 12)
        chat_outer.setSpacing(12)

        chat_title_row = QHBoxLayout()
        chat_title = QLabel("แชท")
        chat_title.setObjectName("chatTitle")

        self.menu_btn = QPushButton(qta.icon("fa5s.bars"), "เมนู")
        self.menu_btn.setObjectName("menuButton")
        self.menu_btn.setFixedHeight(44)
        self.menu_btn.setToolTip("เปิดเมนูเครื่องดื่ม")
        self.menu_btn.clicked.connect(self.open_menu_popup)

        # ปุ่มยกเลิกรายการ (ปิดการใช้งานจนกว่าจะมีการสั่ง)
        self.cancel_btn = QPushButton(qta.icon("fa5s.minus-circle"), "ยกเลิกรายการ")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.setToolTip("ยกเลิกเมนูที่สั่งไว้ (เลือกได้หลายรายการ)")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.open_cancel_popup)

        chat_title_row.addWidget(chat_title)
        chat_title_row.addStretch(1)
        chat_title_row.addWidget(self.menu_btn)
        chat_title_row.addWidget(self.cancel_btn)
        chat_outer.addLayout(chat_title_row)

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
        self.input_edit.returnPressed.connect(lambda: self.send_message(sender="user"))

        self.quick_btn = QPushButton(qta.icon("fa5s.comment-dots"), "")
        self.quick_btn.setObjectName("quickAskButton")
        self.quick_btn.setToolTip("คำถามสำเร็จรูป (user)")
        self.quick_btn.setFixedSize(56, 56)
        self.quick_btn.setIconSize(QSize(26, 26))
        self.quick_btn.clicked.connect(self.show_quick_menu)

        btn_send_left = QPushButton(qta.icon("fa5s.reply"), "")
        btn_send_left.setObjectName("sendLeftButton")
        btn_send_left.setToolTip("ส่ง (ลูกค้า)")
        btn_send_left.setFixedSize(56, 56)
        btn_send_left.setIconSize(QSize(26, 26))
        btn_send_left.clicked.connect(lambda: self.send_message(sender="user"))

        input_row.addWidget(self.input_edit, 1)
        input_row.addWidget(self.quick_btn)
        input_row.addWidget(btn_send_left)
        chat_outer.addLayout(input_row)

        # ===== Right: Camera frame =====
        camera_frame = QFrame()
        camera_frame.setObjectName("cameraFrame")
        camera_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        camera_frame.setMaximumWidth(700)
        camera_outer = QVBoxLayout(camera_frame)
        camera_outer.setContentsMargins(16, 16, 16, 16)
        camera_outer.setSpacing(12)

        # Detected row
        detected_row = QHBoxLayout()
        detected_row.setSpacing(8)

        lbl_detect_title = QLabel("ภาษามือที่พบ :")
        lbl_detect_title.setObjectName("detectTitle")

        self.lbl_detect_value = QLabel("-")
        self.lbl_detect_value.setObjectName("detectValue")
        self.lbl_detect_value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.btn_detect_delete = QPushButton(qta.icon("fa5s.backspace"), "ลบ")
        self.btn_detect_delete.setObjectName("detectDeleteButton")
        self.btn_detect_delete.setFixedHeight(44)
        self.btn_detect_delete.setToolTip("ลบคำสุดท้ายที่ตรวจพบ")
        self.btn_detect_delete.clicked.connect(self.delete_last_detected_token)

        self.btn_detect_send = QPushButton(qta.icon("fa5s.paper-plane"), "ส่ง")
        self.btn_detect_send.setObjectName("detectSendButton")
        self.btn_detect_send.setFixedHeight(44)
        self.btn_detect_send.setToolTip("ส่งคำที่ตรวจพบไปยังฝั่งบาริสต้า (แปลงเป็นประโยคอัตโนมัติ)")
        self.btn_detect_send.clicked.connect(self.send_detected_as_barista)

        detected_row.addWidget(lbl_detect_title)
        detected_row.addWidget(self.lbl_detect_value, 1)
        detected_row.addWidget(self.btn_detect_delete)
        detected_row.addWidget(self.btn_detect_send)

        # Camera view
        self.camera_label = QLabel("Loading camera...")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setFixedSize(480, 270)
        self.camera_label.setStyleSheet("color: gray; background-color: #111; border-radius: 8px;")

        # Control row: left summary, right mic+camera
        control_row = QHBoxLayout()
        control_row.setSpacing(8)

        self.btn_summary = QPushButton(qta.icon("fa5s.cash-register"), "สรุปยอด")
        self.btn_summary.setObjectName("summaryButton")
        self.btn_summary.setFixedSize(120, 44)
        self.btn_summary.setToolTip("แสดงยอดรวมที่สั่ง")
        self.btn_summary.setEnabled(False)
        self.btn_summary.clicked.connect(self._on_summary_clicked)

        mic_button = QPushButton(qta.icon("fa5s.microphone", color="black"), "")
        mic_button.setObjectName("micButton")
        mic_button.setFixedSize(56, 56)

        self.camera_button = QPushButton(qta.icon("fa5s.video", color="black"), "")
        self.camera_button.setObjectName("cameraButton")
        self.camera_button.setFixedSize(56, 56)
        self.camera_button.setIconSize(QSize(26, 26))
        self.camera_button.clicked.connect(self.toggle_camera)

        control_row.addWidget(self.btn_summary)   # left
        control_row.addStretch(1)
        control_row.addWidget(mic_button)         # right
        control_row.addWidget(self.camera_button)

        camera_outer.addLayout(detected_row)
        camera_outer.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        camera_outer.addLayout(control_row)

        content_layout.addWidget(chat_frame)
        content_layout.addWidget(camera_frame)
        content_layout.setStretch(0, 60)
        content_layout.setStretch(1, 40)
        main_layout.addLayout(content_layout)

        # TTS executor
        self._tts_executor = ThreadPoolExecutor(max_workers=1)

    # ===== Helpers: ทำชื่อเมนูแบบสั้น (ตัดคำขึ้นต้น/ลงท้าย) =====
    def _to_concise_name(self, text: str) -> str:
        if not text:
            return text
        s = text.strip()
        # ตัดคำขึ้นต้นที่มักใช้
        s = re.sub(r'^(ขอสั่ง|สั่ง|อยากได้|รับ|เอา)\s*', '', s)
        # ตัดคำลงท้ายสุภาพ/ฟิลเลอร์
        s = re.sub(r'(ครับ|ค่ะ|คะ|หน่อย|นะ|ได้ไหม|ด้วย)$', '', s).strip()
        # ตัดอักขระปิดประโยค
        s = re.sub(r'[!。！？…]+$', '', s).strip()
        return s or text

    def _format_cancel_item(self, name: str, price: int) -> str:
        """ใช้ในป๊อปอัปยกเลิก — ชื่อแบบสั้น + ราคา ตัวใหญ่อ่านง่าย"""
        concise = self._to_concise_name(name)
        return f"{concise} — {price} บาท"

    # ===== Menu popup =====
    def open_menu_popup(self):
        dlg = MenuDialog(self)
        dlg.selected.connect(self._on_menu_selected)  # (text, price:int)
        dlg.exec_()

    def _on_menu_selected(self, text: str, price: int):
        # สร้างบับเบิลฝั่ง user ตามข้อความจริงที่เลือก (จะมี "ขอสั่ง..." ฯลฯ)
        bubble = self._add_chat_bubble(text, sender="user")
        try:
            p = int(price)
            self._order_total += p
            # เก็บ bubble เพื่อจะได้แก้เป็น "--ยกเลิกเมนูนี้แล้ว--" ตอนยกเลิก
            self._orders.append({"name": text, "price": p, "bubble": bubble})
        except Exception:
            pass
        self._has_order = True
        self.btn_summary.setEnabled(True)
        self.cancel_btn.setEnabled(True)

    # ===== ยกเลิกรายการ popup =====
    def open_cancel_popup(self):
        if not self._orders:
            QMessageBox.information(self, "ยังไม่มีรายการ", "ยังไม่มีเมนูที่สั่งไว้")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("ยกเลิกรายการที่สั่ง")
        dlg.resize(640, 560)  # ขยายขนาด popup
        vbox = QVBoxLayout(dlg)

        lst = QListWidget(dlg)
        # ทำให้ติ๊กง่ายขึ้น: ตัวอักษร 22px, padding, และ checkbox ใหญ่ขึ้น
        lst.setStyleSheet("""
            QListWidget { font-size: 22px; }
            QListWidget::item { padding: 10px 8px; }
            QAbstractItemView::indicator, QListView::indicator, QListWidget::indicator {
                width: 28px; height: 28px;
            }
        """)

        for o in self._orders:
            text = self._format_cancel_item(o['name'], o['price'])
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            lst.addItem(item)
        vbox.addWidget(lst)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dlg)
        vbox.addWidget(btns)

        def on_accept():
            to_remove_idx = []
            for i in range(lst.count()):
                it = lst.item(i)
                if it.checkState() == Qt.Checked:
                    to_remove_idx.append(i)

            if not to_remove_idx:
                dlg.reject()
                return

            # ลบจากท้ายก่อน และแก้ข้อความบับเบิลของ user ให้เป็น "--ยกเลิกเมนูนี้แล้ว--"
            for i in reversed(to_remove_idx):
                order = self._orders[i]
                bubble = order.get("bubble")
                if isinstance(bubble, QLabel):
                    bubble.setText("--ยกเลิกเมนูนี้แล้ว--")
                    bubble.setStyleSheet("color: #8A8A8A; font-style: italic;")
                del self._orders[i]

            # คำนวณยอดใหม่ + อัปเดตปุ่ม
            self._order_total = sum(o["price"] for o in self._orders)
            self._has_order = len(self._orders) > 0
            self.btn_summary.setEnabled(self._has_order)
            self.cancel_btn.setEnabled(self._has_order)

            # ไม่ส่งแชทฝั่งบาริสต้า
            dlg.accept()

        btns.accepted.connect(on_accept)
        btns.rejected.connect(dlg.reject)
        dlg.exec_()

    # ===== Chat helpers =====
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
        if sender != "user":
            sender = "user"
        self._add_chat_bubble(text, sender)
        self.input_edit.clear()

    def show_quick_menu(self):
        phrases = [
            "มีเครื่องดื่มแนะนำไหม",
            "ทั้งหมดเท่าใหร่ครับ/ค่ะ",
            "จ่ายเป็นสแกนจ่าย",
            "จ่ายเป็นเงินสด",
            "จ่ายเป็นบัตรเครดิต",
            "ล้างแชทสนทนา",  # ✅ เพิ่มข้อที่ 6
        ]
        menu = QMenu(self)
        for p in phrases:
            act = menu.addAction(p)
            act.triggered.connect(lambda _checked=False, text=p: self._on_quick_action(text))
        pos = self.quick_btn.mapToGlobal(self.quick_btn.rect().bottomLeft())
        menu.exec_(pos)

    def _on_quick_action(self, text: str):
        if text == "ล้างแชทสนทนา":
            self._reset_orders()
            self._reset_chat()
            QMessageBox.information(self, "ล้างแล้ว", "ล้างแชทและรายการสั่งทั้งหมดเรียบร้อย")
        else:
            self._add_chat_bubble(text, sender="user")

    # ===== สรุปยอด =====
    def _on_summary_clicked(self):
        if not self._has_order or self._order_total <= 0:
            QMessageBox.information(self, "ยังไม่มีรายการ", "ลูกค้ายังไม่ได้สั่งเมนู")
            return
        sentence = f"ทั้งหมด {self._order_total} บาทครับ"
        self._add_chat_bubble(sentence, sender="barista")
        try:
            self._speak_async(sentence, wav_path="output.wav")
        except Exception as e:
            print(f"[TTS] error: {e}")

        # รีเซ็ตหลังสรุป
        self._order_total = 0
        self._has_order = False
        self._orders = []
        self.btn_summary.setEnabled(False)
        self.cancel_btn.setEnabled(False)

    # ======= ภาษามือที่พบ -> ส่งให้บาริสต้า =======
    def send_detected_as_barista(self):
        if not self._detected_tokens:
            QMessageBox.information(self, "ว่างเปล่า", "ยังไม่มีคำภาษามือให้ส่ง")
            return

        words = [t.strip().lower() for t in self._detected_tokens if t.strip()]
        if not words:
            QMessageBox.information(self, "ว่างเปล่า", "ยังไม่มีคำภาษามือให้ส่ง")
            return

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

        if sentence == "สั่งไม่ถูกครับ":
            QMessageBox.information(self, "ยังไม่เข้าใจ", "ไม่มีการแปลบทพูดนี้")
            return

        if not sentence:
            QMessageBox.warning(self, "ว่างเปล่า", "ไม่สามารถสร้างประโยคจากคำที่ให้มา")
            return

        self._add_chat_bubble(sentence, sender="barista")
        try:
            self._speak_async(sentence, wav_path="output.wav")
        except Exception as e:
            print(f"[TTS] error: {e}")

        # ส่งแล้ว: ล้างรายการ + ปลดล็อกกันซ้ำ
        self._detected_tokens = []
        self._detected_set = set()
        self._update_detect_label_text()

    # ===== TTS helpers =====
    def _speak_async(self, text: str, wav_path: str = "output.wav"):
        try:
            self._tts_executor.submit(generate_tts_from_text, text, wav_path)
        except Exception as e:
            print(f"[TTS] submit error: {e}")

    def _add_chat_bubble(self, text: str, sender: str) -> QLabel:
        """เพิ่มบับเบิลและคืน QLabel เพื่อให้แก้ไขได้ภายหลัง (ใช้ตอนยกเลิก)"""
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
        return bubble

    def resizeEvent(self, event):
        maxw = self._bubble_max_width()
        for b in self._bubbles:
            b.setMaximumWidth(maxw)
        super().resizeEvent(event)

    # ===== Camera handlers =====
    def ensure_camera_running(self):
        if not self.is_camera_on:
            self.start_camera()

    def start_camera(self, camera_id=0):
        if self.camera_thread is not None:
            try: self.camera_thread.frame_updated.disconnect()
            except Exception: pass
            try: self.camera_thread.detected_label.disconnect()
            except Exception: pass
            try: self.camera_thread.stop()
            except Exception: pass

        self._detected_tokens = []
        self._detected_set = set()
        self._update_detect_label_text()

        self.camera_thread = CameraThread(camera_id=camera_id)
        self.camera_thread.frame_updated.connect(self.update_camera_frame)
        self.camera_thread.camera_ready.connect(self.clear_loading_text)
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
        try: self.camera_thread.frame_updated.disconnect()
        except Exception: pass
        try: self.camera_thread.detected_label.disconnect()
        except Exception: pass

        self.camera_label.clear()
        self.camera_label.setText("Loading camera...")
        self.camera_label.setStyleSheet("color: gray; background-color: #111; border-radius: 8px;")
        self.is_camera_on = False
        try:
            self.camera_button.setIcon(qta.icon("fa5s.video-slash", color="red"))
        except Exception:
            pass

        self._detected_tokens = []
        self._detected_set = set()
        self._update_detect_label_text()

    def update_camera_frame(self, image: QImage):
        if not image.isNull():
            pix = QPixmap.fromImage(image).scaled(
                self.camera_label.size(), Qt.KeepAspectRatio, Qt.FastTransformation
            )
            self.camera_label.setPixmap(pix)

    def clear_loading_text(self):
        self.camera_label.setText("")

    def toggle_camera(self):
        if self.is_camera_on:
            self.stop_camera()
        else:
            self.start_camera()

    # ===== ภาษามือที่พบ : update/add/delete =====
    def on_detected_label(self, label: str):
        token = (label or "").strip().lower()
        if not token:
            return
        if token in self._detected_set:
            return
        self._detected_tokens.append(token)
        self._detected_set.add(token)
        self._update_detect_label_text()

    def _update_detect_label_text(self):
        text = " ".join(self._detected_tokens) if self._detected_tokens else "-"
        self.lbl_detect_value.setText(text)

    def delete_last_detected_token(self):
        if not self._detected_tokens:
            return
        last = self._detected_tokens.pop()
        try:
            self._detected_set.remove(last)
        except KeyError:
            pass
        self._update_detect_label_text()

    # ===== Cleanup =====
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
                layout.removeItem(item)

    def _reset_chat(self):
        self._clear_layout(self.chat_vbox)
        self.chat_vbox.addStretch(1)
        self._bubbles = []
        self._last_sender = None
        self.input_edit.clear()
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _reset_orders(self):
        """รีเซ็ตสถานะการสั่งทั้งหมดให้เหมือนเริ่มใหม่ (ไม่ยุ่งกับกล้อง/ภาษามือ)"""
        self._order_total = 0
        self._has_order = False
        self._orders = []
        self.btn_summary.setEnabled(False)
        self.cancel_btn.setEnabled(False)

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
                try:
                    self._tts_executor.shutdown(wait=False, cancel_futures=True)
                except Exception:
                    pass
                self._detected_tokens = []
                self._detected_set = set()
                self._reset_chat()
                self.on_back()

    def closeEvent(self, e):
        try:
            self._tts_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        super().closeEvent(e)
