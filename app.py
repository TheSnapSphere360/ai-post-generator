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

# Debug: List all spreadsheets the service account can access
st.write("🔍 Sheets available to service account:")
try:
    available_sheets = sheet_client.openall()
    for s in available_sheets:
        st.write(f"📄 {s.title}")
except Exception as e:
    st.error(f"❌ Could not fetch sheets: {e}")

# Try to open the correct spreadsheet and worksheet
try:
    sheet = sheet_client.open("TheSnapSphere360").sheet1
except Exception as e:
    st.error(f"❌ Error opening sheet 'TheSnapSphere360': {e}")
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
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": (
                        "You are a social media expert. Generate captions for TikTok, Instagram Reels, Facebook Reels, Twitter/X, and Snapchat."
                        " Use this exact structure for each platform's output (no exceptions):\n"
                        "[Caption line]\n\n[Hashtag group: 2-3 per line, total 6-10] \n\nFinal line: '🔥 New clips daily — follow for more wild moments.'\n"
                        "Do NOT prefix platform names. Just return five captions in a list, one per platform, separated by a newline."
                    )},
                    {"role": "user", "content": f"{user_input}"}
                ]
            )

            result = response.choices[0].message.content.strip()
            st.success("✨ Captions Ready!")
            st.text_area("📤 Copy & Paste", value=result, height=300)

            # Split captions by platform and format as horizontal row
            captions = [block.strip() for block in result.split("\n\n\n") if block.strip()]
            sheet.append_row(captions)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
