import os
import re
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

# Debug: List all spreadsheets the service account can access
st.write("\U0001F50D Sheets available to service account:")
try:
    available_sheets = sheet_client.openall()
    for s in available_sheets:
        st.write(f"\U0001F4C4 {s.title}")
except Exception as e:
    st.error(f"❌ Could not fetch sheets: {e}")

# Try to open the correct spreadsheet and worksheet
try:
    sheet = sheet_client.open("TheSnapSphere360").worksheet("Captions")
except Exception as e:
    st.error(f"❌ Error opening sheet 'TheSnapSphere360' or worksheet 'Captions': {e}")
    st.stop()

# Streamlit UI
st.title("📲 AI Social Post Generator for Opus Clips")
st.markdown("Upload a clip transcript or paste a summary. Get ready-to-post content for all platforms:")

user_input = st.text_area("📝 Paste Opus Clip Transcript or Summary", height=200)

platforms = ["TikTok", "Instagram", "Facebook", "Twitter", "YouTube Shorts", "Snapchat"]

if st.button("✨ Generate Social Captions"):
    if not user_input.strip():
        st.warning("Please paste a transcript or summary first.")
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Generate catchy, platform-optimized captions for TikTok, Instagram Reels, Facebook Reels, YouTube Shorts, Twitter/X, and Snapchat. Add niche, viral, brand, and character-specific hashtags. Each platform's output should follow this format: \n\n**Platform**:\nCaption line\n\nHashtags line\n"},
                    {"role": "user", "content": f"{user_input}"}
                ]
            )

            result = response.choices[0].message.content.strip()
            st.success("✨ Captions Ready!")
            st.text_area("📤 Copy & Paste", value=result, height=400)

            row_data = []

            for platform in platforms:
                match = re.search(rf"\*\*{platform}\*\*:\s*(.*?)(?=\n\*\*|\Z)", result, re.DOTALL)
                if match:
                    block = match.group(1).strip()

                    # Split caption and hashtags
                    parts = [part.strip() for part in block.split("\n\n") if part.strip()]
                    caption = parts[0] if len(parts) > 0 else ""
                    hashtags = parts[1] if len(parts) > 1 else ""

                    if platform in ["TikTok", "Instagram", "Facebook"]:
                        formatted = f"{caption}\n\n{hashtags}\n\n\ud83d\udd25 New clips daily — follow for more wild moments."
                    else:
                        formatted = f"{caption}\n\n{hashtags}"

                    row_data.append(formatted)
                else:
                    row_data.append("")  # if platform missing

            sheet.append_row(row_data)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
