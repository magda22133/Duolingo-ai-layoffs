import pandas as pd
import json
import re
from groq import Groq

# --- Initialize client ---
client = Groq(api_key= os.environ.get("GROQ_API_KEY")  # <-- put your actual key

# --- System prompt for classification ---
SYSTEM_PROMPT = """
You are a social scientist analyzing the Duolingo AI layoffs.
Classify the following text into one of these categories:
- fear of precarity
- ethical concerns
- quality concerns
Also identify the tone:
- Critical
- Neutral
- Supportive
Return results in strict JSON with keys: category, tone only.
"""

# --- Load posts CSV ---
df = pd.read_csv("posts.csv", encoding="utf-8")  # make sure posts.csv is in the same folder

# Prepare results list
results = []

for index, row in df.iterrows():
    text = row["text"]
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # use a model available to your API key
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0
        )
        output = response.choices[0].message.content

        # Extract JSON from output (in case model adds extra text or formatting)
        json_match = re.search(r"\{.*\}", output, re.DOTALL)
        if json_match:
            classification = json.loads(json_match.group())
        else:
            classification = {"category": "unknown", "tone": "unknown"}

    except Exception as e:
        classification = {"category": "error", "tone": "error"}
        print(f"Error parsing output for text: {text}\n{e}")

    # Save results
    results.append({
        "text": text,
        "source_type": row.get("source_type", ""),
        "source_link": row.get("source_link", ""),
        "category": classification.get("category"),
        "tone": classification.get("tone")
    })

# --- Save classified CSV ---
results_df = pd.DataFrame(results)
results_df.to_csv("classified_posts.csv", index=False)
print("Classification complete! Results saved in 'classified_posts.csv'.")
