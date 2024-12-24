"""
Streamlit application for YouTube Transcript scrapping with a minimalist dark theme
"""

import streamlit as st
from pytube import YouTube, Channel
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    YouTubeRequestFailed,
    VideoUnavailable,
    InvalidVideoId,
    TooManyRequests,
    TranscriptsDisabled,
    NoTranscriptAvailable,
    NotTranslatable,
    TranslationLanguageNotAvailable,
    CookiePathInvalid,
    CookiesInvalid,
    FailedToCreateConsentCookie,
    NoTranscriptFound,
)
import scrapetube
import os
import re
import base64
from pathlib import Path
import pickle


def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/webp;base64,{encoded_string});
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def get_transcript_text(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([item["text"] for item in transcript])


def remove_timestamps(srt_text):
    timestamp_pattern = re.compile(
        r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}"
    )
    lines = srt_text.split("\n")
    filtered_lines = [line for line in lines if not timestamp_pattern.match(line)]
    return "\n".join(filtered_lines)


def download_transcript(video_id, output_dir):
    try:
        transcript = get_transcript_text(video_id)
        if transcript:
            cleaned_text = remove_timestamps(transcript)

            with open(
                os.path.join(output_dir, f"{video_id}.txt"), "w", encoding="utf-8"
            ) as file:
                file.write(cleaned_text)
            return True
        else:
            print(f"No English transcript found for video ID {video_id}")
            return False
    except Exception as e:
        print(f"Failed to download transcript for video ID {video_id}: {e}")
        return False


def concatenate_transcripts(output_dir, final_file):
    with open(final_file, "w", encoding="utf-8") as f_out:
        for filename in os.listdir(output_dir):
            if filename.endswith(".txt"):
                with open(
                    os.path.join(output_dir, filename), "r", encoding="utf-8"
                ) as f_in:
                    f_out.write(f_in.read() + "\n\n")


def get_all_video_ids(channel_url):
    videos = scrapetube.get_channel(channel_url=channel_url)
    video_ids = [video["videoId"] for video in videos]
    return video_ids


def clear_transcript_folder(folder_path):
    """Delete all files in the specified folder."""
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                st.error(f"Error deleting {filename}: {e}")
        st.success("All transcript files cleared!")
    else:
        st.warning("Transcript folder does not exist")


def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


# Google Drive API setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_google_drive_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)


def upload_to_drive(file_path, folder_id=None):
    """Upload a file to Google Drive
    Args:
        file_path: Path to the file to upload
        folder_id: Optional Google Drive folder ID to upload to
    Returns:
        File ID if successful, None otherwise
    """
    try:
        service = get_google_drive_service()
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id] if folder_id else []
        }
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return file.get('id')
    except Exception as e:
        st.error(f"Error uploading to Google Drive: {str(e)}")
        return None


# Get background image
background_image = get_base64_encoded_image("assets/youtube_bg.webp")

# Custom CSS for dark theme and minimalist design
st.set_page_config(
    page_title="YouTube Transcripts",
    page_icon="🎥",
    layout="centered"
)

add_bg_from_local('assets/youtube_bg.webp')

st.markdown(f'''
    <style>
        /* Base theme */
        .stApp {{
            background: rgba(13, 17, 23, 0.85);  /* GitHub Dark theme color with brownish hue */
        }}
        
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: url("data:image/webp;base64,{background_image}");
            background-size: cover;
            background-position: center;
            opacity: 0.3;
            z-index: -1;
        }}
    </style>
''', unsafe_allow_html=True)

