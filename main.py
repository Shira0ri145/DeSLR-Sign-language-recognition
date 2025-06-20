from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QMessageBox
)
from PyQt5.QtGui import QKeyEvent, QIcon
from PyQt5.QtCore import Qt, QTimer
from pages.ChatPage import ChatPage
from pages.StartPage import StartPage

class MainApp(QMainWindow):
    def __init__(self, screen_size):
        super().__init__()

        self.setWindowTitle("DeSLR - Chat UI")
        self.default_size = (1024, 600)
        self.resize(screen_size.width(), screen_size.height())
        self.is_fullscreen = True

        # Widget หลักที่ใช้จัดการหน้า
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # หน้าสตาร์ท
        self.start_page = StartPage(self.show_chat_page)
        self.stack.addWidget(self.start_page)

        # หน้าแชท
        self.chat_page = ChatPage(self.show_start_page)
        self.stack.addWidget(self.chat_page)

        # โหลด QSS
        self.setStyleSheet(open("style.qss", encoding="utf-8").read())

    def show_chat_page(self):
        self.stack.setCurrentWidget(self.chat_page)
        QTimer.singleShot(3000, self.chat_page.chatpagestart_camera)
        

    def show_start_page(self):
        self.stack.setCurrentWidget(self.start_page)
        QTimer.singleShot(3000, self.start_page.start_camera)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F11:
            if self.is_fullscreen:
                self.showNormal()
                self.resize(*self.default_size)
            else:
                self.showFullScreen()
            self.is_fullscreen = not self.is_fullscreen

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'ยืนยันการปิด', 'คุณแน่ใจหรือไม่ว่าต้องการออก?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.start_page.stop_camera()
            event.accept()
        else:
            event.ignore()


# ✅ เรียกใช้งานแอป
app = QApplication([])
app.setApplicationName("DeSLR")
app.setWindowIcon(QIcon("assets/user.png"))
screen = app.primaryScreen()
size = screen.size()
window = MainApp(size)
window.showFullScreen()
app.exec()
