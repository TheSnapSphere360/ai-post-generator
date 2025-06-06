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

# Google Sheet ID and worksheet name
spreadsheet_id = "1Iw6Vn3qG-gFwYZn_fwuapHOe3-vcSToMsFYQl1y_Xvw"
worksheet_name = "Captions"

# Debug: List all spreadsheets the service account can access
st.write("🔍 Sheets available to service account:")
try:
    available_sheets = sheet_client.openall()
    for s in available_sheets:
        st.write(f"📄 {s.title}")
except Exception as e:
    st.error(f"❌ Could not fetch sheets: {e}")

# Open the sheet by ID and worksheet
try:
    sheet = sheet_client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
except Exception as e:
    st.error(f"❌ Error opening sheet or worksheet: {e}")
    st.stop()

# Function to format captions per platform with spacing & ideal hashtag counts
def format_caption(platform, caption, hashtags, cta):
    # Ideal hashtag counts per platform
    hashtag_limits = {
        "tiktok": 7,
        "instagram": 7,
        "facebook": 5,
        "twitter": 3,
        "snapchat": 3,
        "youtube": 0,  # YouTube Shorts exclude hashtags and CTA
    }

    # Limit hashtags to ideal count for platform
    ideal_count = hashtag_limits.get(platform.lower(), 5)
    hashtags = hashtags.split()
    hashtags = hashtags[:ideal_count]
    hashtags_str = " ".join(hashtags)

    # Build formatted caption
    if platform.lower() == "youtube":
        # YouTube Shorts: caption only, no hashtags or CTA
        formatted = caption.strip()
    else:
        formatted = (
            caption.strip()
            + "\n\n"
            + hashtags_str
            + "\n\n"
            + cta
        )
    return formatted

# Streamlit UI
st.title("📲 AI Social Post Generator for Opus Clips")
st.markdown("Upload a clip transcript or paste a summary. Get ready-to-post content for all platforms:")

user_input = st.text_area("📝 Paste Opus Clip Transcript or Summary", height=200)

if st.button("✨ Generate Social Captions"):
    if not user_input.strip():
        st.warning("Please paste a transcript or summary first.")
    else:
        try:
            # Prompt for OpenAI
            prompt = f"""
Generate catchy, platform-optimized captions for the following platforms: TikTok, Instagram Reels, Facebook Reels, YouTube Shorts, Twitter, Snapchat.
Use ideal hashtag counts for each platform (TikTok, Instagram: 7 hashtags; Facebook: 5; Twitter and Snapchat: 3; YouTube Shorts: none).
Format each platform's output as JSON with keys: caption, hashtags, cta.
Example format:
{{
  "tiktok": {{"caption": "...", "hashtags": "...", "cta": "..."}},
  "instagram": {{"caption": "...", "hashtags": "...", "cta": "..."}},
  ...
}}

Here is the clip summary/transcript:
\"\"\"{user_input}\"\"\"
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a social media content expert."},
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse JSON from response
            import json
            content = response.choices[0].message.content.strip()
            captions_json = json.loads(content)

            # CTA line
            cta_line = "🔥 New clips daily — follow for more wild moments."

            # Format each platform caption according to rules
            output_rows = []
            platforms_order = ["tiktok", "instagram", "facebook", "twitter", "snapchat", "youtube"]

            for platform in platforms_order:
                data = captions_json.get(platform, {})
                caption = data.get("caption", "")
                hashtags = data.get("hashtags", "")
                cta = data.get("cta", cta_line)
                formatted_text = format_caption(platform, caption, hashtags, cta)
                output_rows.append(formatted_text)

            # Append to Google Sheet in one row horizontally
            sheet.append_row(output_rows)

            # Display success and the generated captions in one text area for copy/paste
            st.success("✨ Captions Ready!")

            combined_display = "\n\n---\n\n".join(
                f"{platform.capitalize()}:\n{output_rows[i]}"
                for i, platform in enumerate(platforms_order)
            )

            st.text_area("📝 Copy & Paste All Platforms", value=combined_display, height=400)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
