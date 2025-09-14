import cv2

def open_camera(camera_id=0):
    # เปิดกล้อง (0 คือกล้องหลัก ถ้ามีกล้องหลายตัวเปลี่ยนเป็น 1, 2, ...)
    cap = cv2.VideoCapture(camera_id)

    if not cap.isOpened():
        print("ไม่สามารถเปิดกล้องได้")
        return

    while True:
        # อ่านภาพจากกล้อง
        ret, frame = cap.read()
        if not ret:
            print("ไม่สามารถอ่านภาพจากกล้องได้")
            break

        # แสดงผลภาพ
        cv2.imshow("Camera", frame)

        # กด q เพื่อออก
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # ปล่อยกล้องและปิดหน้าต่าง
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    open_camera()
