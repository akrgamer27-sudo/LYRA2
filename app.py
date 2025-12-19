import streamlit as st
from pydub import AudioSegment
from demucs.separate import main as demucs_separate
import os, shutil, glob
import whisper

st.set_page_config(page_title="AI Audio Mixer & Lyrics App", layout="centered")
st.title("🎵 AI Audio Mixer & Lyrics App")

# -------------------------------
# 1️⃣ Upload MP3
uploaded_file = st.file_uploader("Upload your MP3", type=["mp3"])

if uploaded_file:
    with open("song.mp3", "wb") as f:
        f.write(uploaded_file.read())
    st.audio("song.mp3")

    # Convert to WAV to avoid TorchCodec issues
    audio = AudioSegment.from_file("song.mp3")
    audio.export("song.wav", format="wav")

    # -------------------------------
    # 2️⃣ Separate stems
    if st.button("Separate Stems"):
        with st.spinner("Separating stems with Demucs..."):
            output_dir = "demucs_output"
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            demucs_separate([
                "-n", "htdemucs",
                "--out", output_dir,
                "song.wav"  # Use WAV
            ])
        st.success("Stems separated!")

        # Locate stems
        stem_folder = glob.glob(os.path.join(output_dir, "htdemucs", "*"))[0]
        stems = {
            "lead": os.path.join(stem_folder, "vocals.wav"),
            "drums": os.path.join(stem_folder, "drums.wav"),
            "bass": os.path.join(stem_folder, "bass.wav"),
            "synth": os.path.join(stem_folder, "other.wav")
        }

        # -------------------------------
        # 3️⃣ Volume sliders
        st.subheader("Adjust Stem Volumes")
        lead_db = st.slider("Lead dB", -40, 10, 0)
        drums_db = st.slider("Drums dB", -40, 10, 0)
        bass_db = st.slider("Bass dB", -40, 10, 0)
        synth_db = st.slider("Synth/Other dB", -40, 10, 0)

        # Mix function
        def mix_stems(volumes, output_file="mixed_output.mp3"):
            final_mix = None
            for stem_name, path in stems.items():
                audio = AudioSegment.from_file(path)
                audio = audio + volumes.get(stem_name, 0)
                if final_mix is None:
                    final_mix = audio
                else:
                    final_mix = final_mix.overlay(audio)
            final_mix.export(output_file, format="mp3")
            return output_file

        # Preview mixed audio
        if st.button("Preview Mix"):
            mixed_file = mix_stems({
                "lead": lead_db,
                "drums": drums_db,
                "bass": bass_db,
                "synth": synth_db
            })
            st.audio(mixed_file)

        # Download Karaoke version
        if st.button("Download Karaoke Version"):
            karaoke_file = mix_stems({
                "lead": -100,  # mute vocals
                "drums": drums_db,
                "bass": bass_db,
                "synth": synth_db
            }, output_file="karaoke_version.mp3")
            st.download_button("Download Karaoke MP3", karaoke_file, file_name="karaoke_version.mp3")

    # -------------------------------
    # 4️⃣ Extract Lyrics with Whisper
    if st.button("Extract Lyrics"):
        with st.spinner("Loading Whisper model and transcribing..."):
            model = whisper.load_model("large")
            result = model.transcribe("song.wav")  # use WAV
            lyrics = result["text"]

        st.subheader("Extracted Lyrics")
        st.text_area("Lyrics", lyrics, height=300)
        st.download_button("Download Lyrics", lyrics, file_name="lyrics.txt")
        st.info("⚠️ Lyrics may not be 100% accurate depending on accent or language.")
