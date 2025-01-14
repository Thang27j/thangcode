import cv2
import pytesseract
from tkinter import Tk, Label, Frame, Button
from PIL import Image, ImageTk
import serial
import mysql.connector
from datetime import datetime
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="thang270724@",
        database="cơ_sơ_dữ_liệu_biển_số_xe"
    )
    print("Kết nối cơ sở dữ liệu thành công.")
except mysql.connector.Error as err:
    print(f"Lỗi kết nối cơ sở dữ liệu: {err}")
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
try:
    arduino = serial.Serial(port="COM8", baudrate=9600, timeout=1)
    print("Kết nối Arduino thành công.")
except Exception as e:
    print(f"Lỗi kết nối Arduino: {e}")
root = Tk()
root.title("Hệ thống thu phí tự động")
root.geometry("1000x600")
frame_entry = Frame(root, relief="ridge", borderwidth=2)
frame_entry.pack(side="left", padx=10, pady=10, fill="both", expand=True)
frame_exit = Frame(root, relief="ridge", borderwidth=2)
frame_exit.pack(side="right", padx=10, pady=10, fill="both", expand=True)
label_title_entry = Label(frame_entry, text="LÀN VÀO", font=("Arial", 16, "bold"))
label_title_entry.pack(pady=5)
label_title_exit = Label(frame_exit, text="LÀN RA", font=("Arial", 16, "bold"))
label_title_exit.pack(pady=5)
label_camera_entry = Label(frame_entry)
label_camera_entry.pack(pady=5)
label_plate_entry = Label(frame_entry, text="Biển số: ", font=("Arial", 12))
label_plate_entry.pack(pady=5)
label_camera_exit = Label(frame_exit)
label_camera_exit.pack(pady=5)
label_plate_exit = Label(frame_exit, text="Biển số: ", font=("Arial", 12))
label_plate_exit.pack(pady=5)
def manual_open_entry():
    arduino.write(b'OPEN_ENTRY\n')
def manual_close_entry():
    arduino.write(b'CLOSE_ENTRY\n')
def manual_open_exit():
    arduino.write(b'OPEN_EXIT\n')
def manual_close_exit():
    arduino.write(b'CLOSE_EXIT\n')
def exit_system():
    if db:
        db.close()
    if arduino:
        arduino.close()
    cap.release()
    cap_exit.release()
    cv2.destroyAllWindows()
    root.quit()
control_frame_entry = Frame(frame_entry)
control_frame_entry.pack(pady=10)
button_open_entry = Button(control_frame_entry, text="Mở cổng vào", command=manual_open_entry, width=15)
button_open_entry.pack(side="left", padx=5)
button_close_entry = Button(control_frame_entry, text="Đóng cổng vào", command=manual_close_entry, width=15)
button_close_entry.pack(side="left", padx=5)
control_frame_exit = Frame(frame_exit)
control_frame_exit.pack(pady=10)
button_open_exit = Button(control_frame_exit, text="Mở cổng ra", command=manual_open_exit, width=15)
button_open_exit.pack(side="left", padx=5)
button_close_exit = Button(control_frame_exit, text="Đóng cổng ra", command=manual_close_exit, width=15)
button_close_exit.pack(side="left", padx=5)
exit_button = Button(root, text="Thoát hệ thống", command=exit_system, bg="red", fg="white", font=("Arial", 12))
exit_button.pack(side="bottom", pady=10)
cap = cv2.VideoCapture(1)
cap_exit = cv2.VideoCapture(0)
def process_entry_lane(plate_number):
    plate_number = plate_number.strip().replace(" ", "").replace(".", "").replace("-", "").upper()
    if not (len(plate_number) == 8 and plate_number[0:2].isdigit() and plate_number[2:3].isalpha() and plate_number[3:].isdigit()):
        print(f"Định dạng biển số không hợp lệ: {plate_number}")
        return False, "Định dạng biển số không hợp lệ"
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM xe_đã_đăng_ký WHERE Biển_số = %s"
    cursor.execute(query, (plate_number,))
    result = cursor.fetchone()
    if result:
        entry_time = datetime.now()
        insert_query = """
            INSERT INTO lịch_sử_vào_bãi (biển_số, thời_gian_vao_bãi)
            VALUES (%s, %s)
        """
        cursor.execute(insert_query, (plate_number, entry_time))
        db.commit()
        cursor.close()
        return True, "Biển số đã đăng ký, ghi nhận thời gian vào bãi thành công"
    else:
        try:
            entry_time = datetime.now()
            insert_query = """
                INSERT INTO xe_chưa_đăng_ký (biển_số, thời_gian_vào_bãi)
                VALUES (%s, %s)
            """
            cursor.execute(insert_query, (plate_number, entry_time))
            db.commit()
            cursor.close()
            return True, "Biển số chưa đăng ký, đã ghi nhận thông tin"
        except mysql.connector.Error as err:
            cursor.close()
            print(f"Lỗi khi xử lý xe chưa đăng ký: {err}")
            return False, "Lỗi xử lý thông tin"
