import random
import tempfile
import numpy as np
import torchaudio
import soundfile as sf
import simpleaudio as sa

from f5_tts.infer.utils_infer import (
    infer_process, load_model, load_vocoder,
    preprocess_ref_audio_text, remove_silence_for_generated_wav
)
from f5_tts.model.utils import seed_everything
from f5_tts.model import DiT
from f5_tts.cleantext.number_tha import replace_numbers_with_thai
from f5_tts.cleantext.th_repeat import process_thai_repeat
from cached_path import cached_path

# -------- fixed paths --------
default_model_base = "hf://VIZINTZOR/F5-TTS-THAI/model_1000000.pt"  # ✅ ใช้รุ่นเดียวกับ PyQt
vocab_base = "./vocab/vocab.txt"
ref_audio_path = "./sound/example_ref.wav"
ref_text = "สวัสดีครับ ผมชื่อนนท์ ผมมาจากอำนาจเจริญ"

# ถ้าคู่ ref ไม่แมตช์ ให้ใช้ไฟล์เงียบแทน (เหมือน PyQt)
USE_SILENT_REF = False  # ← ลองตั้ง True ถ้าเสียงเพี้ยน

def _silence_tuple():
    sr = 22050
    return (sr, np.zeros(int(sr * 0.5), dtype=np.float32))

print("กำลังโหลดโมเดล TTS...")
model_cfg = dict(
    dim=1024, depth=22, heads=16, ff_mult=2,
    text_dim=512, conv_layers=4,
    # ✅ ให้ตรงกับตัว PyQt
    text_mask_padding=False,
    pe_attn_head=1,
)
model = load_model(
    DiT, model_cfg, str(cached_path(default_model_base)),
    vocab_file=vocab_base, use_ema=True
)
vocoder = load_vocoder()
print("โหลดโมเดลเรียบร้อยแล้ว")

def generate_tts_from_text(text: str, output_path="output.wav"):
    cleaned_text = process_thai_repeat(replace_numbers_with_thai(text))

    # -------- reference conditioning --------
    if USE_SILENT_REF:
        sr, data = _silence_tuple()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            sf.write(tmp.name, data, int(sr))
            ref_audio, ref_text_local = preprocess_ref_audio_text(tmp.name, ref_text)
    else:
        ref_audio, ref_text_local = preprocess_ref_audio_text(ref_audio_path, ref_text)
    # ---------------------------------------

    # random seed (เหมือน PyQt: สุ่มทุกครั้ง)
    seed = random.randint(0, 2**31 - 1)
    seed_everything(seed)

    # ❗พารามิเตอร์ให้เหมือน PyQt เท่าที่เป็นไปได้
    final_wave, final_sr, _ = infer_process(
        ref_audio, ref_text_local, cleaned_text,
        model, vocoder,
        cross_fade_duration=0.15,
        nfe_step=32,
        speed=0.9,
        cfg_strength=2.0,
        # target_rms และ sway_sampling_coef เอาออกให้เหมือน PyQt
        set_max_chars=300,
        progress=None,
        # ไม่ใช้ IPA ให้เหมือน PyQt
    )

    # post-process: ตัดเงียบแล้วโหลดกลับ
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        sf.write(tmp.name, final_wave, final_sr)
        remove_silence_for_generated_wav(tmp.name)
        final_wave, _ = torchaudio.load(tmp.name)

    final_wave = final_wave.squeeze().cpu().numpy()
    if final_wave.ndim == 1:
        final_wave = final_wave.reshape(-1, 1)

    sf.write(output_path, final_wave, final_sr)

    # เล่นเสียง
    wave_obj = sa.WaveObject.from_wave_file(output_path)
    play_obj = wave_obj.play()
    print(f"TTS พูดเสร็จแล้ว: {output_path}")

if __name__ == "__main__":
    # ถ้าเปิดแล้วเสียงยังเพี้ยน ให้ลองตั้ง USE_SILENT_REF=True
    generate_tts_from_text("ทดสอบการพูดภาษาไทยครับ")
