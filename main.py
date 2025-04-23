from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget
)
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt
from pages.ChatPage import ChatPage
from pages.StartPage import StartPage


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
