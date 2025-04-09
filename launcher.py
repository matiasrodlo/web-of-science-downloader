import streamlit
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import math 
import time
import os
import sys
import subprocess

def start_streamlit_app():
    # Get the path to the directory where this script resides
    executable_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    # Specify the path to the main Streamlit app script (app.py)
    streamlit_app_script = os.path.join(executable_dir, "app.py")
    # Run the Streamlit app
    subprocess.run(["streamlit", "run", streamlit_app_script], check=True)

if __name__ == "__main__":
    start_streamlit_app()