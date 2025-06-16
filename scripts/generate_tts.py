import random
import tempfile
import torch
import torchaudio
import soundfile as sf
from PyQt5.QtMultimedia import QSound

from f5_tts.infer.utils_infer import (
    infer_process,
    load_model,
    load_vocoder,
    preprocess_ref_audio_text,
    remove_silence_for_generated_wav,
)
from f5_tts.model.utils import seed_everything
from f5_tts.model import DiT
from cleantext.number_tha import replace_numbers_with_thai
from cleantext.th_repeat import process_thai_repeat
from cached_path import cached_path

default_model_base = "hf://VIZINTZOR/F5-TTS-THAI/model_500000.pt"
vocab_base = "./vocab/vocab.txt"
ref_audio_path = "./example_ref.wav"
ref_text = "สวัสดีครับ ผมชื่อนนท์ ผมมาจากอำนาจเจริญ"

print("กำลังโหลดโมเดล TTS...")
model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
model = load_model(DiT, model_cfg, str(cached_path(default_model_base)), vocab_file=vocab_base, use_ema=True)
vocoder = load_vocoder()
print("โหลดโมเดลเรียบร้อยแล้ว")

def generate_tts_from_text(text: str, output_path="output.wav"):
    cleaned_text = process_thai_repeat(replace_numbers_with_thai(text))
    ref_audio, _ = preprocess_ref_audio_text(ref_audio_path, ref_text)

    seed = random.randint(0, 99999999)
    seed_everything(seed)

    final_wave, final_sr, _ = infer_process(
        ref_audio, ref_text, cleaned_text, model, vocoder,
        cross_fade_duration=0.15, nfe_step=32, speed=0.9,
        cfg_strength=2, target_rms=0.1, sway_sampling_coef=-1,
        fix_duration=None, set_max_chars=250, progress=None,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        sf.write(tmp.name, final_wave, final_sr)
        remove_silence_for_generated_wav(tmp.name)
        final_wave, _ = torchaudio.load(tmp.name)
    final_wave = final_wave.squeeze().cpu().numpy()

    sf.write(output_path, final_wave, final_sr)
    QSound.play(output_path)
    print(f"TTS พูดเสร็จแล้ว: {output_path}")
