import pandas as pd
import json
import re
from groq import Groq
from googleapiclient.discovery import build

# ---------------- CONFIG ----------------
YOUTUBE_API_KEY = "***REMOVED***"
GROQ_API_KEY = "REMOVED"

KEYWORDS = ["Duolingo AI layoffs"]
TARGET_COMMENTS = 200

MAX_VIDEOS = 10
MAX_COMMENTS_PER_VIDEO = 100

POSTS_CSV = "posts.csv"
CLASSIFIED_CSV = "classified_posts.csv"
# ----------------------------------------

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a social scientist analyzing public reactions to Duolingo’s AI-related layoffs.

Classify the text into ONE category:
- fear of precarity
- ethical concerns
- quality concerns

Also classify tone:
- Critical
- Neutral
- Supportive

Return ONLY valid JSON:
{"category": "...", "tone": "..."}
"""

# ---------- helpers ----------

def clean_text(text):
    text = re.sub(r"<.*?>", "", text)          # remove HTML
    text = re.sub(r"http\S+", "", text)        # remove links
    text = text.strip()
    return text

def is_valid_comment(text):
    if len(text) < 20:
        return False
    if "http" in text.lower():
        return False
    return True

# ---------- STEP 1: FETCH COMMENTS ----------

posts = []

print("Fetching YouTube comments...")

for keyword in KEYWORDS:
    search = youtube.search().list(
        q=keyword,
        part="id",
        type="video",
        maxResults=MAX_VIDEOS
    ).execute()

    for item in search.get("items", []):
        video_id = item["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            comments = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=MAX_COMMENTS_PER_VIDEO
            ).execute()

            for c in comments.get("items", []):
                raw = c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                text = clean_text(raw)

                if is_valid_comment(text):
                    posts.append({
                        "text": text,
                        "source": video_url
                    })

                if len(posts) >= TARGET_COMMENTS:
                    break

        except Exception:
            continue

        if len(posts) >= TARGET_COMMENTS:
            break

    if len(posts) >= TARGET_COMMENTS:
        break

df_posts = pd.DataFrame(posts)
df_posts.to_csv(POSTS_CSV, index=False, encoding="utf-8")
print(f"Saved {len(df_posts)} cleaned posts to {POSTS_CSV}")

# ---------- STEP 2: CLASSIFY ----------

results = []

print("Classifying with Groq...")

for i, row in df_posts.iterrows():
    text = row["text"]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ]
        )

        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)

        category = parsed["category"]
        tone = parsed["tone"]

    except Exception:
        category = "Unknown"
        tone = "Unknown"

    results.append({
        "text": text,
        "source": row["source"],
        "category": category,
        "tone": tone
    })

    if (i + 1) % 20 == 0:
        print(f"Classified {i + 1}/{len(df_posts)}")

df_final = pd.DataFrame(results)
df_final.to_csv(CLASSIFIED_CSV, index=False, encoding="utf-8")

print("Done. Saved classified_posts.csv")
