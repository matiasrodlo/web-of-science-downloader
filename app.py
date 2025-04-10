import streamlit as st
import os
import sys
import random
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import math
import time

# ---------- PAGE CONFIGURATION
st.set_page_config(
    page_title='Web of Science Downloader',
    layout='wide'
)

st.markdown(
    """
    <style>            
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .footer {
        position: fixed;
        display: block;
        width: 100%;
        bottom: 0;
        color: rgba(49, 51, 63, 0.4);
    }
    a:link , a:visited{
        color: rgba(49, 51, 63, 0.4);
        background-color: transparent;
        text-decoration: underline;
    }
    </style>
    <div class="footer">
        <p>
            Developed by 
            <a href="https://github.com/albert-pang" target="_blank">
            Albert (GITM) and Tomy Tjandra (CS) - NTUST
            </a>
        </p>
    </div>
    """, unsafe_allow_html=True
)

# --- File Naming Helper Functions ---
def sanitize_query(query):
    query_clean = query.strip().lower().replace(" ", "_")
    query_clean = re.sub(r'[^a-z0-9_]', '', query_clean)
    return query_clean

def generate_filename(query, start_record, end_record, prefix="WOS"):
    query_clean = sanitize_query(query)
    filename = f"{prefix}_{query_clean}_{start_record}-{end_record}.bib"
    return filename

DEFAULT_DOWNLOAD_NAME = "WOS_Output.bib"
DOWNLOAD_DELAY_MIN = 5
DOWNLOAD_DELAY_MAX = 15

# --- New download folder path (for renamed files) ---
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def random_delay():
    delay = random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX)
    st.info(f"Waiting for {delay:.1f} seconds to emulate human behavior...")
    time.sleep(delay)

def find_recent_bib_file(directory, time_limit=300):
    """
    Look for any file with .bib extension in the given directory 
    that was modified within the last `time_limit` seconds.
    """
    try:
        bib_files = [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.lower().endswith('.bib')
        ]
    except Exception as e:
        st.info(f"Error listing directory {directory}: {e}")
        return None

    if not bib_files:
        return None
    current_time = time.time()
    # Return files modified in the last time_limit seconds
    recent_files = [f for f in bib_files if (current_time - os.path.getmtime(f)) < time_limit]
    if recent_files:
        recent_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        return recent_files[0]
    return None

def get_download_path():
    """
    Check both the custom OUTPUT_DIR and the default system Downloads folder
    for either a file named DEFAULT_DOWNLOAD_NAME or any recent .bib file.
    """
    # First check the expected file in OUTPUT_DIR
    custom_path = os.path.join(OUTPUT_DIR, DEFAULT_DOWNLOAD_NAME)
    if os.path.exists(custom_path):
        st.info("Found file in custom downloads folder by expected name.")
        return custom_path

    # Then check the system's default Downloads folder
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    default_path = os.path.join(downloads_dir, DEFAULT_DOWNLOAD_NAME)
    if os.path.exists(default_path):
        st.info("Found file in system default Downloads folder by expected name.")
        return default_path

    # If not found by expected name, search for any recent .bib file
    st.info("Expected file not found; searching for any .bib file...")
    recent_custom = find_recent_bib_file(OUTPUT_DIR)
    if recent_custom:
        st.info(f"Found .bib file in custom folder: {recent_custom}")
        return recent_custom

    recent_default = find_recent_bib_file(downloads_dir)
    if recent_default:
        st.info(f"Found .bib file in default Downloads folder: {recent_default}")
        return recent_default

    st.info("No .bib file found in either location yet.")
    # Return the custom expected path as a fallback.
    return custom_path

def wait_for_download(timeout=60, poll_frequency=1):
    """
    Polls until a .bib file is found in either expected location.
    Returns the file path if found, or None if timeout reached.
    """
    start_time = time.time()
    file_path = None
    while time.time() - start_time < timeout:
        file_path = get_download_path()
        if file_path and os.path.exists(file_path):
            return file_path
        time.sleep(poll_frequency)
    return None

def create_driver():
    options = Options()
    # When attaching to an existing Chrome session using debugger_address,
    # do not add custom download preferences.
    options.debugger_address = "127.0.0.1:9222"
    try:
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver
    except Exception as e:
        st.error(f"Could not connect to existing Chrome session: {e}")
        return None

def main():
    st.title("WOS Downloader App")
    url = st.text_input("Enter URL")
    search_query = st.text_input("Enter search query (for filename)", value="")
    if search_query:
        st.session_state.search_query = search_query

    if st.button("Attach to existing Chrome session") and url:
        if "driver" not in st.session_state:
            driver = create_driver()
            if driver is None:
                return
            st.session_state.driver = driver
            driver.get(url)
            st.info("Chrome session attached. Please log in manually. Then click 'Continue after logging in'.")
        else:
            st.info("Driver already attached.")

    if "driver" in st.session_state and st.button("Continue after logging in"):
        driver = st.session_state.driver
        time.sleep(5)
        if is_university_front_page(driver):
            download_data_university(driver)
        elif is_other_network_front_page(driver):
            download_data_other_network(driver)
        else:
            st.error("Front page not recognized.")
        driver.quit()
        del st.session_state.driver

