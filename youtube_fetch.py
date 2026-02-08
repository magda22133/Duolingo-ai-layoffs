import os
import pandas as pd
from googleapiclient.discovery import build

# --- CONFIG ---
YOUTUBE_API_KEY = "AIzaSyCI1fmx69gFO-veohZc2PqCS0gAyqAt6Ic"  # <-- put your key here
KEYWORDS = ["Duolingo AI layoffs"]        # <-- list your keywords here
MAX_VIDEOS = 5                            # how many videos per keyword
MAX_COMMENTS = 50                         # comments per video
OUTPUT_CSV = "posts.csv"

# --- Initialize YouTube API ---
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

all_posts = []

for keyword in KEYWORDS:
    # Search videos for the keyword
    search_request = youtube.search().list(
        q=keyword,
        part="id",
        type="video",
        maxResults=MAX_VIDEOS
    )
    search_response = search_request.execute()

    for video in search_response.get('items', []):
        video_id = video['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Get top comments
        try:
            comment_request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=MAX_COMMENTS
            )
            comment_response = comment_request.execute()

            for item in comment_response.get('items', []):
                comment_text = item['snippet']['topLevelComment']['snippet']['textDisplay']
                all_posts.append({
                    "text": comment_text,
                    "source_type": "youtube_comment",
                    "source_link": video_url
                })
        except Exception as e:
            print(f"Error fetching comments for {video_url}: {e}")

# --- Save to CSV ---
df = pd.DataFrame(all_posts)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
print(f"Saved {len(all_posts)} posts to {OUTPUT_CSV}")
