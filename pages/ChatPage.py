from PyQt6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, 
    QHBoxLayout,  QFrame
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class ChatPage(QWidget):
    def __init__(self):
        super().__init__()

        # ✅ Layout หลัก
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) 
        

        # ✅ "DeSLR" ด้านบนซ้าย
        title_label = QLabel('<span style="color: white;">De</span><span style="color: #C2FCEA;">SLR</span>')
        title_label.setObjectName("mainTitle")
        title_label.setTextFormat(Qt.TextFormat.RichText)
        main_layout.addWidget(title_label)

        # ✅ Layout ของแชท
        chat_layout = QVBoxLayout()
        chat_layout.setSpacing(20)

        # --- 🔹 บรรทัดแชท 1: Barista ---
        barista_chat_layout = QHBoxLayout()
        barista_chat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        barista_img = QLabel()
        barista_img.setPixmap(QPixmap("assets/wall3.jpg").scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio))
        barista_img.setObjectName("chatImage")

        # 🔹 สร้าง Frame สำหรับข้อความของ Barista
        barista_frame = QFrame()
        barista_frame.setObjectName("chatBubbleBarista")
        barista_frame_layout = QVBoxLayout(barista_frame)

        barista_name = QLabel("Barista")
        barista_name.setObjectName("chatNameBarista")

        barista_text = QLabel("สวัสดี , วันนี้สั่งเมนูอะไรดีคะ ?")
        barista_text.setObjectName("chatTextBarista")

        barista_frame_layout.addWidget(barista_name)
        barista_frame_layout.addWidget(barista_text)

        barista_chat_layout.addWidget(barista_frame)
        barista_chat_layout.addWidget(barista_img)

        # --- 🔹 บรรทัดแชท 2: ลูกค้า (คนสั่ง) ---
        user_chat_layout = QHBoxLayout()
        user_chat_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_img = QLabel()
        user_img.setPixmap(QPixmap("assets/wall1.jpg").scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio))
        user_img.setObjectName("chatImage")

        # 🔹 สร้าง Frame สำหรับข้อความของลูกค้า
        user_frame = QFrame()
        user_frame.setObjectName("chatBubbleUser")
        user_frame_layout = QVBoxLayout(user_frame)

        user_name = QLabel("คุณ (คนสั่ง)")
        user_name.setObjectName("chatNameUser")

        user_text = QLabel("เอาชาเขียวเย็น หวานน้อย 1 แก้วครับ")
        user_text.setObjectName("chatTextUser")

        user_frame_layout.addWidget(user_name)
        user_frame_layout.addWidget(user_text)

        user_chat_layout.addWidget(user_img)
        user_chat_layout.addWidget(user_frame)

        # ✅ ใส่ทุกอย่างลงใน Layout หลัก
        chat_layout.addLayout(barista_chat_layout)
        chat_layout.addLayout(user_chat_layout)
        main_layout.addLayout(chat_layout)

        self.setLayout(main_layout)

