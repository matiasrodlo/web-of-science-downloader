import streamlit as st
import os
import sys
import random
import re
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

# Define variable delays to emulate human behavior
DOWNLOAD_DELAY_MIN = 5   # minimum delay in seconds
DOWNLOAD_DELAY_MAX = 15  # maximum delay in seconds

def random_delay():
    delay = random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX)
    st.info(f"Waiting for {delay:.1f} seconds to emulate human behavior...")
    time.sleep(delay)

# --- File renaming helper functions ---
def sanitize_query(query):
    """Sanitize the search query to create a filename-friendly string."""
    query_clean = query.strip().lower().replace(" ", "_")
    query_clean = re.sub(r'[^a-z0-9_]', '', query_clean)
    return query_clean

def generate_filename(query, start_record, end_record, prefix="WOS"):
    query_clean = sanitize_query(query)
    filename = f"{prefix}_{query_clean}_{start_record}-{end_record}.bib"
    return filename

# Default downloaded file name (adjust if needed based on your Chrome settings)
DEFAULT_DOWNLOAD_NAME = "WOS_Output.bib"

def create_driver():
    options = Options()
    current_directory = os.path.dirname(os.path.abspath(__file__))
    if sys.platform.startswith("linux"):
        chrome_path = "/usr/bin/google-chrome"  # or "/usr/bin/chromium-browser"
        chromedriver_path = "/usr/local/bin/chromedriver"  # Adjust if different
    elif sys.platform.startswith("win"):
        chrome_path = os.path.join(current_directory, r"Chrome/Application/chrome.exe")
        chromedriver_path = os.path.join(current_directory, r"Chromedriver/chromedriver.exe")
    else:
        st.error("Unsupported platform")
        return None

    options.binary_location = chrome_path
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver

def main():
    st.title("WOS Downloader App")
    url = st.text_input("Enter URL")
    # New text input for the search query for naming purposes
    search_query = st.text_input("Enter search query (for filename)", value="")
    
    # Save the query in session state for later use
    if search_query:
        st.session_state.search_query = search_query

    # Button to start and open Chrome
    if st.button("Start and open Chrome") and url:
        if "driver" not in st.session_state:
            driver = create_driver()
            if driver is None:
                return
            st.session_state.driver = driver
            driver.get(url)
            st.info("Chrome has been opened with the given URL. **Please log in manually** in the Chrome window. Once logged in, click the **Continue after logging in** button below.")
        else:
            st.info("Driver already running. Please log in manually in the Chrome window.")

    # Button for continuing after manual login
    if "driver" in st.session_state and st.button("Continue after logging in"):
        driver = st.session_state.driver
        time.sleep(5)  # Brief pause for page stabilization

        if is_university_front_page(driver):
            download_data_university(driver)
        elif is_other_network_front_page(driver):
            download_data_other_network(driver)
        else:
            st.error("Front page not recognized. Cannot proceed with download.")
        
        driver.quit()
        del st.session_state.driver

def is_university_front_page(driver):
    try:
        driver.find_element(By.ID, "onetrust-close-btn-container")
        return True
    except Exception:
        return False

def download_data_university(driver):
    # Close any pop-ups if available.
    try:
        onetrust_banner = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "onetrust-close-btn-container"))
        )
        onetrust_banner.click()
        tour_close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Close this tour']"))
        )
        tour_close_button.click()
    except TimeoutException:
        pass

    n_result_text = driver.find_element(By.CLASS_NAME, "brand-blue").text  
    n_result = int(n_result_text.replace(",", ""))
    n_iter = math.ceil(n_result / 500)
    TIME_GAP = 1
    progress_bar = st.progress(0)

    for iter in range(n_iter):
        progress_text = f"Downloading {iter + 1} out of {n_iter} file(s). Please don't close the browser."
        progress_bar.progress((iter + 1) / n_iter, text=progress_text)
        time.sleep(TIME_GAP)

        # Click the export menu.
        try:
            export_menu = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.TAG_NAME, "app-export-menu"))
            )
            export_menu.click()
        except TimeoutException:
            st.error("Export menu not clickable.")
            continue

        random_delay()
        
        # Select the Bib format option using the new selector.
        try:
            bib_option = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#mat-menu-panel-13 > div > div > div:nth-child(7)"))
            )
            bib_option.click()
        except TimeoutException:
            st.error("Bib format option not found.")
            continue

        random_delay()
        
        # Click the radio button for record content selection.
        try:
            radio_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[for='radio3-input']"))
            )
            radio_btn.click()
        except TimeoutException:
            st.error("Radio button [for='radio3-input'] not clickable. Please verify the selector.")
            continue

        random_delay()
        
        # Input the record range.
        from_rec, to_rec = 500 * iter + 1, 500 * (iter + 1)
        input_elements = driver.find_elements(By.CLASS_NAME, "mat-input-element")
        if len(input_elements) >= 2:
            input_el_from, input_el_to = input_elements[0], input_elements[1]
            input_el_from.clear()
            input_el_from.send_keys(from_rec)
            input_el_to.clear()
            input_el_to.send_keys(to_rec)
        else:
            st.error("Record input elements not found.")
            continue

        random_delay()
        
        # Click the dropdown to open data options.
        try:
            dropdown = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "dropdown"))
            )
            dropdown.click()
        except TimeoutException:
            st.error("Dropdown element not clickable.")
            continue

        random_delay()
        
        # Choose "Full Record and Cited References".
        try:
            data_option = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[title='Full Record and Cited References']"))
            )
            data_option.click()
        except TimeoutException:
            st.error("Data option 'Full Record and Cited References' not found.")
            continue

        random_delay()
        
        # Click the Export button using selector "#exportButton".
        try:
            export_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#exportButton"))
            )
            export_btn.click()
        except TimeoutException:
            st.error("Export button with selector '#exportButton' not clickable.")
            continue

        # Wait until the export popup dialog is no longer visible.
        wait = WebDriverWait(driver, 60)
        try:
            wait.until_not(EC.visibility_of_element_located((By.CLASS_NAME, "window")))
        except TimeoutException:
            st.warning("Timed out waiting for popup dialog to disappear, retrying...")

        st.success(f"SUCCESS DOWNLOADED FROM {from_rec} TO {to_rec}")
        
        # Attempt to rename the downloaded file
        if "search_query" in st.session_state:
            new_filename = generate_filename(st.session_state.search_query, from_rec, to_rec)
            if os.path.exists(DEFAULT_DOWNLOAD_NAME):
                os.rename(DEFAULT_DOWNLOAD_NAME, new_filename)
                st.success(f"File renamed to: {new_filename}")
            else:
                st.warning("Downloaded file not found for renaming.")
        else:
            st.warning("Search query not provided; file not renamed.")
        
        random_delay()

