import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

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
    sheet = sheet_client.open("TheSnapSphere360").worksheet("Captions")
except Exception as e:
    st.error(f"❌ Error opening sheet 'TheSnapSphere360' or worksheet 'Captions': {e}")
    st.stop()

# Streamlit UI
st.title("📲 AI Social Post Generator for Opus Clips")
st.markdown("Upload a clip transcript or paste a summary. Get ready-to-post content for all platforms:")

user_input = st.text_area("📝 Paste Opus Clip Transcript or Summary", height=200)

def format_caption_platform(platform, caption, hashtags):
    """Format caption text per platform rules"""
    if platform in ["TikTok", "Instagram", "Facebook"]:
        # Caption + newline + hashtags + newline + CTA
        return f"{caption}\n\n{hashtags}\n\n🔥 New clips daily — follow for more wild moments."
    elif platform in ["Snapchat", "Twitter"]:
        # Caption + newline + hashtags only
        return f"{caption}\n\n{hashtags}"
    elif platform == "YouTube Shorts":
        # Caption only, no hashtags, no CTA
        return caption
    else:
        # Default fallback, just caption
        return caption

def parse_response_to_platforms(text):
    """
    Parse the OpenAI response into a dict of platforms to formatted captions.
    This expects the response to separate platforms with clear labels like:
    TikTok:
    [caption]
    Hashtags:
    [hashtags]
    etc.
    Adjust regexes as needed based on actual response format.
    """
    platforms = ["TikTok", "Instagram", "Facebook", "YouTube Shorts", "Twitter", "Snapchat"]

    # Split by platform name with optional colon
    platform_blocks = re.split(r'\n?(TikTok|Instagram|Facebook|YouTube Shorts|Twitter|Snapchat):?\n', text, flags=re.IGNORECASE)

    # The split results in a list where platforms are in odd indices and content in even indices
    parsed = {}
    for i in range(1, len(platform_blocks), 2):
        platform = platform_blocks[i].strip()
        content = platform_blocks[i+1].strip()

        # Extract caption and hashtags from content
        # Assuming hashtags come after a blank line or line with "Hashtags:" keyword
        # Try to split on "\n\n" or "Hashtags:" keyword
        if "Hashtags:" in content:
            parts = content.split("Hashtags:")
            caption = parts[0].strip()
            hashtags = parts[1].strip()
        else:
            # Fallback: split by two newlines
            parts = content.split("\n\n", 1)
            caption = parts[0].strip()
            hashtags = parts[1].strip() if len(parts) > 1 else ""

        # Format per platform rules
        formatted = format_caption_platform(platform, caption, hashtags)
        parsed[platform] = formatted

    return parsed

if st.button("✨ Generate Social Captions"):
    if not user_input.strip():
        st.warning("Please paste a transcript or summary first.")
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate catchy, platform-optimized captions for TikTok, Instagram, Facebook, YouTube Shorts, Twitter, and Snapchat. "
                            "Format output clearly with each platform name followed by caption and hashtags. "
                            "Use this exact platform order: TikTok, Instagram, Facebook, YouTube Shorts, Twitter, Snapchat. "
                            "For TikTok, Instagram, Facebook, include final line: '🔥 New clips daily — follow for more wild moments.' "
                            "For YouTube Shorts exclude hashtags and final line. "
                            "For Twitter and Snapchat, include caption and hashtags but no final line."
                        ),
                    },
                    {"role": "user", "content": f"{user_input}"},
                ],
            )

            result_text = response.choices[0].message.content.strip()
            st.success("✨ Captions Ready!")

            # Parse result by platform and format per your rules
            parsed_captions = parse_response_to_platforms(result_text)

            # Display all in one big text area for easy copy
            combined_text = ""
            for platform in ["TikTok", "Instagram", "Facebook", "YouTube Shorts", "Twitter", "Snapchat"]:
                caption_text = parsed_captions.get(platform, "")
                combined_text += caption_text + "\n\n---\n\n"

            st.text_area("📝 Copy & Paste All Platforms", value=combined_text.strip(), height=400)

            # Save one row with each platform's caption in separate columns
            row = [
                parsed_captions.get("TikTok", ""),
                parsed_captions.get("Instagram", ""),
                parsed_captions.get("Facebook", ""),
                parsed_captions.get("YouTube Shorts", ""),
                parsed_captions.get("Twitter", ""),
                parsed_captions.get("Snapchat", ""),
            ]
            sheet.append_row(row)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
