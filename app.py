import streamlit as st
import openai
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AI Clip Publisher", layout="centered")
st.title("📲 AI Social Post Generator for Opus Clips")
st.markdown("Upload a clip transcript or paste a summary. Get ready-to-post content for all platforms:")

user_input = st.text_area("📝 Paste Opus Clip Transcript or Summary", height=200)

if st.button("✨ Generate Social Captions") and user_input:
    with st.spinner("Generating content..."):
        prompt = f"""
You're an expert social media manager. For the following video clip summary, generate:
1. A punchy hook (under 10 words)
2. TikTok caption (max 150 characters)
3. Instagram caption (max 2200 characters)
4. 5 optimized hashtags per platform
5. Best time of day and day of week to post

Be platform-aware. Avoid any banned or restricted keywords. Keep it fun, niche-relevant, and scroll-stopping.

Clip Summary:
\"\"\"{user_input}\"\"\"
"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that formats content for TikTok, Instagram, Facebook, and Twitter."},
                    {"role": "user", "content": prompt}
                ]
            )
            result = response["choices"][0]["message"]["content"]
            st.success("Content ready!")
            st.markdown("### 📤 AI Platform Content")
            st.markdown(result)
        except Exception as e:
            st.error(f"⚠️ Error: {e}")

st.markdown("---")
st.caption("Built by TheSnapSphere360 🧠")