def is_other_network_front_page(driver):
    try:
        driver.find_element(By.ID, "mat-input-0")
        driver.find_element(By.ID, "mat-input-1")
        driver.find_element(By.ID, "signIn-btn")
        return True
    except Exception:
        return False

def download_data_other_network(driver):
    try:
        sign_in_button = driver.find_element(By.ID, "signIn-btn")
        WebDriverWait(driver, 300).until(EC.invisibility_of_element(sign_in_button))
        time.sleep(10)
        onetrust_banner = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "onetrust-close-btn-container"))
        )
        onetrust_banner.click()
        tour_close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Close this tour']"))
        )
        tour_close_button.click()
    except TimeoutException:
        pass

    n_result_text = driver.find_element(By.CLASS_NAME, "brand-blue").text  
    n_result = int(n_result_text.replace(",", ""))
    n_iter = math.ceil(n_result / 500)
    TIME_GAP = 1
    progress_bar = st.progress(0)

    for iter in range(n_iter):
        progress_text = f"Downloading {iter + 1} out of {n_iter} file(s). Please don't close the browser."
        progress_bar.progress((iter + 1) / n_iter, text=progress_text)
        time.sleep(TIME_GAP)

        try:
            export_menu = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.TAG_NAME, "app-export-menu"))
            )
            export_menu.click()
        except TimeoutException:
            st.error("Export menu not clickable.")
            continue

        random_delay()
        
        try:
            bib_option = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#mat-menu-panel-13 > div > div > div:nth-child(7)"))
            )
            bib_option.click()
        except TimeoutException:
            st.error("Bib format option not found.")
            continue

        random_delay()
        
        try:
            radio_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[for='radio3-input']"))
            )
            radio_btn.click()
        except TimeoutException:
            st.error("Radio button [for='radio3-input'] not clickable.")
            continue

        random_delay()
        
        from_rec, to_rec = 500 * iter + 1, 500 * (iter + 1)
        input_elements = driver.find_elements(By.CLASS_NAME, "mat-input-element")
        if len(input_elements) >= 2:
            input_el_from, input_el_to = input_elements[0], input_elements[1]
            input_el_from.clear()
            input_el_from.send_keys(from_rec)
            input_el_to.clear()
            input_el_to.send_keys(to_rec)
        else:
            st.error("Record input elements not found.")
            continue

        random_delay()
        
        try:
            dropdown = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "dropdown"))
            )
            dropdown.click()
        except TimeoutException:
            st.error("Dropdown element not clickable.")
            continue

        random_delay()
        
        try:
            data_option = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[title='Full Record and Cited References']"))
            )
            data_option.click()
        except TimeoutException:
            st.error("Data option 'Full Record and Cited References' not found.")
            continue

        random_delay()
        
        try:
            export_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#exportButton"))
            )
            export_btn.click()
        except TimeoutException:
            st.error("Export button with selector '#exportButton' not clickable.")
            continue

        wait = WebDriverWait(driver, 60)
        try:
            wait.until_not(EC.visibility_of_element_located((By.CLASS_NAME, "window")))
        except TimeoutException:
            st.warning("Timed out waiting for popup dialog to disappear, retrying...")

        st.success(f"SUCCESS DOWNLOADED FROM {from_rec} TO {to_rec}")
        
        # Rename downloaded file using the search query, record range, and prefix.
        if "search_query" in st.session_state:
            new_filename = generate_filename(st.session_state.search_query, from_rec, to_rec)
            if os.path.exists(DEFAULT_DOWNLOAD_NAME):
                os.rename(DEFAULT_DOWNLOAD_NAME, new_filename)
                st.success(f"File renamed to: {new_filename}")
            else:
                st.warning("Downloaded file not found for renaming.")
        else:
            st.warning("Search query not provided; file not renamed.")
        
        random_delay()

if __name__ == "__main__":
    main()