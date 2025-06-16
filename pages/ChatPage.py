from PyQt5.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLineEdit, QPushButton
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer


from scripts import CameraThread, generate_order, generate_tts_from_text, WhisperASR

class ChatPage(QWidget):
    def __init__(self, show_start_page_callback):
        super().__init__()
        self.show_start_page_callback = show_start_page_callback

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop)

        back_button = QPushButton("ย้อนกลับ")
        back_button.clicked.connect(self.on_back_button_click)
        main_layout.addWidget(back_button)

        title_label = QLabel('<span style="color: white;">De</span><span style="color: #C2FCEA;">SLR</span>')
        title_label.setObjectName("mainTitle")
        title_label.setTextFormat(Qt.RichText)
        main_layout.addWidget(title_label)

        input_layout = QHBoxLayout()
        self.barista_input = QLineEdit()
        self.barista_input.setPlaceholderText("พิมพ์ข้อความที่ต้องการให้ Barista พูด...")
        self.barista_input.setMinimumHeight(32)
        self.speak_button = QPushButton("พูด")
        self.speak_button.clicked.connect(self.handle_speak)

        input_layout.addWidget(self.barista_input)
        input_layout.addWidget(self.speak_button)
        main_layout.addLayout(input_layout)

        chat_layout = QVBoxLayout()
        chat_layout.setSpacing(20)

        # Barista chat
        barista_chat_layout = QHBoxLayout()
        barista_chat_layout.setAlignment(Qt.AlignCenter)

        # Barista camera
        self.barista_img = QLabel("Loading camera...")
        self.barista_img.setAlignment(Qt.AlignCenter)
        self.barista_img.setFixedSize(280, 180)
        self.barista_img.setStyleSheet("color: gray; background-color: #111; border-radius: 5px;")
        self.barista_img.setObjectName("chatImage")

        self.barista_camera_thread = CameraThread(camera_id=0)
        self.barista_camera_thread.frame_updated.connect(self.update_barista_camera_frame)
        self.barista_camera_thread.camera_ready.connect(self.clear_barista_loading_text)
        # self.barista_camera_thread.start()

        barista_frame = QFrame()
        barista_frame.setObjectName("chatBubbleBarista")
        barista_frame_layout = QVBoxLayout(barista_frame)

        barista_name = QLabel("Barista")
        barista_name.setObjectName("chatNameBarista")

        self.barista_text = QLabel("สวัสดี , วันนี้สั่งเมนูอะไรดีคะ ?")
        self.barista_text.setObjectName("chatTextBarista")
        self.barista_text.setWordWrap(True)
        self.barista_text.setMinimumWidth(600)

        barista_frame_layout.addWidget(barista_name)
        barista_frame_layout.addWidget(self.barista_text)

        barista_chat_layout.addWidget(barista_frame)
        barista_chat_layout.addWidget(self.barista_img)

        # User chat
        user_chat_layout = QHBoxLayout()
        user_chat_layout.setAlignment(Qt.AlignCenter)

        self.user_img = QLabel("Loading camera...")
        self.user_img.setAlignment(Qt.AlignCenter)
        self.user_img.setFixedSize(280, 180)
        self.user_img.setStyleSheet("color: gray; background-color: #111; border-radius: 5px;")

        self.user_camera_thread = CameraThread(camera_id=1)
        self.user_camera_thread.frame_updated.connect(self.update_user_camera_frame)
        self.user_camera_thread.camera_ready.connect(self.clear_user_loading_text)
        # self.user_camera_thread.start()

        user_frame = QFrame()
        user_frame.setObjectName("chatBubbleUser")
        user_frame_layout = QVBoxLayout(user_frame)

        user_name = QLabel("คุณ (คนสั่ง)")
        user_name.setObjectName("chatNameUser")

        self.user_text = QLabel("กำลังรอเสียงพูด...")
        self.user_text.setObjectName("chatTextUser")
        self.user_text.setWordWrap(True)
        self.user_text.setMinimumWidth(600)

        user_frame_layout.addWidget(user_name)
        user_frame_layout.addWidget(self.user_text)

        user_chat_layout.addWidget(self.user_img)
        user_chat_layout.addWidget(user_frame)

        chat_layout.addLayout(barista_chat_layout)
        chat_layout.addLayout(user_chat_layout)
        main_layout.addLayout(chat_layout)

        # ✅ Start Whisper ASR
        # self.whisper = WhisperASR()
        # self.whisper.result_ready.connect(self.on_transcript)
        # self.asr_timer = QTimer()
        # self.asr_timer.setInterval(5000)  # หรือปรับความถี่ตามที่ต้องการ
        # self.asr_timer.timeout.connect(self.whisper.process_audio)
        # self.whisper.start()
        # self.asr_timer.start()

        self.setLayout(main_layout)

    def update_barista_camera_frame(self, image: QImage):
        self.barista_img.setPixmap(QPixmap.fromImage(image))

    def update_user_camera_frame(self, image: QImage):
        self.user_img.setPixmap(QPixmap.fromImage(image))
    
    def clear_barista_loading_text(self):
        self.barista_img.setText("")

    def clear_user_loading_text(self):
        self.user_img.setText("")

    def closeEvent(self, event):
        self.user_camera_thread.stop()
        self.barista_camera_thread.stop()
        # self.whisper.stop()
        # self.asr_timer.stop()

        event.accept()

    def on_back_button_click(self):
        self.user_camera_thread.stop()
        self.barista_camera_thread.stop()
        # self.whisper.stop()
        # self.asr_timer.stop()

        # self.user_camera_thread.frame_updated.disconnect()

        # 2. ล้างภาพ User (กัน error)
        try:
            self.user_camera_thread.frame_updated.disconnect()
        except (TypeError, RuntimeError):
            pass
        try:
            self.user_img.clear()
            self.user_img.setText("Loading camera...")
            self.user_img.setStyleSheet("color: gray; background-color: #111; border-radius: 5px;")
        except Exception:
            pass

        # 3. ล้างภาพ Barista (กัน error)
        try:
            self.barista_camera_thread.frame_updated.disconnect()
        except (TypeError, RuntimeError):
            pass
        try:
            self.barista_img.clear()
            self.barista_img.setText("Loading camera...")
            self.barista_img.setStyleSheet("color: gray; background-color: #111; border-radius: 5px;")
        except Exception:
            pass

        self.show_start_page_callback()

    
    # def on_transcript(self, text):
    #     print("ถอดเสียงได้:", text)
    #     self.user_text.setText(text)


    def handle_speak(self):
        text = self.barista_input.text().strip()
        if text:
            words = text.split()
            sentence = generate_order(words)
            self.barista_text.setText(sentence)
            generate_tts_from_text(sentence)  
