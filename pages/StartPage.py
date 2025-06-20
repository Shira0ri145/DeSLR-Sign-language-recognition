from PyQt5.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QFrame, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QSize, QTimer
import qtawesome as qta
from scripts import CameraThread

class StartPage(QWidget):
    def __init__(self, switch_callback):
        super().__init__()

        self.switch_callback = switch_callback
        self.is_camera_on = True

         # --- Main layout ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) 

        # --- Header section ---
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Use HTML and RichText to style "SLR"
        title_label = QLabel('<span style="color: white;">De</span><span style="color: #C2FCEA;">SLR</span>')
        title_label.setObjectName("mainTitle")
        title_label.setTextFormat(Qt.TextFormat.RichText)

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

        # Add header to main layout
        main_layout.addLayout(header_layout)

        self.setLayout(main_layout)

        #  --- Main content layout ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 20, 0, 0)
        content_layout.setSpacing(20)

        # Left: Usage guide
        guide_frame = QFrame()
        guide_layout = QVBoxLayout()
        guide_title = QLabel("เริ่มต้นใช้งานง่ายๆ เพียง “สวัสดี”")
        guide_title.setObjectName("guideTitle")

        hand_sign_label = QLabel("ภาษามือสวัสดีง่ายๆ")
        hand_sign_label.setObjectName("handSignText")

        # Layout for Step 1 and Step 2
        step_layout = QHBoxLayout()
        step1_layout = QVBoxLayout()
        step1 = QLabel("Step 1: มือแตะหน้าผาก")
        step1.setObjectName("guideStep")
        step1_img = QLabel()
        step1_img.setPixmap(QPixmap("assets/signlanghello-1.png").scaled(89, 177, Qt.AspectRatioMode.KeepAspectRatio))

        step1_layout.addWidget(step1)
        step1_layout.addWidget(step1_img)
        step1_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        step2_layout = QVBoxLayout()
        step2 = QLabel("Step 2: เอามือผายออก")
        step2.setObjectName("guideStep")
        step2_img = QLabel()
        step2_img.setPixmap(QPixmap("assets/signlanghello-2.png").scaled(89, 177, Qt.AspectRatioMode.KeepAspectRatio))

        step2_layout.addWidget(step2)
        step2_layout.addWidget(step2_img)
        step2_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        step2_wrapper = QVBoxLayout()
        step2_wrapper.addStretch()
        step2_wrapper.addLayout(step2_layout)

        step_layout.addLayout(step1_layout)
        step_layout.addLayout(step2_wrapper)

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

        camera_frame = QFrame()
        camera_layout = QVBoxLayout()
        camera_frame.setObjectName("cameraFrame")

        self.camera_label = QLabel("Loading camera...")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setFixedSize(640, 360)
        self.camera_label.setStyleSheet("color: gray; background-color: #111; border-radius: 5px;")

        self.camera_thread = CameraThread(camera_id=0, use_mediapipe=True)
        self.camera_thread.frame_updated.connect(self.update_camera_frame)
        self.camera_thread.camera_ready.connect(self.clear_loading_text)
        self.camera_thread.detected_label.connect(self.check_detected_label)
        self.camera_thread.start()

        top_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        mic_button = QPushButton()
        mic_button.setIcon(qta.icon("fa5s.microphone", color="black"))
        mic_button.setObjectName("micButton")
        mic_button.setFixedSize(60, 60)
        mic_button.setIconSize(QSize(27, 27))

        self.camera_button = QPushButton()
        self.camera_button.setIcon(qta.icon("fa5s.video", color="black"))  # เริ่มต้นเป็นเปิดกล้อง
        self.camera_button.setObjectName("cameraButton")
        self.camera_button.setFixedSize(60, 60)
        self.camera_button.setIconSize(QSize(25, 25))
        self.camera_button.clicked.connect(self.toggle_camera)

        open_button = QPushButton()
        open_button.setIcon(qta.icon("fa5s.phone"))
        open_button.setObjectName("openButton")
        open_button.setFixedSize(60, 60)
        open_button.setIconSize(QSize(20, 20))
        open_button.clicked.connect(self.handle_open)

        left_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        right_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)


        button_layout = QHBoxLayout()
        button_layout.addItem(left_spacer)
        button_layout.addWidget(mic_button, alignment=Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(open_button, alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.camera_button, alignment=Qt.AlignmentFlag.AlignLeft)
        button_layout.addItem(right_spacer)

        camera_layout.addItem(top_spacer)
        camera_layout.addWidget(self.camera_label, alignment=Qt.AlignmentFlag.AlignCenter)
        camera_layout.addItem(bottom_spacer)
        camera_layout.addLayout(button_layout)

        camera_frame.setLayout(camera_layout)

        content_layout.addWidget(guide_frame)
        content_layout.addWidget(camera_frame)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def check_detected_label(self, label):
        if label == "hello":
            self.handle_open()
            print("go Chat")

    # Create and start a new camera thread
    def start_camera(self):
        if self.camera_thread is not None:
            try:
                self.camera_thread.frame_updated.disconnect()
            except:
                pass
            try:
                self.camera_thread.stop()
            except:
                pass
        self.camera_thread = CameraThread(camera_id=2, use_mediapipe=True)
        self.camera_thread.frame_updated.connect(self.update_camera_frame)
        self.camera_thread.camera_ready.connect(self.clear_loading_text)
        self.camera_thread.detected_label.connect(self.check_detected_label)
        self.camera_thread.start()

    # Called when you want to stop the camera
    def stop_camera(self):
        if self.camera_thread.isRunning():
            self.camera_thread.stop()
        try:
            self.camera_thread.frame_updated.disconnect()
        except (TypeError, RuntimeError):
            pass
        try:
            self.camera_label.clear()
            self.camera_label.setText("Loading camera...")
            self.camera_label.setStyleSheet("color: gray; background-color: #111; border-radius: 5px;")
        except Exception as e:
            print("Error resetting camera label:", e)

    def handle_open(self):
        self.stop_camera()
        QTimer.singleShot(300, self.switch_callback)
        
        
    def closeEvent(self, event):
        self.camera_thread.stop()
        event.accept()


    # Receive and display camera image
    def update_camera_frame(self, image: QImage):
        if not image.isNull():
            self.camera_label.setScaledContents(True)
            pixmap = QPixmap.fromImage(image)
            self.camera_label.setPixmap(pixmap)

    def clear_loading_text(self):
        self.camera_label.setText("")

    def toggle_camera(self):
        if self.is_camera_on:
            self.camera_button.setIcon(qta.icon("fa5s.video-slash", color="red")) 
        else:
            self.camera_button.setIcon(qta.icon("fa5s.video", color="black"))

        self.is_camera_on = not self.is_camera_on
