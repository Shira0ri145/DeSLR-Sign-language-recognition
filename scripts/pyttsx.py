# scripts/pyttsx.py
import sys
import threading
import traceback
import pyttsx3

# --------- ตั้งค่าและเลือก driver ตาม OS ---------
def _pick_driver():
    if sys.platform.startswith("win"):
        return "sapi5"     # Windows
    elif sys.platform == "darwin":
        return "nsss"      # macOS
    else:
        return "espeak"    # Linux (ควรติดตั้ง espeak-ng)

def _make_engine():
    drv = _pick_driver()
    eng = pyttsx3.init(driverName=drv)
    eng.setProperty("rate", 170)
    eng.setProperty("volume", 1.0)

    # พยายามเลือกเสียงไทย ถ้ามี
    try:
        voices = eng.getProperty("voices") or []
        for v in voices:
            vid   = (getattr(v, "id", "") or "").lower()
            name  = (getattr(v, "name", "") or "").lower()
            langs = [str(L).lower() for L in getattr(v, "languages", []) or []]
            if "thai" in name or "th" in vid or any("th" in L for L in langs):
                eng.setProperty("voice", v.id)
                break
    except Exception:
        pass
    return eng

# ใช้ engine แยกต่อการพูด เพื่อเลี่ยงปัญหา COM/thread
def _speak_blocking(text: str):
    eng = _make_engine()
    try:
        eng.say(text)
        eng.runAndWait()
    finally:
        try:
            eng.stop()
        except Exception:
            pass

def speak(text: str, background: bool = True) -> bool:
    """
    พูดข้อความด้วย pyttsx3
    - background=True: พูดใน thread แยก (ไม่ค้าง UI)
    - คืน True ถ้าเริ่มพูดได้, False ถ้า input ว่างหรือมี error
    """
    if not text:
        return False
    try:
        if background:
            t = threading.Thread(target=_speak_blocking, args=(text,), daemon=True)
            t.start()
        else:
            _speak_blocking(text)
        return True
    except Exception:
        print("[pyttsx] speak error:\n", traceback.format_exc())
        return False

# สำหรับ debug: พิมพ์รายชื่อ voices
def list_voices():
    try:
        eng = _make_engine()
        for v in eng.getProperty("voices") or []:
            print("ID:", v.id, "| Name:", getattr(v, "name", None), "| Langs:", getattr(v, "languages", None))
    except Exception:
        print(traceback.format_exc())

if __name__ == "__main__":
    # ทดสอบเรียกเดี่ยว
    print("Driver:", _pick_driver())
    list_voices()
    speak("สวัสดีครับ ทดสอบระบบเสียงภาษาไทย", background=False)
