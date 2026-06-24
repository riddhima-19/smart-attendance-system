import cv2
import pickle
import numpy as np
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from datetime import datetime
from io import BytesIO
from utils.db_utils import get_student_data
from database import initialize_database

def mark_attendance(college_id, name, course):
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect('college.db')
    c = conn.cursor()
    c.execute("SELECT * FROM attendance WHERE college_id = ? AND date = ?", (college_id, today))
    if not c.fetchone():
        c.execute("INSERT INTO attendance (college_id, name, course, date, time) VALUES (?, ?, ?, ?, ?)",
                  (college_id, name, course, today, now))
        conn.commit()
    conn.close()

def get_attendance_records(college_id):
    conn = sqlite3.connect('college.db')
    c = conn.cursor()
    c.execute("SELECT date, time FROM attendance WHERE college_id = ? ORDER BY date DESC", (college_id,))
    records = c.fetchall()
    conn.close()
    return records

def calculate_attendance_percentage(college_id):
    conn = sqlite3.connect('college.db')
    c = conn.cursor()
    c.execute("SELECT MIN(date), MAX(date) FROM attendance")
    min_date, max_date = c.fetchone()
    c.execute("SELECT COUNT(*) FROM attendance WHERE college_id=?", (college_id,))
    present_days = c.fetchone()[0]
    conn.close()
    if min_date and max_date:
        total_days = (datetime.strptime(max_date, "%Y-%m-%d") - datetime.strptime(min_date, "%Y-%m-%d")).days + 1
        return (present_days / total_days) * 100 if total_days > 0 else 0
    return 0

