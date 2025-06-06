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
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
sheet_client = gspread.authorize(creds)

# Debug: List all spreadsheets the service account can access
st.write("🔍 Sheets available to service account:")
try:
    available_sheets = sheet_client.openall()
    for s in available_sheets:
        st.write(f"📄 {s.title}")
except Exception as e:
    st.error(f"❌ Could not fetch sheets: {e}")

# Open the correct spreadsheet and worksheet
try:
    sheet = sheet_client.open("TheSnapSphere360").worksheet("Captions")
except Exception as e:
    st.error(f"❌ Error opening sheet 'TheSnapSphere360' or worksheet 'Captions': {e}")
    st.stop()

# Streamlit UI
st.title("📲 AI Social Post Generator for Opus Clips")
st.markdown("Upload a clip transcript or paste a summary. Get ready-to-post content for all platforms:")

user_input = st.text_area("📝 Paste Opus Clip Transcript or Summary", height=200)

if st.button("✨ Generate Social Captions"):
    if not user_input.strip():
        st.warning("Please paste a transcript or summary first.")
    else:
        try:
            # Call OpenAI chat completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate catchy, platform-optimized captions for TikTok, Instagram Reels, Facebook Reels, "
                            "YouTube Shorts, Twitter/X, and Snapchat. Add niche, viral, brand, and character-specific hashtags. "
                            "Format each platform's output as:\n\n"
                            "[Caption]\n\n"
                            "[Hashtags (all in one line)]\n\n"
                            "🔥 New clips daily — follow for more wild moments.\n\n"
                            "YouTube Shorts should exclude hashtags and the final CTA line.\n"
                        )
                    },
                    {"role": "user", "content": user_input}
                ]
            )

            result = response.choices[0].message.content.strip()
            st.success("✨ Captions Ready!")
            st.text_area("📝 Copy & Paste All Platforms", value=result, height=350)

            # Parse result by platform and save horizontally as one row
            # Assuming result format:
            # [Caption]
            #
            # [Hashtags]
            #
            # CTA line (except YouTube Shorts)
            #
            # (then next platform...)

            platforms = ["TikTok", "Instagram", "Facebook", "YouTube Shorts", "Twitter", "Snapchat"]

            # Split result by double newlines between platforms (heuristic)
            sections = [sec.strip() for sec in result.split("\n\n\n") if sec.strip()]

            # Prepare a row with one cell per platform
            row = []
            for i, sec in enumerate(sections):
                # Replace triple newlines inside sections by double newlines for neatness
                cell_text = sec.replace("\n\n\n", "\n\n")
                row.append(cell_text)

            # Pad row if fewer than platforms detected
            while len(row) < len(platforms):
                row.append("")

            # Append row horizontally
            sheet.append_row(row)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
