import sys
import cv2
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QStackedWidget, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QKeyEvent
from PyQt6.QtCore import Qt, QSize, QTimer
import qtawesome as qta

class StartPage(QWidget):
    def __init__(self, switch_callback):
        super().__init__()

        # Layout หลักทั้งหมด
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # ✅ ให้ทุกอย่างชิดบน

        # --- ส่วนหัวข้อความ ---
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ✅ ใช้ HTML และ Rich Text เพื่อกำหนดสีให้ "SLR"
        title_label = QLabel('<span style="color: white;">De</span><span style="color: #C2FCEA;">SLR</span>')
        title_label.setObjectName("mainTitle")
        title_label.setTextFormat(Qt.TextFormat.RichText)  # ✅ ใช้ RichText เพื่อให้ HTML ทำงาน

        subtitle_label = QLabel(
            '<span style="color: white;">ยินดีต้อนรับเข้าสู่ </span>'
            '<span style="color: #C2FCEA;">ร้านคาเฟ่ที่เงียบ แต่ล้นไปด้วยสุข !</span>'
        )
        subtitle_label.setObjectName("subTitle")
        subtitle_label.setTextFormat(Qt.TextFormat.RichText)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        header_layout.setSpacing(10)

        # ✅ ใส่ Header ลงใน Layout หลัก
        main_layout.addLayout(header_layout)

        self.setLayout(main_layout)

        # --- Layout คอนเทนต์หลัก ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 20, 0, 0)
        content_layout.setSpacing(20)

        # --- ซ้าย: คู่มือใช้งาน ---
        guide_frame = QFrame()
        guide_layout = QVBoxLayout()
        guide_title = QLabel("เริ่มต้นใช้งานง่ายๆ เพียง “สวัสดี”")
        guide_title.setObjectName("guideTitle")

        # ✅ คำว่า "ภาษามือสวัสดีง่ายๆ"
        hand_sign_label = QLabel("ภาษามือสวัสดีง่ายๆ")
        hand_sign_label.setObjectName("handSignText")

        # ✅ Layout สำหรับ Step 1 และ Step 2 (Step 1 อยู่ซ้าย Step 2 อยู่ขวาและต่ำลง)
        step_layout = QHBoxLayout()

        step1_layout = QVBoxLayout()
        step1 = QLabel("Step 1: มือแตะหน้าผาก")
        step1.setObjectName("guideStep")
        step1_img = QLabel()
        step1_img.setPixmap(QPixmap("assets/Coff1.png").scaled(105, 180, Qt.AspectRatioMode.KeepAspectRatio))

        step1_layout.addWidget(step1)
        step1_layout.addWidget(step1_img)
        step1_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        step2_layout = QVBoxLayout()
        step2 = QLabel("Step 2: เอามือผายออก")
        step2.setObjectName("guideStep")
        step2_img = QLabel()
        step2_img.setPixmap(QPixmap("assets/Coff2.png").scaled(105, 180, Qt.AspectRatioMode.KeepAspectRatio))

        step2_layout.addWidget(step2)
        step2_layout.addWidget(step2_img)
        step2_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ✅ ใช้ QVBoxLayout ให้ Step 2 อยู่ต่ำกว่า Step 1
        step2_wrapper = QVBoxLayout()
        step2_wrapper.addStretch()
        step2_wrapper.addLayout(step2_layout)

        # ✅ เพิ่ม Step 1 และ Step 2 เข้า Layout แนวนอน
        step_layout.addLayout(step1_layout)
        step_layout.addLayout(step2_wrapper)

        # ✅ Step 3 แยกด้านล่าง
        step3 = QLabel("Step 3: จากนั้น ก็สั่งเมนูได้เลย")
        step3.setObjectName("guideStep")
        step3_img = QLabel()
        
        guide_layout.addWidget(guide_title)
        guide_layout.addWidget(hand_sign_label)
        guide_layout.addLayout(step_layout)
        guide_layout.addWidget(step3)
        guide_layout.addWidget(step3_img)
        guide_frame.setLayout(guide_layout)
        guide_frame.setObjectName("guideFrame")

        # --- ขวา: กล้อง + ปุ่มวางสาย ---
        camera_frame = QFrame()
        camera_layout = QVBoxLayout()
        camera_frame.setObjectName("cameraFrame")

        camera_label = QLabel("Loading Camera...")
        camera_label.setObjectName("cameraText")
        camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # ✅ สถานะกล้อง (เปิด/ปิด)
        self.is_camera_on = True

        # ✅ ปุ่มใส (ไมค์ และ กล้อง)
        mic_button = QPushButton()
        mic_button.setIcon(qta.icon("fa6s.microphone", color="black"))
        mic_button.setObjectName("micButton")
        mic_button.setFixedSize(60, 60)
        mic_button.setIconSize(QSize(27, 27))

        self.camera_button = QPushButton()
        self.camera_button.setIcon(qta.icon("fa6s.video", color="black"))  # เริ่มต้นเป็นเปิดกล้อง
        self.camera_button.setObjectName("cameraButton")
        self.camera_button.setFixedSize(60, 60)
        self.camera_button.setIconSize(QSize(25, 25))
        self.camera_button.clicked.connect(self.toggle_camera)

        open_button = QPushButton()
        open_button.setIcon(qta.icon("fa6s.phone"))
        open_button.setObjectName("openButton")
        open_button.setFixedSize(60, 60)
        open_button.setIconSize(QSize(20, 20))
        open_button.clicked.connect(switch_callback)

        left_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        right_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)


        button_layout = QHBoxLayout()
        button_layout.addItem(left_spacer)
        button_layout.addWidget(mic_button, alignment=Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(open_button, alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.camera_button, alignment=Qt.AlignmentFlag.AlignLeft)
        button_layout.addItem(right_spacer)

        camera_layout.addItem(top_spacer)
        camera_layout.addWidget(camera_label, alignment=Qt.AlignmentFlag.AlignCenter)
        camera_layout.addItem(bottom_spacer)
        camera_layout.addLayout(button_layout)

        camera_frame.setLayout(camera_layout)

        content_layout.addWidget(guide_frame)
        content_layout.addWidget(camera_frame)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def toggle_camera(self):
        """ ฟังก์ชันเปิด/ปิดกล้อง """
        if self.is_camera_on:
            self.camera_button.setIcon(qta.icon("fa6s.video-slash", color="red"))  # ปิดกล้อง
        else:
            self.camera_button.setIcon(qta.icon("fa6s.video", color="black"))  # เปิดกล้อง

        self.is_camera_on = not self.is_camera_on


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

        


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat UI")
        self.default_size = (1024, 600)
        self.is_fullscreen = True  # ✅ เริ่มต้นเป็น Fullscreen

        # Widget หลักที่ใช้จัดการหน้า
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # หน้าสตาร์ท
        self.start_page = StartPage(self.show_chat_page)
        self.stack.addWidget(self.start_page)

        # หน้าแชท
        self.chat_page = ChatPage()
        self.stack.addWidget(self.chat_page)

        # โหลด QSS
        self.setStyleSheet(open("style.qss", encoding="utf-8").read())

        # ✅ เปิดโปรแกรมมาเป็น Fullscreen
        self.showFullScreen()

    def show_chat_page(self):
        """เปลี่ยนไปหน้าหลักของแชท"""
        self.stack.setCurrentWidget(self.chat_page)

    def keyPressEvent(self, event: QKeyEvent):
        """เช็คการกด F11 เพื่อสลับ Fullscreen"""
        if event.key() == Qt.Key.Key_F11:
            if self.is_fullscreen:
                self.showNormal()
                self.resize(*self.default_size)
            else:
                self.showFullScreen()
            self.is_fullscreen = not self.is_fullscreen

# เรียกใช้งานแอป
app = QApplication([])
window = MainApp()
window.show()
app.exec()