# Custom CSS
st.markdown("""
    <style>
        /* Reset Streamlit styles */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Anton&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
            letter-spacing: -0.02em;
        }
        
        /* Make all backgrounds transparent */
        .stApp, 
        .main,
        .stApp > header,
        section[data-testid="stSidebar"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        .main .block-container,
        div[data-testid="stStatusWidget"],
        body {
            background: transparent !important;
        }

        /* Background image */
        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: url('assets/youtube_bg.webp');
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover;
            opacity: 0.3;
            z-index: -1;
        }

        /* Dark overlay */
        body::after {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.85);
            z-index: -1;
        }

        .stTextInput > div > div > input {
            background-color: #1a1a1a;  /* Dark brownish-gray */
            color: #E2E8F0;
            border: 1px solid #1E293B;
            border-radius: 6px;
            padding: 15px;
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
            font-weight: 300;
            letter-spacing: -0.02em;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #2D3F63;
            box-shadow: 0 0 0 1px #2D3F63;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #64748B;
            font-weight: 300;
        }
        
        .stButton {
            text-align: center;
            margin-top: 2.5rem;
            margin-bottom: 2.5rem;
        }
        
        .stButton > button {
            background-color: rgba(28, 31, 46, 1);
            color: #94A3B8;
            border: 0.2px solid #FF0000;
            padding: 0.5rem 1rem;
            transition: all 0.2s ease;
            box-shadow: none;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.4em;
            text-transform: uppercase;
            font-weight: 300;
        }

        .stButton > button:hover {
            background-color: #FFFFFF;
            color: rgba(28, 31, 46, 1);
            border-color: #FFFFFF;
            transform: translateY(-1px);
        }

        .stButton > button:active {
            transform: translateY(1px);
        }
        
        .title-container {
            text-align: center;
            margin-bottom: 1rem;
            margin-top: 5rem;
        }
        
        .youtube-title {
            font-family: 'Anton', Impact, sans-serif;
            font-size: 5.5rem;
            font-weight: 900;
            color: transparent;
            -webkit-text-stroke: 0.25px #FF0000;
            text-shadow: none;
            margin: 0;
            line-height: 0.85;
            letter-spacing: 0.02em;
            padding: 0;
            text-transform: uppercase;
        }
        
        .youtube-title::before {
            display: none;
        }
        
        .subtitle {
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
            font-size: 1.2rem;
            font-weight: 400;
            color: #94A3B8;
            margin-top: 0.5rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
        }
        
        h1 {
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
            font-weight: 500;
            color: #F8FAFC;
            text-align: center;
            letter-spacing: -0.03em;
            margin-bottom: 2rem;
        }
        
        h2, h3 {
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
            font-weight: 400;
            color: #E2E8F0;
            text-align: center;
            letter-spacing: -0.02em;
        }
        
        .centered-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
        }
        
        .centered-container p {
            color: #64748B;
            font-weight: 300;
            letter-spacing: -0.01em;
            margin-bottom: 2rem;
        }
        
        .status-text {
            color: #64748B;
            font-size: 14px;
            font-weight: 300;
            margin-top: 20px;
            letter-spacing: -0.01em;
        }
        
        .progress-container {
            margin: 20px 0;
            padding: 10px;
            background-color: #0F172A;
            border-radius: 6px;
            border: 1px solid #1E293B;
        }
        
        /* Style for success messages */
        .stSuccess {
            background-color: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.2);
            color: #10B981;
            padding: 16px;
            border-radius: 6px;
            font-weight: 400;
            text-align: center;
        }
        
        /* Style for error messages */
        .stError {
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            color: #EF4444;
            padding: 16px;
            border-radius: 6px;
            font-weight: 400;
        }
        
        /* Success message styling */
        div[data-testid="stSuccessMessage"] {
            text-align: center;
        }
        
        .stSuccess > div > div {
            display: flex;
            justify-content: center;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)


def main():
    # Center align the container
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
            <div class='title-container'>
                <div class='youtube-title'>YouTube</div>
                <div class='subtitle'>Channel Transcripts</div>
            </div>
        """, unsafe_allow_html=True)
        
        channel_url = st.text_input("", placeholder="youtube.com/@channel")
        
        output_dir = "transcripts"
        
        final_file = st.text_input("", placeholder="Name new file")
        
        if st.button("Download"):
            if not channel_url: 
                st.error("Please enter a channel URL")
                return
            
            else:
                if not final_file:
                    final_file = "combined_transcripts.txt"
                else:
                    final_file = final_file + ".txt"

                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                clear_transcript_folder(output_dir)
                
                with st.spinner("Fetching video list..."):
                    video_ids = get_all_video_ids(channel_url)
                    total_videos = len(video_ids)
                
                st.markdown(f"""
                    <div class='status-text'>
                        Found {total_videos} videos to process
                    </div>
                """, unsafe_allow_html=True)

                progress_bar = st.progress(0)
                
                for i, video_id in enumerate(video_ids, 1):
                    progress = int((i / total_videos) * 100)
                    progress_bar.progress(progress)
                    
                    st.markdown(f"""
                        <div class='status-text'>
                            Processing video {i} of {total_videos}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    download_transcript(video_id, output_dir)

                st.markdown("""
                    <div class='status-text'>
                        Combining transcripts...
                    </div>
                """, unsafe_allow_html=True)
                
                concatenate_transcripts(output_dir, final_file)
                
                st.success(f"✨ All transcripts combined into {final_file}")
                
                # Add download button
                with open(final_file, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="Download Combined Transcript",
                        data=f.read(),
                        file_name=final_file,
                        mime="text/plain"
                    )
                    
                # Add Google Drive upload option
                if st.checkbox("Upload to Google Drive"):
                    folder_id = "1QpJxFsWU6INW0aLQdDrHVZ9qZ6QQf0zw"  # Your folder ID
                    
                    if st.button("Upload to YouTube Transcripts Folder"):
                        if os.path.exists(final_file):
                            with st.spinner("Uploading to Google Drive..."):
                                file_id = upload_to_drive(final_file, folder_id)
                                if file_id:
                                    st.success(f"✅ File uploaded successfully to YouTube Transcripts folder!")
                                    drive_link = f"https://drive.google.com/file/d/{file_id}/view"
                                    st.markdown(f"[View file in Google Drive]({drive_link})")


if __name__ == "__main__":
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    main()
