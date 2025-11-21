import streamlit as st
import time
from PIL import Image
import pandas as pd
import io
import os # Import os to check for environment variables/secrets


# Import the newly defined GeminiClient
from api_client import GeminiClient, APIError
from prompts import get_system_prompt


# Page configuration

# Custom Amusing Style
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
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #ff9671;
        transform: scale(1.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(
    page_title="Cattle AI Classifier",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

def process_uploaded_image(uploaded_file):
    """Process uploaded image and convert to JPEG in memory"""
    try:
        # Open image directly from uploaded file
        img = Image.open(uploaded_file)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save to memory buffer as JPEG
        img_buffer = io.BytesIO()
        # Ensure the buffer is reset before reading/sending to API
        img.save(img_buffer, format='JPEG', quality=95)
        img_buffer.seek(0)
        
        return img_buffer, img.size
    except Exception as e:
        st.error(f"Error processing image {uploaded_file.name}: {str(e)}")
        return None, None


def display_image_with_analysis(uploaded_file, image_size, analysis_result, index):
    """Display image alongside its analysis"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(uploaded_file, caption=f"Image {index + 1}", width='stretch')
        
        # Image info
        if image_size:
            st.caption(f"Size: {image_size[0]}x{image_size[1]} pixels")

    
    with col2:
        if analysis_result.get("success"):
            st.success(f"✅ Analysis Complete (Model: {analysis_result['model_used']})")
            
            # Display analysis in expandable section
            with st.expander("📋 Full Analysis", expanded=True):
                # Using st.markdown to properly render potential markdown from the API response
                st.markdown(analysis_result["analysis"]) 
            
            # Token usage info
            if analysis_result.get("tokens_used"):
                st.caption(f"Tokens used: {analysis_result['tokens_used']}")
        
        elif analysis_result.get("error"):
            st.error(f"❌ Analysis Failed: {analysis_result['error']}")
        else:
            st.info("⏳ Analysis pending...")

def export_results_to_excel():
    """Export analysis results to Excel"""
    if not st.session_state.analysis_results:
        st.warning("No results to export!")
        return
    
    # Prepare data for Excel
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
        
        # Create an Excel buffer
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Analysis Results')
        
        st.download_button(
            label="📥 Download Results as Excel",
            data=excel_buffer.getvalue(),
            file_name=f"cattle_analysis_results_{int(time.time())}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


def main():
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🐄 Cattle AI Classifier")
    st.markdown("**AI-powered breed recognition and type classification for cattle and buffaloes**")
    

    # Fun interactive sidebar (replaces configuration)
    st.sidebar.markdown("## 🎪 Welcome to the Fun Barn!")
    st.sidebar.write("Pick a playful mode and have fun while the AI works behind the scenes.")
    mode = st.sidebar.selectbox("Choose a mode", ["Cow Mode 🐄", "Buffalo Mode 🐃", "Detective Mode 🕵️", "Party Mode 🎉"])
    st.sidebar.write("Mode description:")
    if mode == "Cow Mode 🐄":
        st.sidebar.write("Gentle and accurate — favors breed recognition.")
        task_type = "breed_recognition"
    elif mode == "Buffalo Mode 🐃":
        st.sidebar.write("Robust and strong — favors type classification.")
        task_type = "type_classification"
    elif mode == "Detective Mode 🕵️":
        st.sidebar.write("Deep analysis mode — higher verbosity.")
        task_type = "breed_recognition"
    else:
        st.sidebar.write("Random fun! Mix of both.")
        import random
        task_type = random.choice(["breed_recognition", "type_classification"])
        if st.sidebar.button("🎲 Surprise me!"):
            st.sidebar.balloons()

    st.sidebar.divider()
    st.sidebar.markdown("### 🎯 Quick Presets")
    if st.sidebar.button("🔎 Quick Breed (Fast)"):
        task_type = "breed_recognition"
        st.sidebar.success("Preset applied: Quick Breed")
    if st.sidebar.button("🏷️ Quick Type (Fast)"):
        task_type = "type_classification"
        st.sidebar.success("Preset applied: Quick Type")

    st.sidebar.markdown("### ✨ Fun Extras")
    if st.sidebar.button("📸 Show Random Cow Fact"):
        facts = [
            "Cows have almost panoramic vision — great for spotting surprises!",
            "A cow's nose print is as unique as a human fingerprint.",
            "Cows have four stomach compartments — that's multi-tasking digestion!"
        ]
        import random
        st.sidebar.info(random.choice(facts))

    
# Password-protected settings modal
if st.sidebar.button("🔒 Open Settings"):
    st.session_state["show_settings_modal"] = True

# Render modal if requested
if st.session_state.get("show_settings_modal"):
    # Simple modal UI
    st.markdown('<div class="modal-overlay"><div class="modal-box">', unsafe_allow_html=True)
    pwd = st.text_input("Enter admin password to unlock settings", type="password")
    cols = st.columns([3,1])
    with cols[1]:
        if st.button("Unlock"):
            if pwd == "letmein123":  # demo password; you can change this
                st.session_state["settings_unlocked"] = True
                st.session_state["show_settings_modal"] = False
                st.experimental_rerun()
            else:
                st.error("Incorrect password.")
    st.markdown('</div></div>', unsafe_allow_html=True)

# If unlocked, show hidden developer settings somewhere
if st.session_state.get("settings_unlocked"):
    with st.expander("🔧 Developer Settings (Unlocked)", expanded=True):
        api_key = st.text_input("Gemini API Key (paste here)", value=st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or "")
        demo_mode = st.checkbox("Demo mode (simulate results)", value=True)
        if st.button("Save Developer Settings"):
            st.success("Settings saved for this session.")
# Hidden developer settings for API key and advanced options
    with st.sidebar.expander("🔧 Developer Settings (Advanced)", expanded=False):
        api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("⚠️ Gemini API key not configured! Add it in secrets or environment to enable real analysis.")
            # For demo mode, allow a fake key toggle
            demo = st.checkbox("Enable demo mode (no external API)", value=True)
            if demo:
                st.warning("Demo mode: results will be simulated.")
        else:
            st.success("🔒 Gemini API key detected.")

    
    # --- API Key handling for Gemini ---
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        st.sidebar.error("⚠️ Gemini API key not configured!")
        st.error("🔧 Application configuration error. Please ensure GEMINI_API_KEY is set in secrets or environment.")
        st.stop()
    
    # Initialize client
    try:
        # Use the dedicated GeminiClient
        client = GeminiClient(api_key=api_key)
    except ValueError as e:
        st.sidebar.error(f"Initialization Error: {e}")
        st.error("🔧 Application configuration error. Please contact the administrator.")
        st.stop()
    
    # --- Model selection for direct Gemini ---
    # Since we are using a direct client, we must specify a Gemini model that supports vision
    GEMINI_VISION_MODEL = "gemini-2.5-flash"
    
    # Model display (now fixed to a single model)
    selected_model = st.sidebar.text_input(
        "🤖 Selected AI Model (Vision)",
        GEMINI_VISION_MODEL,
        disabled=True,
        help="Using a dedicated Gemini Vision model."
    )
    
    # Task type selection moved to main area as large emoji-based selector
    # Default task_type (will be set by main controls below)
    task_type = st.session_state.get("task_type", "breed_recognition")
    
    # Main interface
    
# --- Large emoji-based selector (main area) ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🎛️ Pick a Fun Mode (big buttons!)")
col1, col2, col3, col4 = st.columns(4)
if "task_type" not in st.session_state:
    st.session_state["task_type"] = "breed_recognition"
with col1:
    if st.button("🐄\nCow Mode\n( Breed )", use_container_width=True):
Cow Mode
( Breed )", use_container_width=True):
        st.session_state["task_type"] = "breed_recognition"
with col2:
    if st.button("🐃
Buffalo Mode
( Type )", use_container_width=True):
        st.session_state["task_type"] = "type_classification"
with col3:
    if st.button("🕵️
Detective
( Deep )", use_container_width=True):
        st.session_state["task_type"] = "breed_recognition"
with col4:
    if st.button("🎉
Party
( Surprise )", use_container_width=True):
        import random
        st.session_state["task_type"] = random.choice(["breed_recognition", "type_classification"])

st.markdown(f"**Selected mode:** {st.session_state['task_type']}")
# --- end selector ---

# --- Audio and animation setup ---
# Simple short beep wav (encoded bytes). This is a tiny 0.1s sine wave beep.
BEEP_WAV = b'RIFF$\x00\x00\x00WAVEfmt ' + b'\x10\x00\x00\x00' + b'\x01\x00\x01\x00' + b'\x40\x1f\x00\x00' + b'\x80>\x00\x00' + b'\x02\x00\x10\x00' + b'data\x00\x00\x00\x00'
# Note: For a real app, replace with a proper short audio file in the repo.

# CSS for modal-like settings and badges
st.markdown(
    """<style>
    /* Modal overlay */
    .modal-overlay {
        position: fixed;
        top: 0; left: 0; right:0; bottom:0;
        background: rgba(0,0,0,0.45);
        display:flex;
        align-items:center;
        justify-content:center;
        z-index:9999;
    }
    .modal-box {
        background: white;
        padding: 20px;
        border-radius: 12px;
        width: 360px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    /* Animated badge */
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
    </style>""", unsafe_allow_html=True
)
# --- end CSS ---

st.header("📤 Upload Images")
    
    uploaded_files = st.file_uploader(
        "Upload cattle/buffalo images for analysis",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        help="You can upload up to 10 images at once"
    )
    
    # Process uploaded files
    if uploaded_files:
        if len(uploaded_files) > 10:
            st.warning("⚠️ Maximum 10 images allowed. Only the first 10 will be processed.")
            uploaded_files = uploaded_files[:10]
        
        # Save files and update session state if needed
        current_file_names = [f.name for f in uploaded_files]
        session_file_names = [f["name"] for f in st.session_state.uploaded_files]
        
        # Check if new files were uploaded
        if current_file_names != session_file_names or not st.session_state.uploaded_files:
            # Clear previous results and re-process new files
            st.session_state.analysis_results = []
            st.session_state.uploaded_files = []
            
            # Process uploaded files in memory
            for uploaded_file in uploaded_files:
                img_buffer, img_size = process_uploaded_image(uploaded_file)
                if img_buffer:
                    st.session_state.uploaded_files.append({
                        "name": uploaded_file.name,
                        "buffer": img_buffer,
                        "size": img_size,
                        "original_file": uploaded_file
                    })

        
        # Analysis section
        st.header("🔬 Analysis Results")
        
        # Progress tracking
        total_files = len(st.session_state.uploaded_files)
        
        # Analyze all button
        if st.button("🚀 Analyze All Images", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Get system prompt for selected task
            system_prompt = get_system_prompt(task_type)
            
            # Reset results before starting new analysis
            st.session_state.analysis_results = []
            
            for i, file_info in enumerate(st.session_state.uploaded_files):
                status_text.text(f"Analyzing image {i+1}/{total_files}: {file_info['name']}")
                
                # Perform analysis using image buffer
                result = client.analyze_image_from_buffer(
                    image_buffer=file_info["buffer"], 
                    model_name=selected_model, 
                    system_prompt=system_prompt
                )
                st.session_state.analysis_results.append(result)
                
                # Update progress
                progress_bar.progress((i + 1) / total_files)
                
                # Brief delay between requests to be polite to the API
                time.sleep(0.5)
            
            status_text.text("✅ All analyses complete!")
            progress_bar.progress(1.0)
            time.sleep(1)
            status_text.empty()
            progress_bar.empty()
        
        # Display results
        if st.session_state.analysis_results:
            # Summary statistics
            successful_analyses = len([r for r in st.session_state.analysis_results if r.get("success")])
            failed_analyses = len([r for r in st.session_state.analysis_results if r.get("error")])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Successful", successful_analyses)
            with col2:
                st.metric("❌ Failed", failed_analyses)
            with col3:
                st.metric("📊 Total", len(st.session_state.uploaded_files))
            
            # Export button
            if successful_analyses > 0:
                export_results_to_excel()
            
            st.divider()
            
            # Display individual results
            for i, (file_info, result) in enumerate(zip(st.session_state.uploaded_files, st.session_state.analysis_results)):
                with st.container():
                    # Pass the original Streamlit file object for display
                    display_image_with_analysis(file_info["original_file"], file_info["size"], result, i)
                    if i < len(st.session_state.uploaded_files) - 1:
                        st.divider()

        
        elif st.session_state.uploaded_files:
            st.info("👆 Click 'Analyze All Images' to start the analysis process.")
    
    # Footer information
    st.divider()
    with st.expander("ℹ️ About this Application"):
        st.markdown(f"""
        **Cattle AI Classifier** is designed to solve two key problem statements from the Ministry of Fisheries, Animal Husbandry & Dairying:
        
        1. **Problem Statement ID 25005**: Image-based Animal Type Classification for cattle and buffaloes
        2. **Problem Statement ID 25004**: Image-based breed recognition for cattle and buffaloes of India
        
        
# --- Post-analysis celebration (fallback placement) ---
try:
    st.balloons()
except Exception:
    pass
try:
    st.audio(BEEP_WAV, format='audio/wav')
except Exception:
    pass
st.markdown("### 🏅 Result Badges (Demo)")
cols = st.columns(3)
import random
acc = random.randint(75, 99)
conf = random.randint(60, 99)
speed = random.choice(["Fast", "Medium", "Slow"])
cols[0].markdown(f"<div class='badge'>Accuracy: {acc}%</div>", unsafe_allow_html=True)
cols[1].markdown(f"<div class='badge'>Confidence: {conf}%</div>", unsafe_allow_html=True)
cols[2].markdown(f"<div class='badge'>Speed: {speed}</div>", unsafe_allow_html=True)
**Features:**
        - Upload up to 10 images for batch analysis
        - Uses the dedicated **Gemini Vision API** ({GEMINI_VISION_MODEL})
        - Breed recognition for Indian cattle and buffalo breeds
        - Animal type classification for breeding assessment
        - Export results to Excel format
        - Secure in-memory image processing
        """)

if __name__ == "__main__":
    main()
