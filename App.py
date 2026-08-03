import csv
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
import cv2
import numpy as np
import streamlit as st
from ultralytics import YOLO

# ================================
# STREAMLIT PAGE CONFIG
# ================================
st.set_page_config(
    page_title="AI Attendance System",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 AI Face Recognition Attendance System")


# ================================
# LOAD MODEL SAFELY
# ================================
@st.cache_resource(show_spinner="Loading AI Model...")
def load_yolo_model():
    from ultralytics import YOLO

    model_path = "best.pt"
    if not os.path.exists(model_path):
        st.error(
            f"❌ Model file '{model_path}' not found in GitHub repository!"
        )
        st.stop()
    return YOLO(model_path)


try:
    model = load_yolo_model()
    MASTER_LIST = list(model.names.values())
except Exception as e:
    st.error(f"Error loading model: {e}")
    st.stop()


# ================================
# CONFIGURATION
# ================================
SEND_EMAIL = True
SENDER_EMAIL = "robosapiensai1@gmail.com"
SENDER_PASSWORD = "lxknevuplkzarrhh"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

STUDENT_EMAILS = {
    "Kalki Mehta": "kalki.mehta@aeaschoolvashi.edu.in",
    "Madhurima Mukherjee": "madhurima.mukherjee@aeaschoolvashi.edu.in",
    "Arush Shetty": "arush.shetty@aeaschoolvashi.edu.in",
    "Shreyas Bhoite": "shreyas.bhoite@aeaschool.vashi.edu.in",
    "Siddh Gala": "siddh.gala@aeaschoolvashi.edu.in",
    "Dhairya Shah": "shah.dhairya@aeaschoolvashi.edu.in",
    "Shreyansh Choudhary": "shreyansh.choudhary@aeaschoolvashi.edu.in",
    "Aryan Sareen": "aryan.sareen@aeaschoolvashi.edu.in",
}

CSV_FILE = "attendance.csv"

if "session_attendance" not in st.session_state:
    st.session_state.session_attendance = {}


# ================================
# HELPER FUNCTIONS
# ================================
def send_direct_absent_email(student_name, student_email, date_str):
    if not SEND_EMAIL or not student_email:
        return False, "Disabled or missing email address."

    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = student_email
        msg["Subject"] = f"Absence Notification - {date_str}"

        body = f"Hello {student_name},\n\nYou were marked ABSENT for today's session ({date_str})."
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "Email delivered"
    except Exception as e:
        return False, str(e)


def log_attendance(name, cutoff_time_str):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

    try:
        cutoff_time = datetime.strptime(
            f"{date_str} {cutoff_time_str}", "%Y-%m-%d %H:%M"
        )
        status = "Present" if now <= cutoff_time else "Late"
    except ValueError:
        status = "Present"

    try:
        with open(CSV_FILE, "r") as f:
            if f"{name},{date_str}" in f.read():
                return status, timestamp_str
    except FileNotFoundError:
        with open(CSV_FILE, "w", newline="") as f:
            csv.writer(f).writerow(["Name", "Date", "Timestamp", "Status"])

    with open(CSV_FILE, mode="a", newline="") as f:
        csv.writer(f).writerow([name, date_str, timestamp_str, status])

    return status, timestamp_str


def finalize_absentees():
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
                    logged_names.add(row[0])
    except FileNotFoundError:
        with open(CSV_FILE, "w", newline="") as f:
            csv.writer(f).writerow(["Name", "Date", "Timestamp", "Status"])

    dispatch_logs = []
    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        for name in MASTER_LIST:
            if name not in logged_names:
                writer.writerow([name, date_str, timestamp_str, "Absent"])
                recipient_email = STUDENT_EMAILS.get(name)
                if recipient_email:
                    success, msg = send_direct_absent_email(
                        name, recipient_email, date_str
                    )
                    status_text = (
                        f"📧 Sent to {recipient_email}"
                        if success
                        else f"❌ Error: {msg}"
                    )
                else:
                    status_text = "⚠️ No email on file"

                dispatch_logs.append(
                    {
                        "Student": name,
                        "Status": "Absent",
                        "Dispatch Note": status_text,
                    }
                )

    return dispatch_logs


# ================================
# SIDEBAR
# ================================
st.sidebar.header("⚙️ Settings")
cutoff_input = st.sidebar.text_input("Late Cutoff Time (HH:MM 24h)", value="09:15")
conf_slider = st.sidebar.slider("Confidence Threshold", 0.1, 1.0, 0.25, 0.05)

st.sidebar.markdown("### 📋 Enrolled Roster")
for student in MASTER_LIST:
    st.sidebar.markdown(f"- {student}")


# ================================
# TABS
# ================================
tab1, tab2 = st.tabs(["📷 Camera Detector", "📊 Summary & Alerts"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Camera Input")
        picture = st.camera_input("Take photo for attendance")

    with col2:
        st.subheader("Detection Result")
        if picture:
            bytes_data = picture.getvalue()
            cv_img = cv2.imdecode(
                np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR
            )

            results = model(cv_img, conf=conf_slider, verbose=False)[0]

            detected = False
            for box in results.boxes:
                detected = True
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                name = (
                    MASTER_LIST[cls_id]
                    if cls_id < len(MASTER_LIST)
                    else f"ID_{cls_id}"
                )
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                status, timestamp_str = log_attendance(name, cutoff_input)
                st.session_state.session_attendance[name] = {
                    "Date & Time": timestamp_str,
                    "Status": status,
                }

                box_color = (
                    (0, 255, 128) if status == "Present" else (0, 165, 255)
                )
                cv2.rectangle(cv_img, (x1, y1), (x2, y2), box_color, 3)
                cv2.putText(
                    cv_img,
                    f"{name} ({conf * 100:.0f}%)",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    box_color,
                    2,
                )

            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            st.image(rgb_img, use_container_width=True)

            if detected:
                st.success("✅ Student recognized and logged!")
            else:
                st.warning(
                    "⚠️ No face detected. Try adjusting lighting or threshold."
                )
        else:
            st.info("Take a photo using the camera on the left.")

with tab2:
    st.subheader("Attendance Records")
    if st.session_state.session_attendance:
        st.dataframe(
            [
                {"Name": k, **v}
                for k, v in st.session_state.session_attendance.items()
            ],
            use_container_width=True,
        )
    else:
        st.info("No records logged yet.")

    st.markdown("---")
    if st.button("🚨 Finalize Session & Send Emails", type="primary"):
        with st.spinner("Processing..."):
            logs = finalize_absentees()
        if logs:
            st.table(logs)
        else:
            st.success("All students were present!")
