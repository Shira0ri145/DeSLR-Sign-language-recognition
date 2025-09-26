from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtGui import QIcon, QKeyEvent
from PyQt5.QtCore import QTimer, Qt
import sys

from pages.home_page import HomePage
from pages.start_page import StartPage


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DeSLR - Chat UI")
        self.setWindowIcon(QIcon("assets/user.png"))

        # โหลด QSS
        self.setStyleSheet(open("style.qss", encoding="utf-8").read())

        # ขนาดเริ่มต้นเมื่อออกจากโหมดเต็มจอ
        self.default_size = (1024, 600)
        self.resize(*self.default_size)

        # สร้าง Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # สร้างหน้า
        self.home_page = HomePage(on_start=self.show_start_page)
        self.start_page = StartPage(on_back=self.show_home_page)

        # ใส่ลง Stack: 0 = Home, 1 = Start
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.start_page)

        # เริ่มที่หน้า Home
        self.stack.setCurrentWidget(self.home_page)

    def keyPressEvent(self, event: QKeyEvent):
        # กด F11 สลับ Fullscreen / Normal
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
                self.resize(*self.default_size)  # กลับมาขนาดปกติที่กำหนด
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'ยืนยันการปิด', 'คุณแน่ใจหรือไม่ว่าต้องการออก?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.start_page.stop_camera()
            except Exception:
                pass
            event.accept()
        else:
            event.ignore()

    def show_home_page(self):
        # ปิดกล้องใน StartPage ก่อนกลับหน้า Home
        try:
            self.start_page.stop_camera()
        except Exception:
            pass
        self.stack.setCurrentWidget(self.home_page)

    def show_start_page(self):
        self.stack.setCurrentWidget(self.start_page)
        # เปิดกล้องหลังเข้า StartPage
        QTimer.singleShot(150, self.start_page.ensure_camera_running)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("DeSLR")

    window = MainApp()
    window.showFullScreen()  # ← เริ่มแบบเต็มจอทันที
    sys.exit(app.exec())

