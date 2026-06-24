import cv2
import numpy as np
import pickle
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from database import initialize_database
from utils.db_utils import get_student_data, insert_student_data

class StudentRegistration:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Registration")
        self.root.geometry("1000x700")
        
        self.face_samples = []
        self.profile_photo = None
        self.capturing = False

        initialize_database()
        self.setup_gui()

        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.update_video()

    def setup_gui(self):
        left = ttk.Frame(self.root)
        left.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        right = ttk.Frame(self.root)
        right.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.video_label = ttk.Label(left)
        self.video_label.pack()

        control_frame = ttk.Frame(left)
        control_frame.pack(pady=10)
        self.capture_btn = ttk.Button(control_frame, text="Start Face Capture", command=self.toggle_capture)
        self.capture_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Upload Profile Photo", command=self.upload_photo).pack(side=tk.LEFT, padx=5)

        form_frame = ttk.Frame(right)
        form_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Student Registration", font=('Helvetica', 16)).grid(row=0, column=0, columnspan=2, pady=10)

        self.entries = {}
        fields = [
            ("College ID", "college_id"),
            ("Full Name", "full_name"),
            ("Course", "course"),
            ("Year", "year"),
            ("Phone Number", "phone_number"),
            ("Email", "email"),
            ("Parents' Name", "parents_name"),
            ("Address", "address")
        ]

        for i, (label, key) in enumerate(fields):
            ttk.Label(form_frame, text=label + ":").grid(row=i+1, column=0, sticky=tk.W, padx=5, pady=5)
            entry = ttk.Entry(form_frame)
            entry.grid(row=i+1, column=1, sticky=tk.EW, padx=5, pady=5)
            self.entries[key] = entry

        ttk.Button(form_frame, text="Register Student", command=self.register_student).grid(row=len(fields)+2, column=0, columnspan=2, pady=20)
        self.status_var = tk.StringVar()
        ttk.Label(form_frame, textvariable=self.status_var).grid(row=len(fields)+3, column=0, columnspan=2)

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if self.capturing:
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    face = gray[y:y+h, x:x+w]
                    face = cv2.resize(face, (100, 100))
                    self.face_samples.append(face)
                    self.status_var.set(f"Captured {len(self.face_samples)} face samples")

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imgtk = ImageTk.PhotoImage(Image.fromarray(rgb))
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.root.after(10, self.update_video)

    def toggle_capture(self):
        self.capturing = not self.capturing
        if self.capturing:
            self.capture_btn.config(text="Stop Face Capture")
            self.face_samples = []
            self.status_var.set("Capturing face samples...")
        else:
            self.capture_btn.config(text="Start Face Capture")
            self.status_var.set(f"Captured {len(self.face_samples)} samples" if self.face_samples else "No face samples captured")

    def upload_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if path:
            with open(path, "rb") as f:
                self.profile_photo = f.read()
            self.status_var.set("Profile photo uploaded")

    def register_student(self):
        college_id = self.entries['college_id'].get().strip()
        full_name = self.entries['full_name'].get().strip()
        course = self.entries['course'].get().strip()

        if not college_id or not full_name or not course:
            messagebox.showerror("Error", "College ID, Full Name, and Course are required.")
            return

        if get_student_data(college_id):
            messagebox.showerror("Error", "Student already registered.")
            return

        if len(self.face_samples) < 5:
            messagebox.showerror("Error", "Capture at least 5 face samples.")
            return

        try:
            face_data = pickle.dumps([f.flatten() for f in self.face_samples])
            student_data = (
                college_id,
                full_name,
                course,
                self.entries['year'].get().strip(),
                self.entries['phone_number'].get().strip(),
                self.entries['email'].get().strip(),
                self.entries['parents_name'].get().strip(),
                self.entries['address'].get().strip(),
                self.profile_photo,
                face_data
            )

            insert_student_data(student_data)
            messagebox.showinfo("Success", "Student registered successfully.")
            self.reset_form()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to register student: {e}")

    def reset_form(self):
        for e in self.entries.values():
            e.delete(0, tk.END)
        self.face_samples = []
        self.profile_photo = None
        self.capturing = False
        self.capture_btn.config(text="Start Face Capture")
        self.status_var.set("Ready for next student")

    def __del__(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    root = tk.Tk()
    app = StudentRegistration(root)
    root.mainloop()
