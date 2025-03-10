import sys
import queue
import threading
import sounddevice as sd
import numpy as np
import whisper
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal

# โหลดโมเดล Whisper
model = whisper.load_model("base")  # เลือกขนาดเล็กหน่อยให้เร็ว

class TranscriberThread(QThread):
    result_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.q = queue.Queue()

    def callback(self, indata, frames, time, status):
        self.q.put(indata.copy())

    def run(self):
        with sd.InputStream(channels=1, samplerate=16000, callback=self.callback):
            buffer = np.empty((0, 1), dtype=np.float32)
            while self.running:
                try:
                    data = self.q.get(timeout=1)
                    buffer = np.vstack((buffer, data))
                    if len(buffer) > 16000 * 3:  # ทุก 3 วินาที
                        audio_chunk = buffer[-16000 * 3:]  # เอาแค่ 3 วิล่าสุด
                        buffer = buffer[-16000 * 3:]  # ตัดขนาด buffer
                        result = model.transcribe(audio_chunk.flatten(), language="th")
                        self.result_ready.emit(result["text"])
                except queue.Empty:
                    continue

    def stop(self):
        self.running = False
        self.wait()

class VoiceTypingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Typing with Whisper")
        layout = QVBoxLayout()
        self.textbox = QTextEdit()
        layout.addWidget(self.textbox)
        self.setLayout(layout)

        self.transcriber = TranscriberThread()
        self.transcriber.result_ready.connect(self.update_text)
        self.transcriber.start()

    def update_text(self, text):
        self.textbox.append(text)

    def closeEvent(self, event):
        self.transcriber.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoiceTypingApp()
    window.show()
    sys.exit(app.exec_())