def is_university_front_page(driver):
    try:
        return bool(driver.find_elements(By.ID, "onetrust-close-btn-container") or driver.find_elements(By.TAG_NAME, "app-export-menu"))
    except Exception:
        return False

def is_other_network_front_page(driver):
    try:
        driver.find_element(By.ID, "mat-input-0")
        driver.find_element(By.ID, "mat-input-1")
        driver.find_element(By.ID, "signIn-btn")
        return True
    except Exception:
        return False

def save_downloaded_file(from_rec, to_rec):
    downloaded_file = wait_for_download(timeout=60)
    if downloaded_file:
        if "search_query" in st.session_state and st.session_state.search_query.strip() != "":
            new_filename = generate_filename(st.session_state.search_query, from_rec, to_rec)
        else:
            new_filename = generate_filename("default", from_rec, to_rec)
        destination = os.path.join(OUTPUT_DIR, new_filename)
        try:
            os.rename(downloaded_file, destination)
            st.success(f"File moved to: {destination}")
        except Exception as e:
            st.error(f"Error renaming file: {e}")
    else:
        st.warning("Downloaded file not found after waiting.")

def download_data_university(driver):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "onetrust-close-btn-container"))).click()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Close this tour']"))).click()
    except TimeoutException:
        pass

    n_result_text = driver.find_element(By.CLASS_NAME, "brand-blue").text
    n_result = int(n_result_text.replace(",", ""))
    n_iter = math.ceil(n_result / 500)
    progress_bar = st.progress(0)

    for iter in range(n_iter):
        progress_bar.progress((iter + 1) / n_iter, text=f"Downloading file {iter + 1} of {n_iter}")
        time.sleep(1)
        try:
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.TAG_NAME, "app-export-menu"))).click()
            random_delay()
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#mat-menu-panel-13 > div > div > div:nth-child(7)"))
            ).click()
            random_delay()
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[for='radio3-input']"))
            ).click()
            random_delay()
            from_rec, to_rec = 500 * iter + 1, 500 * (iter + 1)
            input_elements = driver.find_elements(By.CLASS_NAME, "mat-input-element")
            if len(input_elements) >= 2:
                input_elements[0].clear()
                input_elements[0].send_keys(from_rec)
                input_elements[1].clear()
                input_elements[1].send_keys(to_rec)
            else:
                st.error("Record range inputs not found.")
                continue
            random_delay()
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CLASS_NAME, "dropdown"))).click()
            random_delay()
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[title='Full Record and Cited References']"))
            ).click()
            random_delay()
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#exportButton"))
            ).click()
            WebDriverWait(driver, 60).until_not(EC.visibility_of_element_located((By.CLASS_NAME, "window")))
            st.success(f"SUCCESS: Downloaded records {from_rec} to {to_rec}")
            save_downloaded_file(from_rec, to_rec)
            random_delay()
        except TimeoutException:
            st.error("Timeout during one of the export steps.")
            continue

def download_data_other_network(driver):
    try:
        WebDriverWait(driver, 300).until(EC.invisibility_of_element((By.ID, "signIn-btn")))
        time.sleep(10)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "onetrust-close-btn-container"))).click()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Close this tour']"))
        ).click()
    except TimeoutException:
        pass

    n_result_text = driver.find_element(By.CLASS_NAME, "brand-blue").text
    n_result = int(n_result_text.replace(",", ""))
    n_iter = math.ceil(n_result / 500)
    progress_bar = st.progress(0)

    for iter in range(n_iter):
        progress_bar.progress((iter + 1) / n_iter, text=f"Downloading file {iter + 1} of {n_iter}")
        time.sleep(1)
        try:
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.TAG_NAME, "app-export-menu"))).click()
            random_delay()
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#mat-menu-panel-13 > div > div > div:nth-child(7)"))
            ).click()
            random_delay()
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[for='radio3-input']"))
            ).click()
            random_delay()
            from_rec, to_rec = 500 * iter + 1, 500 * (iter + 1)
            input_elements = driver.find_elements(By.CLASS_NAME, "mat-input-element")
            if len(input_elements) >= 2:
                input_elements[0].clear()
                input_elements[0].send_keys(from_rec)
                input_elements[1].clear()
                input_elements[1].send_keys(to_rec)
            else:
                st.error("Record range inputs not found.")
                continue
            random_delay()
            WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CLASS_NAME, "dropdown"))).click()
            random_delay()
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[title='Full Record and Cited References']"))
            ).click()
            random_delay()
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#exportButton"))
            ).click()
            WebDriverWait(driver, 60).until_not(EC.visibility_of_element_located((By.CLASS_NAME, "window")))
            st.success(f"SUCCESS: Downloaded records {from_rec} to {to_rec}")
            save_downloaded_file(from_rec, to_rec)
            random_delay()
        except TimeoutException:
            st.error("Timeout during one of the export steps.")
            continue

if __name__ == "__main__":
    main()
