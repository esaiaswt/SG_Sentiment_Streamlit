import streamlit as st
import subprocess
import threading
import time
import os
from streamlit.components.v1 import html

# Set Streamlit page config
def set_page_config():
    st.set_page_config(
        page_title="SG Sentiment Map",
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon="🗺️",
        menu_items={}
    )

set_page_config()

st.title("SG Today's Sentiment")
st.markdown("""
This app visualizes the latest sentiment of Singapore news articles on an interactive map. The data is automatically refreshed every 8 hours, and you can view the most recent sentiment analysis results directly on the map below.

**How to use this app:**
- The map below shows the latest sentiment analysis of Singapore news articles.
- Click on the emoji on the map to view the news details.
- The data and map refresh automatically every 8 hours; you do not need to reload the page.
- When the data is being updated, a progress bar and log output will be shown.
- Once the update is complete, the map will be displayed in wide screen.
""")

st.markdown(
    """
    <style>
    body { background-color: #0e1117; }
    .stApp { background-color: #0e1117; }
    </style>
    """,
    unsafe_allow_html=True
)

LOG_FILE = "pipeline_log.txt"
MAP_FILE = "singapore_news_sentiment_map.html"
PIPELINE_SCRIPT = "run_pipeline.py"

# Function to run pipeline and capture output
def run_pipeline_with_progress():
    progress = st.progress(0)
    log_box = st.empty()
    logs = []
    
    process = subprocess.Popen(
        ["python", PIPELINE_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    total_steps = 100  # Dummy steps for progress bar
    step = 0
    for line in process.stdout:
        logs.append(line)
        log_box.text_area("Pipeline Output", value="".join(logs), height=300)
        step = min(step + 1, total_steps)
        progress.progress(step / total_steps)
    process.wait()
    progress.progress(1.0)
    return logs

# Function to clear screen and show map
def show_map():
    st.empty()
    if os.path.exists(MAP_FILE):
        with open(MAP_FILE, "r", encoding="utf-8") as f:
            map_html = f.read()
        html(map_html, height=800, width=None)  # Use full width
    else:
        st.error(f"Map file {MAP_FILE} not found.")

# Scheduler thread to run pipeline every 8 hours
def scheduler_thread():
    while True:
        run_pipeline_with_progress()
        time.sleep(8 * 60 * 60)  # 8 hours

def main():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        # Start scheduler in background
        threading.Thread(target=scheduler_thread, daemon=True).start()
        # Run pipeline at start
        run_pipeline_with_progress()
        st.rerun()
    else:
        show_map()

if __name__ == "__main__":
    main()
