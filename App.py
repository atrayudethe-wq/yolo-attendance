import argparse
import csv
from datetime import datetime

# ================================================================
# EMAIL MODULES COMMENTED OUT FOR TESTING
# Un-comment the block below when ready to send live emails
# ================================================================
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
"""

import time
import cv2
from ultralytics import YOLO

# ================================
# CONFIGURATION & STUDENT DIRECTORY
# ================================
# Set to True when you want to enable live email sending
SEND_EMAIL = False

# Sender Gmail Configuration (Un-comment and fill details when live)
"""
SENDER_EMAIL = "robosapiensai1@gmail.com"
SENDER_PASSWORD = "lxknevuplkzarrhh"  # 16-character Gmail App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
"""

# Map each class name/student name to their personal email address
# Make sure string keys match the YOLO model class names EXACTLY
STUDENT_EMAILS = {
    "Kalki Mehta": "kalki.mehta@aeaschoolvashi.edu.in",
    "Madhurima mukherjee": "madhurima.mukherjee@aeaschoolvashi.edu.in",
    "Arush Shetty": "arush.shetty@aeaschoolvashi.edu.in",
    "shreyas bhoite": "shreyas.bhoite@aeaschoolvashi.edu.in",
    "Siddh  Gala": "siddh.gala@aeaschoolvashi.edu.in",
    "Dhairya Shah": "shah.dhairya@aeaschoolvashi.edu.in",
    "Shreyansh Choudhary": "shreyansh.choudhary@aeaschoolvashi.edu.in",
    "Chris": "aryan.sareen@aeaschoolvashi.edu.in",
    "Mansi Sable": "manasi.sable@aeaschoolvashi.edu.in",
    "Viya Jain": "viya.jain@aeaschoolvashi.edu.in",
    "astha bhanushali": "astha.bhanushali@aeaschoolvashi.edu.in",
    "Aarika Saini": "aarika.saini@aeaschoolvashi.edu.in",
    "Jinesh dagaliya": "jinesh.dagaliya@aeaschoolvashi.edu.in",
    "Yadnesh Jadhav": "yadnesh.jadhav@aeaschoolvashi.edu.in",
    "Veehan Gala": "veehan.gala@aeaschoolvashi.edu.in",
    # Add all your trained class names and their respective emails here
}

# ================================
# CLI ARGUMENTS
# ================================
parser = argparse.ArgumentParser(
    description="YOLO Attendance System - Direct Absentee Email Alerts"
)
parser.add_argument(
    "--weights",
    type=str,
    default="best.pt",
    help="Path to YOLO weights file",
)
parser.add_argument(
    "--cam", type=int, default=0, help="Camera index (default: 0)"
)
parser.add_argument(
    "--conf",
    type=float,
    default=0.5,
    help="Confidence threshold (default: 0.5)",
)
parser.add_argument(
    "--cutoff",
    type=str,
    default="09:15",
    help="Late cutoff time in HH:MM (24-hour format, default: 09:15)",
)
args = parser.parse_args()

# ================================
# MODEL & FILE SETUP
# ================================
print(f"[INFO] Loading model weights from: {args.weights}")
model = YOLO(args.weights)

# Derive master list from trained model classes + STUDENT_EMAILS dictionary
# Using set union ensures no students (like Veehan Gala) are omitted from roster tracking
MODEL_CLASSES = set(model.names.values())
CONFIGURED_STUDENTS = set(STUDENT_EMAILS.keys())
MASTER_LIST = list(MODEL_CLASSES.union(CONFIGURED_STUDENTS))

CSV_FILE = "attendance.csv"


"""
def send_direct_absent_email(student_name, student_email, date_str):
    Sends a personalized email notification directly to an absent student.
    if not SEND_EMAIL or not student_email:
        print(
            f"[TEST MODE] Email suppressed for {student_name} ({student_email})"
        )
        return

    # ================================================================
    # LIVE EMAIL DISPATCH LOGIC
    # Un-comment the multi-line block below when ready to send live emails
    # ================================================================
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = student_email
        msg["Subject"] = f"Absence Notification - {date_str}"

        body = (
            f"Hello {student_name},\n\n"
            f"This is an automated notification to inform you that you were marked ABSENT "
            f"for today's session ({date_str}).\n\n"
            f"If you believe this is an error, please contact your instructor.\n\n"
            f"Best regards,\nAttendance Management System"
        )

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(
            f"[EMAIL SENT 📧] Notification sent directly to {student_name} ({student_email})"
        )
    except Exception as e:
        print(f"[EMAIL ERROR ❌] Failed to send email to {student_name}: {e}")
"""


def log_attendance(name, cutoff_time_str):
    """Logs person's entry into CSV as 'Present' or 'Late'."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

    try:
        cutoff_time = datetime.strptime(
            f"{date_str} {cutoff_time_str}", "%Y-%m-%d %H:%M"
        )
    except ValueError:
        cutoff_time = datetime.strptime(f"{date_str} 09:15", "%Y-%m-%d %H:%M")

    status = "Present" if now <= cutoff_time else "Late"

    try:
        with open(CSV_FILE, "r") as f:
            content = f.read()
            if f"{name},{date_str}" in content:
                return
    except FileNotFoundError:
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Date", "Timestamp", "Status"])

    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, date_str, timestamp_str, status])

    color_flag = "🟩" if status == "Present" else "🟨"
    print(f"[LOGGED {color_flag}] {name} marked {status} at {timestamp_str}")


def finalize_absentees():
    """Logs missing students as Absent and triggers email notification handler."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

    logged_names = set()

    try:
        with open(CSV_FILE, "r") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2 and row[1] == date_str:
                    logged_names.add(row[0].strip())
    except FileNotFoundError:
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Date", "Timestamp", "Status"])

    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        for name in MASTER_LIST:
            if name not in logged_names:
                # 1. Log as Absent in CSV
                writer.writerow([name, date_str, timestamp_str, "Absent"])
                print(f"[LOGGED 🟥] {name} marked ABSENT")

                # 2. Trigger email processing
                """
                recipient_email = STUDENT_EMAILS.get(name)
                if recipient_email:
                    send_direct_absent_email(name, recipient_email, date_str)
                else:
                    print(
                        f"[WARNING ⚠️] No email address configured for {name} in STUDENT_EMAILS."
                    )
                """


# ================================
# CAMERA LOOP
# ================================
cap = cv2.VideoCapture(args.cam)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

prev_frame_time = 0
print(f"[INFO] Cutoff set to: {args.cutoff}")
print(f"[INFO] Master Roster Loaded ({len(MASTER_LIST)} students): {', '.join(sorted(MASTER_LIST))}")
print("[INFO] Press 'q' on preview window to stop feed & process absentees.")

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        new_frame_time = time.time()
        fps = (
            1 / (new_frame_time - prev_frame_time)
            if prev_frame_time != 0
            else 0
        )
        prev_frame_time = new_frame_time

        results = model(frame, conf=args.conf, verbose=False)[0]

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            name = (
                list(model.names.values())[cls_id]
                if cls_id < len(model.names)
                else f"ID_{cls_id}"
            )

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 128), 2)
            label = f"{name} ({conf * 100:.1f}%)"
            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 128),
                2,
            )

            log_attendance(name, args.cutoff)

        cv2.putText(
            frame,
            f"FPS: {int(fps)}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )
        cv2.imshow("Attendance Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    print(
        "\n[INFO] Session ended. Processing absentees..."
    )
    finalize_absentees()