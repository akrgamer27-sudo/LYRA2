import streamlit as st
import os
import shutil
import glob
import subprocess
import numpy as np
import soundfile as sf
from demucs.separate import main as demucs_separate
import whisper

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="LYRA – AI Music Studio",
    page_icon="🎧",
    layout="centered"
)

st.title("🎧 LYRA")
st.subheader("AI Music Studio • Mix • Separate • Transcribe")

# -------------------------------------------------
# FILE UPLOAD
# -------------------------------------------------
uploaded_file = st.file_uploader("Upload an MP3 file", type=["mp3"])

if uploaded_file is not None:
    with open("song.mp3", "wb") as f:
        f.write(uploaded_file.read())

    st.audio("song.mp3")

    # MP3 → WAV
    subprocess.run(
        ["ffmpeg", "-y", "-i", "song.mp3", "song.wav"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # -------------------------------------------------
    # STEM SEPARATION
    # -------------------------------------------------
    if st.button("🎛 Separate Stems"):
        with st.spinner("Separating stems with Demucs..."):

            output_dir = "demucs_output"
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

            demucs_separate([
                "-n", "htdemucs",
                "--two-stems=vocals",
                "--out", output_dir,
                "song.wav"
            ])

        st.success("Stems separated!")

        stem_root = os.path.join(output_dir, "htdemucs")
        folders = glob.glob(os.path.join(stem_root, "*"))

        if not folders:
            st.error("❌ Stem separation failed.")
            st.stop()

        stem_folder = folders[0]

        # -------------------------------------------------
        # LOAD STEMS (NUMPY)
        # -------------------------------------------------
        def load_wav(path):
            data, sr = sf.read(path)
            if data.ndim == 1:
                data = np.expand_dims(data, axis=1)
            return data, sr

        vocals, sr = load_wav(os.path.join(stem_folder, "vocals.wav"))
        drums, _ = load_wav(os.path.join(stem_folder, "drums.wav"))
        bass, _ = load_wav(os.path.join(stem_folder, "bass.wav"))
        other, _ = load_wav(os.path.join(stem_folder, "other.wav"))

        # -------------------------------------------------
        # MIXER UI
        # -------------------------------------------------
        st.subheader("🎚 Mixer")

        v_db = st.slider("Vocals", -40, 10, 0)
        d_db = st.slider("Drums", -40, 10, 0)
        b_db = st.slider("Bass", -40, 10, 0)
        o_db = st.slider("Synth / Other", -40, 10, 0)

        def db_to_gain(db):
            return 10 ** (db / 20)

        def mix_and_export(filename, mute_vocals=False):
            mix = (
                vocals * (0 if mute_vocals else db_to_gain(v_db)) +
                drums * db_to_gain(d_db) +
                bass * db_to_gain(b_db) +
                other * db_to_gain(o_db)
            )
            mix = np.clip(mix, -1.0, 1.0)
            sf.write(filename, mix, sr)

        if st.button("▶ Preview Mix"):
            mix_and_export("preview.wav")
            st.audio("preview.wav")

        if st.button("⬇ Download Karaoke"):
            mix_and_export("karaoke.wav", mute_vocals=True)
            st.download_button(
                "Download Karaoke",
                open("karaoke.wav", "rb"),
                file_name="karaoke.wav"
            )

    # -------------------------------------------------
    # LYRICS
    # -------------------------------------------------
    if st.button("📝 Extract Lyrics"):
        with st.spinner("Transcribing with Whisper..."):
            model = whisper.load_model("base")
            result = model.transcribe("song.wav")

        lyrics = result["text"]

        st.text_area("Lyrics", lyrics, height=300)
        st.download_button("⬇ Download Lyrics", lyrics, "lyrics.txt")
