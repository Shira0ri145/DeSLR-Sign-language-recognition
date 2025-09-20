# pages/menu_dialog.py
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
import qtawesome as qta

MENU_IMAGE = "assets/menuapp.png"


class ChoiceDialog(QDialog):
    """กล่องเลือกตัวเลือกง่าย ๆ ด้วยปุ่มหลายปุ่ม"""
    def __init__(self, title: str, options: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.choice = None

        self.setStyleSheet("""
            QDialog { background: #0b2f2e; }
            QLabel#title { color: white; font-size: 18px; font-weight: 700; }
            QPushButton.opt {
                background: white; color: #174A4E; border: 1px solid #BFD6D7;
                border-radius: 10px; padding: 10px 14px; font-weight: 600;
            }
            QPushButton.opt:hover { background: #EEF6F7; }
            QPushButton#closeBtn {
                background: white; border: 1px solid #BFD6D7; border-radius: 8px; padding:6px 10px;
            }
            QPushButton#closeBtn:hover { background:#EEF6F7; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("title")
        title_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(title_lbl)

        wrap = QWidget()
        row = QHBoxLayout(wrap); row.setSpacing(10)
        for opt in options:
            b = QPushButton(opt, wrap)
            b.setProperty("class", "opt")
            b.setObjectName("optBtn")
            b.setMinimumWidth(110)
            b.setMaximumHeight(44)
            b.setStyleSheet("QPushButton{background:white;}")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, x=opt: self._pick(x))
            row.addWidget(b)
        row.addStretch(1)
        root.addWidget(wrap)

        btn_close = QPushButton(qta.icon("fa5s.times"), "ยกเลิก")
        btn_close.setObjectName("closeBtn")
        btn_close.clicked.connect(self.reject)
        root.addWidget(btn_close, 0, Qt.AlignRight)

    def _pick(self, value: str):
        self.choice = value
        self.accept()


class MenuDialog(QDialog):
    """
    ป๊อปอัปโชว์รูปเมนู + ปุ่มโปร่งใสทับตำแหน่งราคา
    เมื่อกดจุดหนึ่ง จะถามต่อ 2 ขั้น: (ร้อน/เย็น/ปั่น) แล้ว (ความหวาน)
    จากนั้น emit ข้อความสั่งครบประโยคกลับไป
    """
    selected = pyqtSignal(str)  # ส่ง "ขอสั่ง ... ครับ" กลับ

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("เมนูเครื่องดื่ม")
        self.setModal(True)
        self.setMinimumSize(980, 700)
        self.setStyleSheet("""
            QDialog { background: #0b2f2e; }
            #menuImage { border: 2px solid white; border-radius: 8px; }
            QPushButton#priceBtn { background: rgba(255,255,255,0); border: none; }
            QPushButton#closeBtn {
                background: white; border: 1px solid #BFD6D7; border-radius: 8px; padding:6px 10px;
            }
            QPushButton#closeBtn:hover { background: #EEF6F7; }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16,16,16,16)
        lay.setSpacing(10)

        self.img_label = QLabel()
        self.img_label.setObjectName("menuImage")
        self.img_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.img_label, 1)

        self.close_btn = QPushButton(qta.icon("fa5s.times"), "ปิด")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.clicked.connect(self.reject)
        lay.addWidget(self.close_btn, 0, Qt.AlignRight)

        # โหลดรูป
        self._pix = QPixmap(MENU_IMAGE)
        if self._pix.isNull():
            self.img_label.setText("ไม่พบรูปเมนู: {}".format(MENU_IMAGE))
        else:
            self.img_label.setPixmap(
                self._pix.scaled(self.img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        # ปุ่มทับบนรูป (hotspots) – ค่าพิกัดแบบสัดส่วนของรูป
        self.hotspot_buttons = []
        self.hotspots = [
            # x%, y%, w%, h%, label, menu_name
            (0.095, 0.645, 0.09, 0.20, "65.-", "ชาเขียว"),
            (0.210, 0.645, 0.09, 0.20, "65.-", "ชาไทย"),
            (0.330, 0.645, 0.09, 0.20, "65.-", "นมชมพู"),
            (0.460, 0.645, 0.09, 0.20, "65.-", "นมสดคาราเมล"),
            (0.580, 0.645, 0.09, 0.20, "65.-", "โกโก้มิ้น"),
            (0.815, 0.645, 0.09, 0.20, "65.-", "โกโก้"),
        ]

        self._rebuild_hotspots()

    # ---------- helper ----------
    def _strip_meta(self, s: str) -> str:
        """ตัดข้อความในวงเล็บเช่น ' (55)' หรือ ' (50%)' ออก เหลือแค่คำหลัก"""
        return s.split('(')[0].strip()

    # ---------- Layout & hotspots ----------
    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if not self._pix.isNull():
            self.img_label.setPixmap(
                self._pix.scaled(self.img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        self._rebuild_hotspots()

    def _rebuild_hotspots(self):
        for b in self.hotspot_buttons:
            b.setParent(None)
            b.deleteLater()
        self.hotspot_buttons.clear()

        if self._pix.isNull():
            return

        label_w = self.img_label.width()
        label_h = self.img_label.height()
        pix_w = self._pix.width()
        pix_h = self._pix.height()

        scale = min(label_w / pix_w, label_h / pix_h)
        disp_w = int(pix_w * scale)
        disp_h = int(pix_h * scale)

        off_x = (label_w - disp_w) // 2
        off_y = (label_h - disp_h) // 2

        for (xp, yp, wp, hp, price_txt, menu_name) in self.hotspots:
            x = off_x + int(xp * disp_w)
            y = off_y + int(yp * disp_h)
            w = int(wp * disp_w)
            h = int(hp * disp_h)

            btn = QPushButton(self.img_label)
            btn.setObjectName("priceBtn")
            btn.setToolTip(f"{menu_name} • {price_txt} (คลิก)")
            btn.setGeometry(x, y, w, h)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, name=menu_name: self._start_flow(name))
            btn.show()
            self.hotspot_buttons.append(btn)

    # ---------- Flow: menu -> temp -> sweetness ----------
    def _start_flow(self, menu_name: str):
        # 1) เลือกรูปแบบ
        temp_dlg = ChoiceDialog("เลือกรูปแบบ (ร้อน/เย็น/ปั่น)", ["ร้อน (50)", "เย็น (55)", "ปั่น (60)"], self)
        if temp_dlg.exec_() != QDialog.Accepted or not temp_dlg.choice:
            return
        temp = self._strip_meta(temp_dlg.choice)  # ตัดราคาออก

        # 2) เลือกระดับความหวาน
        sweet_dlg = ChoiceDialog(
            "เลือกระดับความหวาน",
            ["ไม่หวาน (0%)", "หวานน้อย (50%)", "หวานปกติ (100%)", "หวานมาก (200%)"],
            self
        )
        if sweet_dlg.exec_() != QDialog.Accepted or not sweet_dlg.choice:
            return
        sweet = self._strip_meta(sweet_dlg.choice)  # ตัด % ออก

        # 3) สร้างประโยคสั่งซื้อและส่งออก (ไม่เอาราคา/เปอร์เซ็นต์)
        text = f"ขอสั่ง{menu_name}{temp}{sweet} ครับ"
        self.selected.emit(text)
        self.accept()
