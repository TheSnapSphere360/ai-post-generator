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

# Authenticate with Google Sheets using secrets from Streamlit
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
sheet_client = gspread.authorize(creds)

# Try to open target sheet and worksheet
try:
    sheet = sheet_client.open("TheSnapSphere360 Captions").worksheet("Captions")
except Exception as e:
    st.error(f"❌ Error opening sheet or worksheet: {e}")
    st.stop()

# Format caption helper
def format_caption(caption, hashtags_list, platform):
    hashtag_limits = {
        "tiktok": 10,
        "instagram": 15,
        "facebook": 3,
        "youtube_shorts": 5,
        "twitter": 2,
        "snapchat": 3
    }
    limit = hashtag_limits.get(platform.lower(), 10)
    limited_hashtags = hashtags_list[:limit]
    hashtags_line = " ".join(f"#{tag}" for tag in limited_hashtags)
    
    cta_line = "🔥 New clips daily — follow for more wild moments."
    
    if platform.lower() in ["tiktok", "instagram", "facebook"]:
        formatted = f"{caption.strip()}\n\n{hashtags_line}\n\n{cta_line}"
    else:
        # For YouTube Shorts, Twitter, Snapchat no CTA line
        formatted = f"{caption.strip()}\n\n{hashtags_line}"
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
            # Ask OpenAI to generate captions + hashtags for each platform in a JSON string format
            prompt = (
                "Generate catchy captions and hashtags for these platforms: TikTok, Instagram Reels, Facebook Reels, "
                "YouTube Shorts, Twitter/X, Snapchat. Provide output as JSON with keys as platform names, each containing "
                "a 'caption' string and a list 'hashtags'. Example:\n"
                '{ "tiktok": {"caption": "...", "hashtags": ["tag1","tag2"]}, "instagram": {...}, ... }\n\n'
                f"Content:\n{user_input}"
            )
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You generate social media captions with hashtags as requested."},
                    {"role": "user", "content": prompt}
                ]
            )
            json_text = response.choices[0].message.content.strip()
            
            import json
            data = json.loads(json_text)

            # Format each platform using our helper
            formatted_captions = {}
            for platform, details in data.items():
                caption = details.get("caption", "")
                hashtags = details.get("hashtags", [])
                formatted_captions[platform] = format_caption(caption, hashtags, platform)

            # Display and save horizontally in sheet (columns for each platform)
            st.success("✨ Captions Ready!")
            for platform, text in formatted_captions.items():
                st.subheader(platform.capitalize())
                st.text_area(f"📤 Copy & Paste for {platform.capitalize()}", value=text, height=180)

            # Save one row with platforms ordered (customize as needed)
            platforms_order = ["tiktok", "instagram", "facebook", "youtube_shorts", "twitter", "snapchat"]
            row_to_append = [formatted_captions.get(p, "") for p in platforms_order]
            sheet.append_row(row_to_append)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
