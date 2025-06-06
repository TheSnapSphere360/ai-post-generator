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

# Open spreadsheet and worksheet
sheet = sheet_client.open("TheSnapSphere360").worksheet("Captions")

# Streamlit UI
st.title("📲 AI Social Post Generator for Opus Clips")
st.markdown("Upload a clip transcript or paste a summary. Get ready-to-post content for all platforms:")

user_input = st.text_area("📝 Paste Opus Clip Transcript or Summary", height=200)

if st.button("✨ Generate Social Captions"):
    if not user_input.strip():
        st.warning("Please paste a transcript or summary first.")
    else:
        try:
            # Call OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate short-form video captions for the following platforms, each labeled clearly: "
                            "TikTok, Instagram, Facebook, YouTube Shorts, Twitter, and Snapchat. Format each like this:\n\n"
                            "**TikTok**:\n[Caption]\n\n**Instagram**:\n[Caption] ..."
                        )
                    },
                    {"role": "user", "content": user_input}
                ]
            )

            result = response.choices[0].message.content.strip()
            st.success("✨ Captions Ready!")
            st.text_area("📤 Copy & Paste", value=result, height=400)

            # Parse and extract captions per platform
            platforms = ["TikTok", "Instagram", "Facebook", "YouTube Shorts", "Twitter", "Snapchat"]
            row_data = []
            for platform in platforms:
                if f"**{platform}**:" in result:
                    part = result.split(f"**{platform}**:")[1]
                    next_parts = [result.split(f"**{p}**:")[1] for p in platforms if f"**{p}**:" in result and result.find(f"**{p}**:") > result.find(f"**{platform}**:")]
                    end_index = result.find(next_parts[0]) if next_parts else None
                    caption = part[:end_index].strip() if end_index else part.strip()
                    row_data.append(caption)
                else:
                    row_data.append("")

            # Save to sheet horizontally
            sheet.append_row(row_data)

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
