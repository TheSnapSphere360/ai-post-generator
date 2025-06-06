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

# Try to open the correct spreadsheet and worksheet
try:
    sheet = sheet_client.open("TheSnapSphere360 Captions").worksheet("Captions")
except Exception as e:
    st.error(f"❌ Error opening sheet or worksheet: {e}")
    st.stop()

# Ideal hashtag counts per platform
IDEAL_HASHTAG_COUNTS = {
    "tiktok": 15,
    "instagram": 12,
    "facebook": 8,
    "twitter": 4,
    "snapchat": 5,
    "youtube": 0,  # no hashtags for YouTube Shorts
}

CTA_LINE = "🔥 New clips daily — follow for more wild moments."

def format_caption(caption_text, hashtags_list, platform):
    ideal_count = IDEAL_HASHTAG_COUNTS.get(platform, 5)
    limited_hashtags = hashtags_list[:ideal_count]
    hashtags_line = " ".join(limited_hashtags)

    parts = [caption_text.strip(), "", hashtags_line]

    if platform in ["tiktok", "instagram", "facebook"]:
        parts.append("")
        parts.append(CTA_LINE)

    return "\n".join(parts)

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
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Generate catchy, platform-optimized captions for TikTok, Instagram Reels, Facebook Reels, YouTube Shorts, Twitter/X, and Snapchat. Include niche, viral, brand, and character-specific hashtags. Return JSON with keys for each platform: caption and hashtags as lists."},
                    {"role": "user", "content": user_input}
                ]
            )
            import json
            raw_result = response.choices[0].message.content.strip()

            # Parse JSON result safely
            try:
                platforms_data = json.loads(raw_result)
            except Exception:
                st.error("⚠️ Failed to parse AI response. Make sure AI returns JSON.")
                st.text_area("Raw AI output", raw_result, height=300)
                st.stop()

            # Format captions for each platform
            formatted_captions = {}
            for platform in IDEAL_HASHTAG_COUNTS.keys():
                if platform in platforms_data:
                    cap = platforms_data[platform].get("caption", "")
                    tags = platforms_data[platform].get("hashtags", [])
                    formatted_captions[platform] = format_caption(cap, tags, platform)
                else:
                    formatted_captions[platform] = ""

            # Display captions for copy-pasting
            for platform, caption_text in formatted_captions.items():
                st.subheader(platform.capitalize())
                st.text_area(f"{platform.capitalize()} Caption", caption_text, height=150)

            # Save one row with all platform captions horizontally
            sheet.append_row([formatted_captions[p] for p in IDEAL_HASHTAG_COUNTS.keys()])

            st.success("✨ Captions saved to Google Sheets!")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
