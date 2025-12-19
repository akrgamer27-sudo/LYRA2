import streamlit as st
import tempfile
import os
import numpy as np
import soundfile as sf

st.set_page_config(
    page_title="LYRA – Music Studio",
    page_icon="🎧",
    layout="centered"
)

st.title("🎧 LYRA")
st.subheader("Python-based Audio Web Application")

st.markdown(
    """
    Upload a song and control its sound using sliders.
    This is a Python web application built using Streamlit.
    """
)

# -----------------------------
# File upload
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload an MP3 or WAV file",
    type=["mp3", "wav"]
)

if uploaded_file is not None:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(uploaded_file.read())
        audio_path = tmp.name

    # Load audio
    audio, sr = sf.read(audio_path)

    st.audio(audio_path)

    st.divider()
    st.subheader("🎚 Audio Controls")

    # Sliders
    vocal_gain = st.slider("🎤 Vocal (Mid frequencies)", 0.0, 2.0, 1.0, 0.01)
    drum_gain = st.slider("🥁 Drums (Low frequencies)", 0.0, 2.0, 1.0, 0.01)
    synth_gain = st.slider("🎹 Synth (High frequencies)", 0.0, 2.0, 1.0, 0.01)

    # Simple frequency-based processing
    fft = np.fft.rfft(audio, axis=0)
    freqs = np.fft.rfftfreq(len(audio), d=1/sr)

    low = freqs < 250
    mid = (freqs >= 250) & (freqs < 4000)
    high = freqs >= 4000

    fft[low] *= drum_gain
    fft[mid] *= vocal_gain
    fft[high] *= synth_gain

    processed_audio = np.fft.irfft(fft, axis=0)

    # Save processed audio
    out_path = os.path.join(tempfile.gettempdir(), "lyra_mix.wav")
    sf.write(out_path, processed_audio, sr)

    st.success("Audio processed successfully!")
    st.audio(out_path)

    with open(out_path, "rb") as f:
        st.download_button(
            "⬇ Download Mixed Audio",
            f,
            file_name="lyra_mix.wav",
            mime="audio/wav"
        )

else:
    st.info("Please upload an audio file to begin.")