class StudentDashboard:
    def __init__(self, root, college_id):
        self.root = root
        self.root.title("Student Dashboard")
        self.root.geometry("500x400")

        self.student_data = get_student_data(college_id)
        self.attendance_records = get_attendance_records(college_id)
        self.attendance_percentage = calculate_attendance_percentage(college_id)

        self.setup_gui()

    def setup_gui(self):
        info_frame = ttk.LabelFrame(self.root, text="Student Info")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        labels = [
            ("College ID", self.student_data[0]),
            ("Full Name", self.student_data[1]),
            ("Course", self.student_data[2]),
            ("Year", self.student_data[3]),
            ("Phone", self.student_data[4]),
            ("Email", self.student_data[5]),
            ("Parent's Name", self.student_data[6]),
            ("Address", self.student_data[7]),
            ("Attendance %", f"{self.attendance_percentage:.2f}%"),
        ]

        for label, value in labels:
            row = ttk.Frame(info_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{label}:", width=15).pack(side=tk.LEFT)
            ttk.Label(row, text=value).pack(side=tk.LEFT)

        records_frame = ttk.LabelFrame(self.root, text="Recent Attendance")
        records_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for date, time in self.attendance_records[:5]:  # show top 5
            ttk.Label(records_frame, text=f"{date} - {time}").pack(anchor=tk.W)

class AttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance System")
        self.root.geometry("1000x600")
        
        self.load_face_data()
        self.setup_gui()
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.current_student = None
        self.recognized_ids_today = set()
        self.update_video_feed()

    def load_face_data(self):
        self.face_encodings = []
        self.face_labels = []

        conn = sqlite3.connect('college.db')
        cursor = conn.cursor()
        cursor.execute("SELECT college_id, face_data FROM student_info")
        records = cursor.fetchall()
        conn.close()

        for college_id, face_data in records:
            if face_data:
                faces = pickle.loads(face_data)
                for f in faces:
                    self.face_encodings.append(f)
                    self.face_labels.append(college_id)

        if self.face_encodings:
            from sklearn.neighbors import KNeighborsClassifier
            self.knn = KNeighborsClassifier(n_neighbors=3)
            self.knn.fit(self.face_encodings, self.face_labels)
        else:
            messagebox.showerror("Error", "No face data found in database!")
            self.root.destroy()

    def setup_gui(self):
        left_frame = ttk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        right_frame = ttk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

        self.video_label = ttk.Label(left_frame)
        self.video_label.pack()

        self.info_frame = ttk.LabelFrame(right_frame, text="Student Information")
        self.info_frame.pack(pady=10)

        self.photo_label = ttk.Label(self.info_frame)
        self.photo_label.pack(pady=5)

        self.info_labels = {}
        fields = ['College ID', 'Name', 'Course', 'Year', 'Status']
        for field in fields:
            label = ttk.Label(self.info_frame, text=f"{field}: -")
            label.pack(anchor=tk.W, padx=5, pady=2)
            self.info_labels[field.lower()] = label

        self.status_var = tk.StringVar()
        ttk.Label(right_frame, textvariable=self.status_var).pack(pady=10)

        ttk.Button(right_frame, text="Open Student Dashboard", command=self.open_dashboard).pack(pady=10)

    def update_video_feed(self):
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(10, self.update_video_feed)
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (100, 100)).flatten().reshape(1, -1)

            try:
                pred_id = self.knn.predict(face_img)[0]
                confidence = np.max(self.knn.predict_proba(face_img))

                if confidence > 0.7:
                    self.current_student = get_student_data(pred_id)
                    self.update_info()

                    today = datetime.now().strftime("%Y-%m-%d")
                    if pred_id not in self.recognized_ids_today:
                        mark_attendance(pred_id, self.current_student[1], self.current_student[2])
                        self.recognized_ids_today.add(pred_id)
                        self.status_var.set(f"✅ Attendance marked for {self.current_student[1]}")

                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                    cv2.putText(frame, pred_id, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 2)
                    cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
            except:
                pass

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)

        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

        self.root.after(10, self.update_video_feed)

    def update_info(self):
        if self.current_student:
            cid, name, course, year = self.current_student[0:4]
            self.info_labels['college id'].config(text=f"College ID: {cid}")
            self.info_labels['name'].config(text=f"Name: {name}")
            self.info_labels['course'].config(text=f"Course: {course}")
            self.info_labels['year'].config(text=f"Year: {year}")
            self.info_labels['status'].config(text="Status: Present")

            # Load and display profile image if available
            if self.current_student[8]:
                try:
                    img_data = self.current_student[8]
                    image = Image.open(BytesIO(img_data)).resize((120, 120))
                    photo = ImageTk.PhotoImage(image)
                    self.photo_label.configure(image=photo)
                    self.photo_label.image = photo
                except:
                    self.photo_label.config(text="⚠️ Error loading image")
            else:
                self.photo_label.config(text="No Profile Photo")

    def open_dashboard(self):
        if self.current_student:
            StudentDashboard(tk.Toplevel(self.root), self.current_student[0])
        else:
            messagebox.showwarning("⚠️", "No student detected!")

    def __del__(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()

# Add your StudentDashboard class here or import it if separate

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceSystem(root)
    root.mainloop()

class StudentDashboard:
    def __init__(self, root, college_id):
        self.root = root
        self.root.title("Student Dashboard")
        self.root.geometry("500x400")

        from utils.db_utils import get_student_data, get_attendance_records, calculate_attendance_percentage
        self.student_data = get_student_data(college_id)
        self.attendance_records = get_attendance_records(college_id)
        self.attendance_percentage = calculate_attendance_percentage(college_id)

        self.setup_gui()

    def setup_gui(self):
        import tkinter as tk
        from tkinter import ttk

        info_frame = ttk.LabelFrame(self.root, text="Student Info")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        labels = [
            ("College ID", self.student_data[0]),
            ("Full Name", self.student_data[1]),
            ("Course", self.student_data[2]),
            ("Year", self.student_data[3]),
            ("Phone", self.student_data[4]),
            ("Email", self.student_data[5]),
            ("Parent's Name", self.student_data[6]),
            ("Address", self.student_data[7]),
            ("Attendance %", f"{self.attendance_percentage:.2f}%"),
        ]

        for label, value in labels:
            row = ttk.Frame(info_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{label}:", width=15).pack(side=tk.LEFT)
            ttk.Label(row, text=value).pack(side=tk.LEFT)

        records_frame = ttk.LabelFrame(self.root, text="Recent Attendance")
        records_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for date, time in self.attendance_records[:5]:  # show top 5
            ttk.Label(records_frame, text=f"{date} - {time}").pack(anchor=tk.W)

