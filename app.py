import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Authenticate with Google Sheets using Streamlit secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
sheet_client = gspread.authorize(creds)

# Open target Google Sheet and worksheet
try:
    sheet = sheet_client.open("TheSnapSphere360").worksheet("Captions")
except Exception as e:
    st.error(f"❌ Error opening Google Sheet or worksheet: {e}")
    st.stop()

# UI
st.title("📲 AI Social Post Generator for Opus Clips")
st.markdown("Upload a clip transcript or paste a summary. Get ready-to-post content for all platforms:")

user_input = st.text_area("📝 Paste Opus Clip Transcript or Summary", height=200)

if st.button("✨ Generate Social Captions"):
    if not user_input.strip():
        st.warning("Please paste a transcript or summary first.")
    else:
        try:
            # Send request to OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": (
                        "Generate platform-specific captions (TikTok, Instagram, Facebook, Twitter, Snapchat, YouTube Shorts) for a comedy podcast clip. "
                        "Use the following structure for each caption:\n\n"
                        "[Caption line]\n\n[Hashtags line 1]\n[Hashtags line 2]\n[Hashtags line 3]\n\n🔥 New clips daily — follow for more wild moments.\n\n"
                        "- ONLY YouTube Shorts should skip hashtags and the final line.\n"
                        "- Each caption should be standalone and funny.\n"
                        "- DO NOT include platform names in the output."
                    )},
                    {"role": "user", "content": user_input}
                ]
            )

            full_output = response.choices[0].message.content.strip()

            # Parse captions by splitting double newlines (6 captions expected)
            sections = [s.strip() for s in full_output.split("\n\n\n") if s.strip()]
            while len(sections) < 6:
                sections.append("")

            st.success("✨ Captions Ready!")
            st.text_area("📤 Copy & Paste All", value=full_output, height=400)

            # Append to sheet as one row (each platform in its own column)
            sheet.append_row(sections)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
