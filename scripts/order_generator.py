# scripts/order_generator.py

def generate_order(words):
        # Mapping คำสั้นๆไปหาคำสวยๆ
        COMMUNICATION_WORDS = {
            "สวัสดี": "greet",
            "นี้": "greet",
            "วันนี้": "greet",
            "รับ": "greet",
            "อะไร": "greet",
            "ขอบคุณ": "thank",
            "แนะนำ": "recommend",
            "วัน": "one",
            "ทั้งหมด": "tangmod",
            "เท่าไหร่": "tawlai",
            "ดื่ม": "drink"
        }

        MENU_WORDS = {
            "ชา": "ชา", 
            "โกโก้": "โกโก้", 
            "อเมริกาโน่": "อเมริกาโน่", 
            "ลาเต้": "ลาเต้"
        }

        OPTION_WORDS = {
            "เขียว": "เขียว", 
            "ไทย": "ไทย", 
            "ดำ": "ดำ"
        }

        SWEETNESS_WORDS = {
            "หวาน": "หวาน",
            "น้อย": "น้อย",
            "ปกติ": "ปกติ",
            "มาก": "มาก",
            "ไม่": "ไม่"
        }

        TEMPERATURE_WORDS = {
            "ร้อน": "ร้อน", 
            "เย็น": "เย็น", 
            "ปั่น": "ปั่น"
        }

        # เตรียมตัวแปร
        greeting = ""
        today_word = ""
        recommend = False
        menu = ""
        option = ""
        temp = ""
        sweet = ""
        
        has_want = False
        has_drink = False
        has_question = False


        # เช็คคำในแต่ละหมวด
        for word in words:
            if word == "สวัสดี":
                greeting = "สวัสดีครับ"
            if word in ["วันนี้", "นี้"]:
                today_word = "วันนี้"
            if word in MENU_WORDS:
                menu = MENU_WORDS[word]
            if word in OPTION_WORDS:
                option = OPTION_WORDS[word]
            if word in TEMPERATURE_WORDS:
                temp = TEMPERATURE_WORDS[word]
            if word in SWEETNESS_WORDS:
                sweet += SWEETNESS_WORDS[word]
            if word == "แนะนำ":
                recommend = True
            if word == "อยาก":
                has_want = True
            if word == "ดื่ม":
                has_drink = True
            if word == "อะไร":
                has_question = True


        # รวม menu + option + temp + sweet เป็นชื่อเครื่องดื่ม
        drink = ""
        if menu:
            drink = menu
            if option:
                drink += option
            if temp:
                drink += temp
            if sweet:
                drink += sweet

          # === แยกส่วน greeting + ดื่มอะไร ===
        greeting_sentence = ""
        if greeting:
            greeting_sentence = greeting
            if today_word:
                greeting_sentence += f" {today_word}"

        if has_drink:
            if has_question:
                drink_query = "ดื่มอะไรดีครับ"
            else:
                drink_query = "ดื่ม"
                
            if greeting_sentence:
                return f"{greeting_sentence} {drink_query}"
            elif today_word:
                return f"{today_word} {drink_query}"
            else:
                return drink_query


        # กรณีแนะนำ
        if recommend:
            if "สวัสดี" in words and ("วันนี้" in words or "นี้" in words):
                if drink:
                    return f"{greeting} วันนี้ขอแนะนำเป็น {drink} ครับ"
                else:
                    return f"{greeting} วันนี้ขอแนะนำเครื่องดื่มครับ"
            if greeting:
                if drink:
                    return f"{greeting} ขอแนะนำเป็น {drink} ครับ"
                else:
                    return f"{greeting} ขอแนะนำเครื่องดื่มครับ"
            elif "วันนี้" in words or "นี้" in words:
                if drink:
                    return f"วันนี้ขอแนะนำเป็น {drink} ครับ"
                else:
                    return f"วันนี้ ขอแนะนำเครื่องดื่มครับ"
            else:
                if drink:
                    return f"ขอแนะนำเป็น {drink} ครับ"
                else:
                    return "ขอแนะนำเครื่องดื่มครับ"

        # กรณีมีแค่ทักทาย
        if greeting_sentence:
            return greeting_sentence

        if "ขอบคุณ" in words:
            return "ขอบคุณครับ"
        
        parts = []
        if drink:
            parts.append(f"ขอ {drink}")
        if drink:
            parts.append("1 แก้วครับ")

        return " ".join(parts)