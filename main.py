from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame
from PyQt6.QtGui import QPixmap, QIcon, QKeyEvent
from PyQt6.QtCore import Qt


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
        step1 = QLabel("Step 1: เอามือแตะหน้าผาก")
        step1.setObjectName("guideStep")
        step1_img = QLabel()
        step1_img.setPixmap(QPixmap("assets/Coff1.png").scaled(105, 180, Qt.AspectRatioMode.KeepAspectRatio))

        step1_layout.addWidget(step1)
        step1_layout.addWidget(step1_img)
        step1_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        step2_layout = QVBoxLayout()
        step2 = QLabel("Step 2: แล้วเอามือผายออก")
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
        right_frame = QFrame()
        right_layout = QVBoxLayout()

        # ✅ สร้าง QVBoxLayout ใหม่สำหรับกล้องและปุ่ม
        camera_layout = QVBoxLayout()
        camera_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        camera_view = QLabel()
        camera_view.setPixmap(QPixmap("assets/cafe.png").scaled(500, 300, Qt.AspectRatioMode.KeepAspectRatio))
        camera_view.setObjectName("cameraView")

        right_layout.addWidget(camera_view)
        right_frame.setLayout(right_layout)

        content_layout.addWidget(guide_frame)
        content_layout.addWidget(right_frame)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)



class ChatPage(QWidget):
    def __init__(self):
        super().__init__()

        # Layout หลัก
        main_layout = QVBoxLayout()

        # 🎭 รูปโปรไฟล์ฝั่งขวา
        profile_pic = QLabel()
        profile_pic.setPixmap(QPixmap("assets/baris.png").scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        profile_pic.setObjectName("profilePic")

        # 💬 กล่องข้อความของคนทางขวา
        right_text = QLabel("ทั้งหมด 50baht ครับ")
        right_text.setObjectName("rightBubble")

        # 🖼️ ภาพด้านขวา
        right_image = QLabel()
        right_image.setPixmap(QPixmap("assets/baris.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        right_image.setObjectName("rightImage")

        # 🔄 Layout สำหรับฝั่งขวา
        right_layout = QHBoxLayout()
        right_layout.addWidget(right_text)
        right_layout.addWidget(profile_pic)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Layout สำหรับภาพด้านขวา
        right_image_layout = QHBoxLayout()
        right_image_layout.addWidget(right_image)
        right_image_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # 🎭 รูปผู้ใช้ทางซ้าย
        user_image = QLabel()
        user_image.setPixmap(QPixmap("assets/user.png").scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        user_image.setObjectName("userImage")

        # 💬 กล่องข้อความของคนทางซ้าย
        left_text = QLabel("สวัสดี ฉันขอสั่ง ชาเขียวเย็น หวานน้อย 1 แก้วครับ")
        left_text.setObjectName("leftBubble")

        # 🔄 Layout สำหรับฝั่งซ้าย
        left_layout = QHBoxLayout()
        left_layout.addWidget(user_image)
        left_layout.addWidget(left_text)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ใส่ Layout เข้ากับ Layout หลัก
        main_layout.addLayout(right_layout)
        main_layout.addLayout(right_image_layout)
        main_layout.addLayout(left_layout)

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
