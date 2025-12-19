import streamlit as st
import os
import shutil
import glob
import subprocess
from demucs.separate import main as demucs_separate
import whisper
from pydub import AudioSegment

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

    # -------------------------------------------------
    # MP3 → WAV (SAFE METHOD)
    # -------------------------------------------------
    subprocess.run(
        ["ffmpeg", "-y", "-i", "song.mp3", "song.wav"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # -------------------------------------------------
    # STEM SEPARATION
    # -------------------------------------------------
    if st.button("🎛 Separate Stems"):
        with st.spinner("Separating stems with Demucs (this may take time)..."):

            output_dir = "demucs_output"

            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)

            demucs_separate([
                "-n", "htdemucs",
                "--two-stems=vocals",
                "--out", output_dir,
                "song.wav"
            ])

        st.success("Stems separated successfully!")

        # -------------------------------------------------
        # SAFE STEM FOLDER DETECTION
        # -------------------------------------------------
        stem_root = os.path.join(output_dir, "htdemucs")

        if not os.path.exists(stem_root):
            st.error("❌ Stem folder not found. Try a shorter audio.")
            st.stop()

        stem_folders = glob.glob(os.path.join(stem_root, "*"))

        if len(stem_folders) == 0:
            st.error("❌ No stems generated. Demucs may have failed.")
            st.stop()

        stem_folder = stem_folders[0]

        stems = {
            "vocals": os.path.join(stem_folder, "vocals.wav"),
            "drums": os.path.join(stem_folder, "drums.wav"),
            "bass": os.path.join(stem_folder, "bass.wav"),
            "other": os.path.join(stem_folder, "other.wav")
        }

        # -------------------------------------------------
        # MIXER UI
        # -------------------------------------------------
        st.subheader("🎚 Mixer")

        vocal_db = st.slider("Vocals", -40, 10, 0)
        drum_db = st.slider("Drums", -40, 10, 0)
        bass_db = st.slider("Bass", -40, 10, 0)
        other_db = st.slider("Synth / Other", -40, 10, 0)

        def mix_audio(volumes, output_name):
            mix = None
            for name, path in stems.items():
                audio = AudioSegment.from_file(path)
                audio = audio + volumes.get(name, 0)
                mix = audio if mix is None else mix.overlay(audio)
            mix.export(output_name, format="mp3")
            return output_name

        if st.button("▶ Preview Mix"):
            mixed_file = mix_audio(
                {
                    "vocals": vocal_db,
                    "drums": drum_db,
                    "bass": bass_db,
                    "other": other_db
                },
                "preview_mix.mp3"
            )
            st.audio(mixed_file)

        if st.button("⬇ Download Karaoke"):
            karaoke_file = mix_audio(
                {
                    "vocals": -100,
                    "drums": drum_db,
                    "bass": bass_db,
                    "other": other_db
                },
                "karaoke.mp3"
            )
            st.download_button(
                "Download Karaoke MP3",
                open(karaoke_file, "rb"),
                file_name="karaoke.mp3"
            )

    # -------------------------------------------------
    # LYRICS EXTRACTION
    # -------------------------------------------------
    if st.button("📝 Extract Lyrics"):
        with st.spinner("Transcribing using Whisper AI..."):
            model = whisper.load_model("base")
            result = model.transcribe("song.wav")
            lyrics = result["text"]

        st.subheader("Extracted Lyrics")
        st.text_area("Lyrics", lyrics, height=300)

        st.download_button(
            "⬇ Download Lyrics",
            lyrics,
            file_name="lyrics.txt"
        )

        st.info("⚠ Lyrics accuracy depends on language, accent, and audio quality.")