def process_exit_lane(plate_number):
    plate_number = plate_number.strip().replace(" ", "").replace(".", "").replace("-", "").upper()
    if not (len(plate_number) == 8 and plate_number[0:2].isdigit() and plate_number[2:3].isalpha() and plate_number[3:].isdigit()):
        print(f"Định dạng biển số không hợp lệ: {plate_number}")
        return False, "Định dạng biển số không hợp lệ"
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM xe_đã_đăng_ký WHERE Biển_số = %s"
    cursor.execute(query, (plate_number,))
    vehicle_data = cursor.fetchone()
    if vehicle_data:
        try:
            entry_query = """
                SELECT thời_gian_vao_bãi FROM lịch_sử_vào_bãi
                WHERE Biển_số = %s
                ORDER BY thời_gian_vao_bãi DESC
                LIMIT 1
            """
            cursor.execute(entry_query, (plate_number,))
            entry_data = cursor.fetchone()
            if entry_data:
                entry_time = entry_data["thời_gian_vao_bãi"]
                current_time = datetime.now()
                parking_duration_minutes = (current_time - entry_time).total_seconds() / 60
                total_parking_time = int(parking_duration_minutes)
                minute_rate = 10000
                parking_fee = total_parking_time * minute_rate
                balance = vehicle_data["Số_dư"]
                if balance >= parking_fee:
                    insert_exit_query = """
                        INSERT INTO lịch_sử_ra_bãi (biển_số, thời_gian_ra_bãi, phí)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_exit_query, (plate_number, current_time, parking_fee))
                    new_balance = balance - parking_fee
                    update_balance_query = """
                        UPDATE xe_đã_đăng_ký
                        SET Số_dư = %s
                        WHERE Biển_số = %s
                    """
                    cursor.execute(update_balance_query, (new_balance, plate_number))
                    db.commit()
                    return True, f"Thanh toán thành công. Phí: {parking_fee} VND"
                else:
                    return False, "Số dư không đủ"
            else:
                return False, "Không tìm thấy lịch sử vào bãi"
        except mysql.connector.Error as err:
            return False, f"Lỗi: {err}"
        finally:
            cursor.close()
    else:
        try:
            entry_query = """
                SELECT thời_gian_vào_bãi FROM xe_chưa_đăng_ký
                WHERE biển_số = %s AND thời_gian_ra_bãi IS NULL
            """
            cursor.execute(entry_query, (plate_number,))
            entry_data = cursor.fetchone()
            if entry_data:
                current_time = datetime.now()
                entry_time = entry_data["thời_gian_vào_bãi"]
                parking_duration_minutes = (current_time - entry_time).total_seconds() / 60
                total_parking_time = int(parking_duration_minutes)
                minute_rate = 10000
                parking_fee = total_parking_time * minute_rate
                update_query = """
                    UPDATE xe_chưa_đăng_ký
                    SET thời_gian_ra_bãi = %s, phí = %s
                    WHERE biển_số = %s AND thời_gian_ra_bãi IS NULL
                """
                cursor.execute(update_query, (current_time, parking_fee, plate_number))
                db.commit()
                cursor.close()
                return False, f"Xe chưa đăng ký. Phí: {parking_fee} VND. Vui lòng thanh toán tại quầy"
            else:
                cursor.close()
                return False, "Không tìm thấy thông tin xe vào bãi"
        except mysql.connector.Error as err:
            cursor.close()
            return False, f"Lỗi: {err}"
def update_entry_lane():
    ret, frame = cap.read()
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        label_camera_entry.imgtk = imgtk
        label_camera_entry.configure(image=imgtk)
        if arduino.in_waiting > 0:
            arduino_message = arduino.readline().decode('utf-8').strip()
            if arduino_message == "DETECTED_ENTRY":
                print("Xe phát hiện tại làn vào.")
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                detected_plate = pytesseract.image_to_string(thresh).strip()
                label_plate_entry.config(text=f"Biển số: {detected_plate}")
                print(f"Biển số nhận diện: {detected_plate}")
                if detected_plate:
                    success, _ = process_entry_lane(detected_plate)
                    if success:
                        arduino.write(b'OPEN_ENTRY\n')
    root.after(10, update_entry_lane)
def update_exit_lane():
    ret, frame = cap_exit.read()
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        label_camera_exit.imgtk = imgtk
        label_camera_exit.configure(image=imgtk)
        if arduino.in_waiting > 0:
            arduino_message = arduino.readline().decode('utf-8').strip()
            if arduino_message == "DETECTED_EXIT":
                print("Xe phát hiện tại làn ra.")
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                detected_plate = pytesseract.image_to_string(thresh).strip()
                label_plate_exit.config(text=f"Biển số: {detected_plate}")
                print(f"Biển số nhận diện: {detected_plate}")
                if detected_plate:
                    success, _ = process_exit_lane(detected_plate)
                    if success:
                        arduino.write(b'OPEN_EXIT\n')
    root.after(10, update_exit_lane)
update_entry_lane()
update_exit_lane()
root.mainloop()
cap.release()
cap_exit.release()
cv2.destroyAllWindows()