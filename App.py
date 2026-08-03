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
# STREAMLIT PAGE CONFIGURATION
# ================================
st.set_page_config(
    page_title="AI Attendance Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Modern Dark UI Styling
st.markdown(
    """
    <style>
        /* Main Header Banner */
        .main-header {
            background: linear-gradient(135deg, #1E1E2F 0%, #0F0F17 100%);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #2E2E48;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.3);
        }
        .main-header h1 {
            color: #00E676;
            font-size: 2.3rem;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .main-header p {
            color: #B0BEC5;
            font-size: 1.05rem;
            margin: 0;
        }

        /* Metric Cards Styling */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: bold;
            color: #00E676;
        }

        /* Primary Button Styling */
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# ================================
# CONFIGURATION & STUDENT DIRECTORY
# ================================
SEND_EMAIL = True

# Sender Gmail Configuration
SENDER_EMAIL = "robosapiensai1@gmail.com"
SENDER_PASSWORD = "lxknevuplkzarrhh"  # 16-character Gmail App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Map each class name/student name to their personal email address
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


# ================================
# MODEL & SESSION INITIALIZATION
# ================================
@st.cache_resource
def load_yolo_model():
    return YOLO("best.pt")


model = load_yolo_model()
MASTER_LIST = list(model.names.values())

# Initialize session state for tracking attendance in memory
if "session_attendance" not in st.session_state:
    st.session_state.session_attendance = {}


# ================================
# BACKEND FUNCTIONS
# ================================
def send_direct_absent_email(student_name, student_email, date_str):
    """Sends a personalized email notification directly to an absent student."""
    if not SEND_EMAIL or not student_email:
        return False, "Disabled or missing email address."

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
        return True, "Email delivered"
    except Exception as e:
        return False, str(e)


def log_attendance(name, cutoff_time_str):
    """Logs person's entry into CSV as 'Present' or 'Late'."""
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

    # Avoid duplicate entry for the same day in CSV
    try:
        with open(CSV_FILE, "r") as f:
            content = f.read()
            if f"{name},{date_str}" in content:
                return status, timestamp_str
    except FileNotFoundError:
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Date", "Timestamp", "Status"])

    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([name, date_str, timestamp_str, status])

    return status, timestamp_str


def finalize_absentees():
    """Logs missing students as Absent and sends direct individual emails."""
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
            writer = csv.writer(f)
            writer.writerow(["Name", "Date", "Timestamp", "Status"])

    dispatch_logs = []
    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        for name in MASTER_LIST:
            if name not in logged_names:
                # 1. Log as Absent in CSV
                writer.writerow([name, date_str, timestamp_str, "Absent"])

                # 2. Send email directly to this absent student
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
                    {"Student": name, "Status": "Absent", "Dispatch Note": status_text}
                )

    return dispatch_logs


# ================================
# UI HEADER & SIDEBAR
# ================================
st.markdown(
    """
    <div class="main-header">
        <h1>🎓 AI Face Recognition Attendance System</h1>
        <p>YOLO11 Automated Attendance Tracking & Instant Email Dispatcher</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("⚙️ Session Controls")
cutoff_input = st.sidebar.text_input(
    "Late Cutoff Time (HH:MM 24h)",
    value="09:15",
    help="Students scanning after this time will be marked as Late.",
)
conf_slider = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.1,
    max_value=1.0,
    value=0.5,
    step=0.05,
    help="Minimum detection probability required for recognition.",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Enrolled Roster")
for student in MASTER_LIST:
    st.sidebar.markdown(f"- **{student}**")

# ================================
# DASHBOARD TABS
# ================================
tab1, tab2 = st.tabs(["📷 Live Camera Feed", "📊 Attendance Summary & Alerts"])

with tab1:
    col_cam, col_res = st.columns([1, 1])

    with col_cam:
        st.subheader("📸 Camera Capture")
        picture = st.camera_input("Position face in camera view and capture frame")

    with col_res:
        st.subheader("🎯 Real-Time Detections")
        if picture:
            bytes_data = picture.getvalue()
            cv_img = cv2.imdecode(
                np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR
            )

            results = model(cv_img, conf=conf_slider, verbose=False)[0]

            detected_in_frame = False
            for box in results.boxes:
                detected_in_frame = True
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                name = (
                    MASTER_LIST[cls_id]
                    if cls_id < len(MASTER_LIST)
                    else f"ID_{cls_id}"
                )
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Log entry to CSV and memory
                status, timestamp_str = log_attendance(name, cutoff_input)
                st.session_state.session_attendance[name] = {
                    "Date & Time": timestamp_str,
                    "Status": status,
                }

                # Bounding Box Colors: Green for Present, Orange for Late
                box_color = (0, 255, 128) if status == "Present" else (0, 165, 255)
                cv2.rectangle(cv_img, (x1, y1), (x2, y2), box_color, 2)
                label = f"{name} ({conf * 100:.1f}%) [{status}]"
                cv2.putText(
                    cv_img,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    box_color,
                    2,
                )

            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            st.image(rgb_img, use_container_width=True)

            if not detected_in_frame:
                st.warning("No recognized student faces detected in frame.")
        else:
            st.info("Awaiting camera frame capture...")

with tab2:
    st.subheader("📈 Real-Time Class Analytics")

    # Metrics Overview
    total_enrolled = len(MASTER_LIST)
    total_logged = len(st.session_state.session_attendance)
    present_count = sum(
        1
        for v in st.session_state.session_attendance.values()
        if v["Status"] == "Present"
    )
    late_count = sum(
        1
        for v in st.session_state.session_attendance.values()
        if v["Status"] == "Late"
    )
    absent_count = total_enrolled - total_logged

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Enrolled", total_enrolled)
    m2.metric("Present 🟩", present_count)
    m3.metric("Late 🟨", late_count)
    m4.metric("Absent (Pending) 🟥", absent_count)

    st.markdown("---")
    st.subheader("📋 Logged Records")

    if st.session_state.session_attendance:
        table_data = [
            {"Name": k, "Date & Time": v["Date & Time"], "Status": v["Status"]}
            for k, v in st.session_state.session_attendance.items()
        ]
        st.dataframe(table_data, use_container_width=True)
    else:
        st.info("No students scanned during this active session yet.")

    st.markdown("---")
    st.subheader("🚨 Finalize Session & Notify Absentees")
    st.markdown(
        "Clicking the button below will lock today's session, mark remaining missing students as **Absent**, and send automated email alerts directly to their email addresses."
    )

    if st.button("🚨 Finalize Session & Send Emails", type="primary"):
        with st.spinner("Processing absentees and sending emails..."):
            logs = finalize_absentees()

        if logs:
            st.warning("Session Finalized. The following students were marked ABSENT:")
            st.table(logs)
        else:
            st.success("🎉 All enrolled students were present! No absentee emails needed.")