import os
import json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google Sheets auth with service account JSON from Streamlit secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
sheet_client = gspread.authorize(creds)

# Open your sheet by ID and worksheet name
SPREADSHEET_ID = "1Iw6Vn3qG-gFwYZn_fwuapHOe3-vcSToMsFYQl1y_Xvw"
WORKSHEET_NAME = "Captions"

try:
    sheet = sheet_client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
except Exception as e:
    st.error(f"❌ Error opening sheet or worksheet: {e}")
    st.stop()

st.title("📱 AI Social Post Generator for Opus Clips")
st.markdown("Upload a clip transcript or paste a summary. Get ready-to-post captions for all platforms.")

user_input = st.text_area("📝 Paste Opus Clip Transcript or Summary", height=250)

# Ideal hashtags counts for platforms
IDEAL_HASHTAGS = {
    "tiktok": 10,
    "instagram": 20,
    "facebook": 10,
    "twitter": 5,
    "snapchat": 5,
    "youtube": 5
}

def build_caption_block(caption, hashtags, cta):
    # Join hashtags into a single string
    hashtags_line = " ".join(hashtags)
    return f"{caption}\n\n{hashtags_line}\n\n{cta}"

def truncate_hashtags(hashtags_str, max_count):
    # Split hashtags by space and keep max_count
    tags = hashtags_str.strip().split()
    return tags[:max_count]

if st.button("✨ Generate Social Captions"):
    if not user_input.strip():
        st.warning("Please paste a transcript or summary first.")
    else:
        system_msg = (
            "You are a social media expert creating catchy captions for multiple platforms. "
            "Respond ONLY with a JSON object with keys: tiktok, instagram, facebook, twitter, snapchat, youtube. "
            "Each value should be an object with these string fields: caption, hashtags, cta. "
            "Example:\n"
            '{\n'
            '  "tiktok": {"caption": "text", "hashtags": "#tag1 #tag2", "cta": "🔥 New clips daily — follow for more wild moments."},\n'
            '  "instagram": {...},\n'
            '  ...\n'
            '}\n'
            "No explanations or markdown, only JSON."
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_input}
                ]
            )
            raw_content = response.choices[0].message.content.strip()
            st.text_area("Raw OpenAI Response (for debugging)", value=raw_content, height=250)

            data = json.loads(raw_content)

            cta_line = "🔥 New clips daily — follow for more wild moments."

            row = []
            # Order of platforms and append to row for horizontal insert
            platforms_order = ["tiktok", "instagram", "facebook", "twitter", "snapchat", "youtube"]
            for platform in platforms_order:
                if platform in data:
                    cap = data[platform].get("caption", "").strip()
                    tags_str = data[platform].get("hashtags", "").strip()
                    cta = data[platform].get("cta", "").strip()
                    # Use ideal hashtags count, truncate if needed
                    tags_list = truncate_hashtags(tags_str, IDEAL_HASHTAGS.get(platform, 10))
                    # Build final block with proper spacing
                    block = build_caption_block(cap, tags_list, cta)
                    row.append(block)
                else:
                    row.append("")  # blank for missing platform

            # Append new row horizontally
            sheet.append_row(row)
            st.success("✅ Captions generated and saved to Google Sheets!")

            # Show generated captions nicely
            st.text_area("🎉 Captions Output (copy from here)", value="\n\n---\n\n".join(row), height=300)

        except json.JSONDecodeError as jde:
            st.error(f"JSON parsing error: {jde}")
            st.error("Raw response was:")
            st.code(raw_content)
        except Exception as e:
            st.error(f"Error generating captions: {e}")
