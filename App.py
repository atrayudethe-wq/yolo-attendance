import csv
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
import cv2
import numpy as np
import streamlit as st

# ================================
# STREAMLIT PAGE CONFIGURATION
# ================================
st.set_page_config(
    page_title="AI Attendance Management System",
    page_icon="🎓",
    layout="wide",
)

# Custom Dark UI Styling
st.markdown(
    """
    <style>
        .main-header {
            background: linear-gradient(135deg, #1E1E2F 0%, #0F0F17 100%);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #2E2E48;
            text-align: center;
            margin-bottom: 20px;
        }
        .main-header h1 {
            color: #00E676;
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .main-header p {
            color: #B0BEC5;
            font-size: 1rem;
            margin: 0;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: bold;
            color: #
