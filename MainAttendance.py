import cv2
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog
import os
import time
import threading
import pyttsx3

# Function to play sound in a separate thread
def play_sound(name):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(f"Thank you {name}, your attendance is recorded")
    engine.runAndWait()

# Create folder for face images
if not os.path.exists("CapturedFaces"):
    os.makedirs("CapturedFaces")

# Tkinter root
root = tk.Tk()
root.withdraw()

# Load or create CSV safely
attendance_file = "Attendance.csv"
try:
    attendance_df = pd.read_csv(attendance_file)
    # If file exists but empty, create new DataFrame
    if attendance_df.empty:
        attendance_df = pd.DataFrame(columns=["Name", "Date", "Time", "Photo"])
except (FileNotFoundError, pd.errors.EmptyDataError):
    attendance_df = pd.DataFrame(columns=["Name", "Date", "Time", "Photo"])

# Webcam and face detector
cap = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Track faces in session to avoid duplicates
session_faces = {}

def countdown(frame, x, y, w, h, seconds=5):
    """Display live countdown on camera while keeping feed smooth"""
    start_time = time.time()
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        elapsed = int(time.time() - start_time)
        remaining = seconds - elapsed
        if remaining <= 0:
            break
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
        cv2.putText(frame, f"Capturing in {remaining}", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 3)
        cv2.imshow("Attendance System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            exit()

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        # Temporary ID for this face
        face_id = f"{x}_{y}_{w}_{h}"

        # Only take attendance if this face not recorded in session
        if face_id not in session_faces:
            # Countdown overlay
            countdown(frame, x, y, w, h, seconds=5)

            # Capture face image
            face_img = frame[y:y+h, x:x+w]

            # Popup to enter name
            name = simpledialog.askstring("Input", "Enter your name:", parent=root)
            if not name:
                name = "Unknown"
            name = name.strip().title()

            # Save the image with the name in filename
            photo_filename = f"CapturedFaces/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(photo_filename, face_img)

            # Record attendance in CSV
            now = datetime.now()
            date_string = now.strftime("%Y-%m-%d")
            time_string = now.strftime("%H:%M:%S")
            new_row = pd.DataFrame({"Name": [name], "Date": [date_string],
                                    "Time": [time_string], "Photo": [photo_filename]})
            attendance_df = pd.concat([attendance_df, new_row], ignore_index=True)
            attendance_df.to_csv(attendance_file, index=False)

            # Play thank you sound immediately in a separate thread
            threading.Thread(target=play_sound, args=(name,), daemon=True).start()

            # Mark face as recorded
            session_faces[face_id] = name

        # Draw rectangle and name
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
        cv2.putText(frame, session_faces.get(face_id, ""), (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.imshow("Attendance System", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
