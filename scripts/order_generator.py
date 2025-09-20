# scripts/order_generator.py

# ===== พจนานุกรม: เพิ่ม/แก้แค่ตรงนี้ที่เดียว =====
GREETING_WORDS = {
    "hello": "สวัสดีครับ",
    "thank": "ขอบคุณครับ",
    "recommended": "แนะนำ",
    "tawlai": "เท่าไหร่",
}

MENU_WORDS = {
    "greentea": "ชาเขียว",
    "thaitea": "ชาไทย",
    "cocoa": "โกโก้",
    "americano": "อเมริกาโน่",
    "latte": "ลาเต้",
    "espresso": "เอสเปรสโซ่",
}

def get_allowed_words() -> set:
    """รวมคีย์ทั้งหมดที่อนุญาตให้พิมพ์"""
    return set(GREETING_WORDS.keys()) | set(MENU_WORDS.keys())

def validate_tokens(tokens) -> list[str]:
    """คืนลิสต์คำที่ไม่รองรับ (ถ้าลิสต์ว่าง แปลว่าผ่าน)"""
    allowed = get_allowed_words()
    return [t for t in tokens if t not in allowed and t.strip()]

def generate_order(words):
    greeting = ""
    is_thank = False
    is_recommend = False
    is_question = False
    drink = ""

    for i, word in enumerate(words):
        if word == "hello":
            greeting = GREETING_WORDS["hello"]
            # ถัดจาก hello เป็น recommended → ประโยคแนะนำพิเศษ
            if i + 1 < len(words) and words[i + 1] == "recommended":
                return "สวัสดีครับ ขอแนะนำเครื่องดื่มครับ"

        elif word == "thank":
            is_thank = True
        elif word == "recommended":
            is_recommend = True
        elif word == "tawlai":
            is_question = True
        elif word in MENU_WORDS:
            drink = MENU_WORDS[word]

    parts = []

    if greeting:
        parts.append(greeting)

    if is_recommend:
        if drink:
            parts.append(f"ขอแนะนำเป็น {drink} ครับ")
        else:
            parts.append("ขอแนะนำเครื่องดื่มครับ")


    if is_thank and not parts:
        return "ขอบคุณครับ"

    return " ".join(parts) if parts else "สั่งไม่ถูกครับ"
