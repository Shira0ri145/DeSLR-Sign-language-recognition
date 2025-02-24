FROM python:3.11

WORKDIR /app

# ติดตั้ง ffmpeg (Whisper ต้องใช้)
RUN apt-get update && apt-get install -y ffmpeg

# คัดลอก requirements.txt และติดตั้ง
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมดเข้าไปใน Container
COPY . .

EXPOSE 8888


# คำสั่งเริ่มต้น
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--NotebookApp.token=''"]
