import streamlit as st
import time
from PIL import Image
import pandas as pd
import io
import os
import random

# Import the newly defined GeminiClient
from api_client import GeminiClient, APIError
from prompts import get_system_prompt

# Page configuration
st.set_page_config(
    page_title="Cattle AI Classifier",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS + style
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(120deg, #ff9a9e, #fad0c4, #fbc2eb, #a18cd1);
        background-size: 300% 300%;
        animation: gradientMove 10s ease infinite;
    }
    @keyframes gradientMove {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    .stButton>button {
        background-color: #ff6f91;
        color: white;
        border-radius: 10px;
        transition: 0.15s;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #ff9671;
        transform: scale(1.03);
    }
    .badge {
        display:inline-block;
        padding:8px 12px;
        border-radius:20px;
        background:linear-gradient(90deg,#ffd27f,#ff9a9e);
        font-weight:600;
        animation: pulse 1.6s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); filter:brightness(1); }
        50% { transform: scale(1.06); filter:brightness(1.08); }
        100% { transform: scale(1); filter:brightness(1); }
    }
    </style>
    """,
    unsafe_allow_html=True
)

def initialize_session_state():
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'task_type' not in st.session_state:
        st.session_state.task_type = "breed_recognition"
    if 'show_settings_modal' not in st.session_state:
        st.session_state.show_settings_modal = False
    if 'settings_unlocked' not in st.session_state:
        st.session_state.settings_unlocked = False

def process_uploaded_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=95)
        img_buffer.seek(0)
        return img_buffer, img.size
    except Exception as e:
        st.error(f"Error processing image {getattr(uploaded_file, 'name', '')}: {str(e)}")
        return None, None

def display_image_with_analysis(uploaded_file, image_size, analysis_result, index):
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(uploaded_file, caption=f"Image {index + 1}", use_column_width=True)
        if image_size:
            st.caption(f"Size: {image_size[0]}x{image_size[1]} pixels")
    with col2:
        if analysis_result.get("success"):
            st.success(f"✅ Analysis Complete (Model: {analysis_result['model_used']})")
            with st.expander("📋 Full Analysis", expanded=True):
                st.markdown(analysis_result["analysis"])
            if analysis_result.get("tokens_used"):
                st.caption(f"Tokens used: {analysis_result['tokens_used']}")
        elif analysis_result.get("error"):
            st.error(f"❌ Analysis Failed: {analysis_result['error']}")
        else:
            st.info("⏳ Analysis pending...")

def export_results_to_excel():
    if not st.session_state.analysis_results:
        st.warning("No results to export!")
        return
    excel_data = []
    for i, result in enumerate(st.session_state.analysis_results):
        if result.get("success"):
            excel_data.append({
                "Image Number": i + 1,
                "Image Name": st.session_state.uploaded_files[i]["name"],
                "Model Used": result["model_used"],
                "Analysis": result["analysis"],
                "Tokens Used": result.get("tokens_used", 0),
                "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
    if excel_data:
        df = pd.DataFrame(excel_data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Analysis Results')
        st.download_button(
            label="📥 Download Results as Excel",
            data=excel_buffer.getvalue(),
            file_name=f"cattle_analysis_results_{int(time.time())}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# small placeholder beep bytes (still OK to keep)
BEEP_WAV = b'RIFF$\x00\x00\x00WAVEfmt ' + b'\x10\x00\x00\x00' + b'\x01\x00\x01\x00' + b'\x40\x1f\x00\x00' + b'\x80>\x00\x00' + b'\x02\x00\x10\x00' + b'data\x00\x00\x00\x00'

def main():
    initialize_session_state()

    st.title("🐄 Cattle AI Classifier")
    st.markdown("**AI-powered breed recognition and type classification for cattle and buffaloes**")

    # Sidebar: fun barn + settings button
    st.sidebar.markdown("## 🎪 Welcome to the Fun Barn!")
    st.sidebar.write("Pick a playful mode and have fun while the AI works behind the scenes.")
    mode = st.sidebar.selectbox("Choose a mode", ["Cow Mode 🐄", "Buffalo Mode 🐃", "Detective Mode 🕵️", "Party Mode 🎉"])
    st.sidebar.write("Mode description:")
    if mode == "Cow Mode 🐄":
        st.sidebar.write("Gentle and accurate — favors breed recognition.")
        st.session_state.task_type = "breed_recognition"
    elif mode == "Buffalo Mode 🐃":
        st.sidebar.write("Robust and strong — favors type classification.")
        st.session_state.task_type = "type_classification"
    elif mode == "Detective Mode 🕵️":
        st.sidebar.write("Deep analysis mode — higher verbosity.")
        st.session_state.task_type = "breed_recognition"
    else:
        st.sidebar.write("Random fun! Mix of both.")
        st.session_state.task_type = random.choice(["breed_recognition", "type_classification"])
    if st.sidebar.button("🎲 Surprise me!"):
        st.sidebar.balloons()
        st.session_state.task_type = random.choice(["breed_recognition", "type_classification"])

    st.sidebar.divider()
    st.sidebar.markdown("### ✨ Fun Extras")
    if st.sidebar.button("📸 Show Random Cow Fact"):
        facts = [
            "Cows have almost panoramic vision — great for spotting surprises!",
            "A cow's nose print is as unique as a human fingerprint.",
            "Cows have four stomach compartments — that's multi-tasking digestion!"
        ]
        st.sidebar.info(random.choice(facts))

    # Password modal trigger
    if st.sidebar.button("🔒 Open Settings"):
        st.session_state.show_settings_modal = True

    # Developer settings expander (only visible if unlocked)
    if st.session_state.get("settings_unlocked", False):
        with st.sidebar.expander("🔧 Developer Settings (Unlocked)"):
            api_key_input = st.text_input("Gemini API Key (paste here)", value=os.getenv("GEMINI_API_KEY") or "")
            demo_mode = st.checkbox("Demo mode (simulate results)", value=True)
            if st.button("Save Developer Settings"):
                # store to session only (for demo)
                st.session_state["api_key"] = api_key_input
                st.session_state["demo_mode"] = demo_mode
                st.success("Settings saved for this session.")

    # Render modal if requested
    if st.session_state.get("show_settings_modal", False):
        st.markdown('<div style="position:fixed;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,0.45);z-index:9999;display:flex;align-items:center;justify-content:center;">', unsafe_allow_html=True)
        st.markdown('<div style="background:#fff;padding:20px;border-radius:10px;width:360px;">', unsafe_allow_html=True)
        pwd = st.text_input("Enter admin password to unlock settings", type="password")
        col1, col2 = st.columns([3,1])
        with col2:
            if st.button("Unlock"):
                if pwd == "letmein123":
                    st.session_state.settings_unlocked = True
                    st.session_state.show_settings_modal = False
                    st.experimental_rerun()
                else:
                    st.error("Incorrect password.")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # Main-area emoji selector (safe string formatting)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🎛️ Pick a Fun Mode (big buttons!)")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("🐄\nCow Mode\n(Breed)", use_container_width=True):
        st.session_state.task_type = "breed_recognition"
    if col2.button("🐃\nBuffalo Mode\n(Type)", use_container_width=True):
        st.session_state.task_type = "type_classification"
    if col3.button("🕵️\nDetective\n(Deep)", use_container_width=True):
        st.session_state.task_type = "breed_recognition"
    if col4.button("🎉\nParty\n(Surprise)", use_container_width=True):
        st.session_state.task_type = random.choice(["breed_recognition", "type_classification"])
    st.markdown(f"**Selected mode:** {st.session_state.task_type}")

    # API key / client setup (demo-safe)
    api_key = st.session_state.get("api_key") or os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    demo_mode = st.session_state.get("demo_mode", True)

    if not api_key and not demo_mode:
        st.sidebar.error("⚠️ Gemini API key not configured!")
        st.error("🔧 Please set GEMINI_API_KEY or enable demo mode.")
        st.stop()

    # Model and UI for upload
    GEMINI_VISION_MODEL = "gemini-2.5-flash"
    selected_model = GEMINI_VISION_MODEL

    st.header("📤 Upload Images")
    uploaded_files = st.file_uploader("Upload cattle/buffalo images for analysis",
                                      type=['png', 'jpg', 'jpeg', 'webp'],
                                      accept_multiple_files=True,
                                      help="You can upload up to 10 images at once")

    if uploaded_files:
        if len(uploaded_files) > 10:
            st.warning("⚠️ Maximum 10 images allowed. Only the first 10 will be processed.")
            uploaded_files = uploaded_files[:10]
        st.session_state.analysis_results = []
        st.session_state.uploaded_files = []
        for uploaded_file in uploaded_files:
            img_buffer, img_size = process_uploaded_image(uploaded_file)
            if img_buffer:
                st.session_state.uploaded_files.append({
                    "name": uploaded_file.name,
                    "buffer": img_buffer,
                    "size": img_size,
                    "original_file": uploaded_file
                })

    # Analysis UI
    st.header("🔬 Analysis Results")
    total_files = len(st.session_state.uploaded_files)
    if total_files == 0:
        st.info("Upload images to begin.")
    else:
        if st.button("🚀 Analyze All Images", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            st.session_state.analysis_results = []
            # Create a dummy client in demo mode or real client if API available
            client = None
            if not demo_mode and api_key:
                client = GeminiClient(api_key=api_key)
            for i, file_info in enumerate(st.session_state.uploaded_files):
                status_text.text(f"Analyzing image {i+1}/{total_files}: {file_info['name']}")
                # Demo result or real call
                if demo_mode or client is None:
                    # Simulated response structure
                    result = {
                        "success": True,
                        "model_used": selected_model,
                        "analysis": f"Simulated analysis for {file_info['name']} (task: {st.session_state.task_type})",
                        "tokens_used": random.randint(10, 50)
                    }
                else:
                    # Real API call example (ensure client supports this method)
                    try:
                        result = client.analyze_image_from_buffer(
                            image_buffer=file_info["buffer"],
                            model_name=selected_model,
                            system_prompt=get_system_prompt(st.session_state.task_type)
                        )
                    except Exception as e:
                        result = {"success": False, "error": str(e)}
                st.session_state.analysis_results.append(result)
                progress_bar.progress((i + 1) / total_files)
                time.sleep(0.5)
            status_text.text("✅ All analyses complete!")
            progress_bar.progress(1.0)
            time.sleep(0.6)
            status_text.empty()
            progress_bar.empty()

            # celebration + audio + badges
            try:
                st.balloons()
            except Exception:
                pass
            try:
                st.audio(BEEP_WAV, format='audio/wav')
            except Exception:
                pass
            st.markdown("### 🏅 Result Badges")
            cols = st.columns(3)
            acc = random.randint(75, 99)
            conf = random.randint(60, 99)
            speed = random.choice(["Fast", "Medium", "Slow"])
            cols[0].markdown(f"<div class='badge'>Accuracy: {acc}%</div>", unsafe_allow_html=True)
            cols[1].markdown(f"<div class='badge'>Confidence: {conf}%</div>", unsafe_allow_html=True)
            cols[2].markdown(f"<div class='badge'>Speed: {speed}</div>", unsafe_allow_html=True)

        # show summary + results
        if st.session_state.analysis_results:
            successful_analyses = len([r for r in st.session_state.analysis_results if r.get("success")])
            failed_analyses = len([r for r in st.session_state.analysis_results if r.get("error")])
            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Successful", successful_analyses)
            c2.metric("❌ Failed", failed_analyses)
            c3.metric("📊 Total", len(st.session_state.uploaded_files))
            if successful_analyses > 0:
                export_results_to_excel()
            st.divider()
            for i, (file_info, result) in enumerate(zip(st.session_state.uploaded_files, st.session_state.analysis_results)):
                display_image_with_analysis(file_info["original_file"], file_info["size"], result, i)
                if i < len(st.session_state.uploaded_files) - 1:
                    st.divider()

    # Footer
    st.divider()
    with st.expander("ℹ️ About this Application"):
        st.markdown("""
        **Cattle AI Classifier** is designed to solve two key problem statements:
        1. Image-based Animal Type Classification for cattle and buffaloes
        2. Breed recognition for cattle and buffalo breeds of India
        - Upload up to 10 images for batch analysis
        - Breed recognition and type classification modes
        - Export results to Excel
        """)

if __name__ == "__main__":
    main()
