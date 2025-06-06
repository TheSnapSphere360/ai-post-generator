import os
import json
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
sheet_client = gspread.authorize(creds)

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

IDEAL_HASHTAGS = {
    "tiktok": 7,
    "instagram": 10,
    "facebook": 5,
    "twitter": 4,
    "snapchat": 4,
    "youtube": 5
}

CTA_LINE = "🔥 New clips daily — follow for more wild moments."
CTA_PLATFORMS = {"tiktok", "instagram", "facebook"}

def remove_hashtags_from_caption(caption, hashtags_str):
    # Extract hashtags from string
    hashtags = set(re.findall(r"#\w+", hashtags_str))
    # Remove hashtags from caption (case-insensitive)
    for tag in hashtags:
        caption = re.sub(re.escape(tag), "", caption, flags=re.IGNORECASE)
    # Clean extra spaces
    caption = re.sub(r"\s{2,}", " ", caption).strip()
    return caption

def build_caption_block(caption, hashtags, cta="", include_cta=True):
    hashtags_line = " ".join(hashtags).strip()
    parts = []
    if caption:
        parts.append(caption.strip())
    if hashtags_line:
        parts.append(hashtags_line)
    if include_cta and cta:
        parts.append(cta.strip())
    return "\n\n".join(parts)

def truncate_hashtags(hashtags_str, max_count):
    tags = hashtags_str.strip().split()
    return tags[:max_count]

if st.button("✨ Generate Social Captions"):
    if not user_input.strip():
        st.warning("Please paste a transcript or summary first.")
    else:
        system_msg = (
            "You are a social media expert creating catchy captions for multiple platforms. "
            "Respond ONLY with a JSON object with keys: tiktok, instagram, facebook, twitter, snapchat, youtube. "
            "Each value should be an object with string fields: caption, hashtags, cta. "
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
            data = json.loads(raw_content)

            row = []
            platforms_order = ["tiktok", "instagram", "facebook", "twitter", "snapchat", "youtube"]
            for platform in platforms_order:
                if platform in data:
                    cap = data[platform].get("caption", "")
                    tags_str = data[platform].get("hashtags", "")
                    cta = data[platform].get("cta", CTA_LINE)

                    # Remove hashtags from caption so no duplicates
                    cap_clean = remove_hashtags_from_caption(cap, tags_str)

                    tags_list = truncate_hashtags(tags_str, IDEAL_HASHTAGS.get(platform, 5))

                    include_cta = platform in CTA_PLATFORMS

                    block = build_caption_block(cap_clean, tags_list, cta if include_cta else "", include_cta)
                    row.append(block)
                else:
                    row.append("")

            sheet.append_row(row)
            st.success("✅ Captions generated and saved to Google Sheets!")

            st.text_area("🎉 Captions Output (copy from here)", value="\n\n---\n\n".join(row), height=300)

        except json.JSONDecodeError as jde:
            st.error(f"JSON parsing error: {jde}")
            st.error("Raw response was:")
            st.code(raw_content)
        except Exception as e:
            st.error(f"Error generating captions: {e}")
