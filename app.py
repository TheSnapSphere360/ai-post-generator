import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Load the OpenAI key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# UI layout
st.title("📲 AI Social Post Generator for Opus Clips")
st.markdown("Upload a clip transcript or paste a summary. Get ready-to-post content for all platforms:")

user_input = st.text_area("📝 Paste Opus Clip Transcript or Summary", height=200)

if st.button("✨ Generate Social Captions"):
    if not user_input.strip():
        st.warning("Please paste a transcript or summary first.")
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You generate short, platform-optimized social captions. Focus on humor, clarity, and platform tone."},
                    {"role": "user", "content": f"Create 1 TikTok caption, 1 YouTube Shorts title, and 1 Twitter post based on this clip:\n\n{user_input}"}
                ]
            )
            result = response.choices[0].message.content.strip()
            st.success("✨ Captions Ready!")
            st.text_area("📤 Copy & Paste", value=result, height=200)
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
