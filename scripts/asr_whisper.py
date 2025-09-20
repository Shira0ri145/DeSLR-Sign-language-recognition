import queue
import numpy as np
import sounddevice as sd
import torch
from transformers import pipeline
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QThread

class WhisperASR(QObject):
    result_ready = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.running = False
        self.queue = queue.Queue()

        # ตั้งค่าระบบเสียง
        self.samplerate = 16000
        self.blocksize = 16000
        self.channels = 1

        # โหลดโมเดล Whisper
        model_name = "biodatlab/whisper-th-medium-combined"
        device = 0 if torch.cuda.is_available() else "cpu"
        self.pipe = pipeline(
            task="automatic-speech-recognition",
            model=model_name,
            chunk_length_s=30,
            device=device,
        )

        # Stream เสียง
        self.stream = None

    def start(self):
        self.running = True
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            channels=self.channels,
            dtype="float32",
            callback=self.audio_callback,
        )
        self.stream.start()

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print("[WhisperASR] Status:", status)
        audio = indata[:, 0].copy()
        self.queue.put(audio)

    def process_audio(self):
        if not self.queue.empty():
            audio_data = []
            while not self.queue.empty():
                audio_data.extend(self.queue.get())

            audio_array = np.array(audio_data, dtype=np.float32)

            # ตรวจสอบพลังงานเสียง
            energy = np.sqrt(np.mean(audio_array**2))
            if energy < 0.03:
                print("[WhisperASR] ข้ามเสียงเงียบ")
                return

            try:
                print("[WhisperASR] ถอดเสียง...")
                result = self.pipe(audio_array, generate_kwargs={"language": "<|th|>", "task": "transcribe"})
                transcript = result["text"].strip()
                if transcript:
                    self.result_ready.emit(transcript)

            except Exception as e:
                print(f"[WhisperASR] ERROR: {e}")
                self.result_ready.emit(f"[ERROR] {e}")
