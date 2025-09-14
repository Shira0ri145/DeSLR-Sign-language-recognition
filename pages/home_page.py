# pages/home_page.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor
import qtawesome as qta

class HomePage(QWidget):
    def __init__(self, on_start):
        super().__init__()
        self.on_start = on_start

        # ===== Outer layout: center vertically + horizontally =====
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(0)

        # ----- the card -----
        card = QFrame()
        card.setObjectName("homeCard")
        card.setFixedWidth(780)          # กำหนดความกว้าง เพื่อให้จัดกลางได้สวย
        card.setMinimumHeight(120)

        # shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(42)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 18)
        card.setGraphicsEffect(shadow)

        # card content
        card_l = QHBoxLayout(card)
        card_l.setContentsMargins(20, 16, 20, 16)
        card_l.setSpacing(16)

        avatar = QLabel()
        avatar.setObjectName("homeAvatar")
        avatar.setFixedSize(56, 56)
        avatar.setPixmap(
            QPixmap("assets/user.png").scaled(
                56, 56, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
        )

        text_box = QVBoxLayout()
        title = QLabel("DeSLR Café")
        title.setObjectName("homeTitle")
        subtitle = QLabel("พร้อมเริ่มต้นแชทด้วยภาษามือ")
        subtitle.setObjectName("homeSub")

        underline = QFrame()
        underline.setObjectName("homeUnderline")
        underline.setFixedHeight(1)

        text_box.addWidget(title)
        text_box.addWidget(subtitle)
        text_box.addWidget(underline)

        start_btn = QPushButton()
        start_btn.setObjectName("homeStartBtn")
        start_btn.setFixedSize(44, 44)
        start_btn.setIcon(qta.icon("fa5s.video"))
        start_btn.clicked.connect(self.on_start)

        card_l.addWidget(avatar)
        card_l.addLayout(text_box, 1)
        card_l.addStretch(1)  # ดันปุ่มไปขวา
        card_l.addWidget(start_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

        # ===== Center the card =====
        row_center = QHBoxLayout()
        row_center.addStretch(1)
        row_center.addWidget(card)
        row_center.addStretch(1)

        outer.addStretch(1)          # ดันลงจากด้านบน
        outer.addLayout(row_center)  # จัดกึ่งกลางแนวนอน
        outer.addStretch(1)          # ดันขึ้นจากด้านล่าง
