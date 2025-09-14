import re
import json

def parse_gpt_clips(gpt_text):
    """
    Tar GPT-output som Markdown-liknande lista och returnerar JSON-lista med start, end, name.
    """
    clips = []

    # Regex som ignorerar mellanslag, bindestreck och stjärnor
    pattern = r'- \*\*Start Time:\*\*\s*(\d+).*?- \*\*End Time:\*\*\s*(\d+).*?- \*\*Reason:\*\*\s*(.*?)(?=\n\d+\. \*\*Highlight|\Z)'
    matches = re.findall(pattern, gpt_text, flags=re.DOTALL)

    for i, (start, end, reason) in enumerate(matches, 1):
        clip = {
            "start": int(start),
            "end": int(end),
            "name": f"highlight{i}.mp4",
            "reason": reason.strip()
        }
        clips.append(clip)

    return clips

# Testa funktionen
if __name__ == "__main__":
    sample_text = """1. **Highlight 1**
   - **Start Time:** 0
   - **End Time:** 5
   - **Reason:** Michael Dute lands a powerful right hand that knocks Tyrone Spong down, signaling a decisive moment in the fight.

2. **Highlight 2**
   - **Start Time:** 5
   - **End Time:** 7
   - **Reason:** The fight concludes with Dute's victory, emphasizing the impact of the knockout punch."""
    
    clips_json = parse_gpt_clips(sample_text)
    print(json.dumps(clips_json, indent=2))
