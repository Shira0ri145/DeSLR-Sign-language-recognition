import sys, argparse, tempfile, random
from pathlib import Path

import numpy as np
import soundfile as sf
import torchaudio

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QTextEdit, QMessageBox
)
import simpleaudio as sa

# -------- F5-TTS imports --------
from f5_tts.infer.utils_infer import (
    infer_process, load_model, load_vocoder, preprocess_ref_audio_text,
    remove_silence_for_generated_wav
)
from f5_tts.model import DiT
from f5_tts.model.utils import seed_everything
from f5_tts.cleantext.number_tha import replace_numbers_with_thai
from f5_tts.cleantext.th_repeat import process_thai_repeat
from cached_path import cached_path

# -------- ref audio finder --------
_REF_CANDIDATE_NAMES = ["example_ref.wav"]
REF_TEXT_DEFAULT = "สวัสดีครับ ผมชื่อนนท์ ผมมาจากอำนาจเจริญ"

def find_ref_audio_path(cli_override: str | None = None) -> str | None:
    if cli_override:
        p = Path(cli_override).expanduser().resolve()
        if p.is_file():
            return str(p)
    here = Path(__file__).resolve()
    root_repo = here.parent
    parent_of_repo = root_repo.parent
    candidates = []
    for name in _REF_CANDIDATE_NAMES:
        candidates += [
            root_repo / "sound" / name,
            parent_of_repo / "sound" / name,
            Path.cwd() / "sound" / name,
            Path.cwd() / name,
        ]
    for p in candidates:
        if p.is_file():
            return str(p.resolve())
    return None

def _silence_tuple():
    sr = 22050
    return (sr, np.zeros(int(sr * 0.5), dtype=np.float32))

# -------- model (default only) --------
default_model_base = "hf://VIZINTZOR/F5-TTS-THAI/model_1000000.pt"
vocab_base = "./vocab/vocab.txt"
f5tts_model = None
vocoder = None

def load_f5tts_default():
    global f5tts_model, vocoder
    if vocoder is None:
        vocoder = load_vocoder()
    if f5tts_model is None:
        cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512,
                   text_mask_padding=False, conv_layers=4, pe_attn_head=1)
        f5tts_model = load_model(
            DiT, cfg, str(cached_path(default_model_base)),
            vocab_file=vocab_base, use_ema=True
        )

# -------- fixed params (no UI) --------
SPEED_FIXED = 0.9
REMOVE_SILENCE = True
CROSS_FADE_DURATION = 0.15
NFE_STEP = 32
CFG_STRENGTH = 2.0
MAX_CHARS = 300
LANG_PROCESS = "Default"  # no IPA
SEED_DEFAULT = -1

# -------- worker --------
class TTSWorker(QThread):
    finished = pyqtSignal(str)   # audio_path
    failed = pyqtSignal(str)

    def __init__(self, ref_audio_path: str | None, text: str):
        super().__init__()
        self.ref_audio_path = ref_audio_path
        self.text = text

    def run(self):
        try:
            txt = (self.text or "").strip()
            if not txt:
                self.failed.emit("กรุณากรอกข้อความที่จะสร้าง")
                return

            load_f5tts_default()

            seed_val = SEED_DEFAULT
            if seed_val == -1:
                seed_val = random.randint(0, sys.maxsize)
            seed_everything(seed_val)

            # ref audio + text
            if self.ref_audio_path and Path(self.ref_audio_path).is_file():
                ref_audio, ref_text = preprocess_ref_audio_text(self.ref_audio_path, REF_TEXT_DEFAULT)
            else:
                sr, data = _silence_tuple()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    sf.write(tmp.name, data, int(sr))
                    ref_audio, ref_text = preprocess_ref_audio_text(tmp.name, REF_TEXT_DEFAULT)

            # clean text
            gen_text_cleaned = process_thai_repeat(replace_numbers_with_thai(txt))

            # infer
            final_wave, final_sr, _ = infer_process(
                ref_audio, ref_text, gen_text_cleaned,
                f5tts_model, vocoder,
                cross_fade_duration=CROSS_FADE_DURATION,
                nfe_step=NFE_STEP,
                speed=SPEED_FIXED,
                progress=None,
                cfg_strength=CFG_STRENGTH,
                set_max_chars=MAX_CHARS,
                use_ipa=(LANG_PROCESS == "IPA"),
            )

            # optional remove silence
            if REMOVE_SILENCE:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    sf.write(f.name, final_wave, final_sr)
                    remove_silence_for_generated_wav(f.name)
                    wave, _ = torchaudio.load(f.name)
                final_wave = wave.squeeze().cpu().numpy()

            # write wav
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as outwav:
                sf.write(outwav.name, final_wave, final_sr)
                self.finished.emit(outwav.name)

        except Exception as e:
            self.failed.emit(str(e))

# -------- main window (only textbox + button) --------
class MainWindow(QMainWindow):
    def __init__(self, ref_audio_path: str | None):
        super().__init__()
        self.setWindowTitle("F5-TTS ภาษาไทย (Minimal)")
        self.ref_audio_path = ref_audio_path
        self.sa_obj = None

        w = QWidget(); lay = QVBoxLayout(w)

        self.txt = QTextEdit()
        lay.addWidget(self.txt)

        self.btn = QPushButton("🚀 สร้าง")
        lay.addWidget(self.btn)

        self.setCentralWidget(w)
        self.btn.clicked.connect(self._on_generate)

    def _on_generate(self):
        text = self.txt.toPlainText()
        self.btn.setEnabled(False)
        self.worker = TTSWorker(self.ref_audio_path, text)
        self.worker.finished.connect(self._on_done)
        self.worker.failed.connect(self._on_fail)
        self.worker.start()

    def _on_done(self, audio_path: str):
        # autoplay (no UI shown)
        try:
            if self.sa_obj is not None:
                try: self.sa_obj.stop()
                except: pass
            wave_obj = sa.WaveObject.from_wave_file(audio_path)
            self.sa_obj = wave_obj.play()
        except Exception:
            pass
        self.btn.setEnabled(True)

    def _on_fail(self, msg: str):
        QMessageBox.critical(self, "TTS Error", msg)
        self.btn.setEnabled(True)

# -------- entry --------
def main():
    ap = argparse.ArgumentParser(description="F5-TTS PyQt (Minimal)")
    ap.add_argument("--ref-audio", type=str, default=None,
                    help="ระบุ path ของไฟล์อ้างอิง; ถ้าไม่ระบุ ระบบจะค้นหาให้")
    args = ap.parse_args()

    ref_path = find_ref_audio_path(args.ref_audio)
    app = QApplication(sys.argv)
    win = MainWindow(ref_path)
    win.resize(700, 360)
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
