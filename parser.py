import os
import json
import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

SYSTEM_PROMPT = """You are a CAD data extractor. You MUST return ONLY a JSON object. No markdown. No explanation. No code blocks. No backticks. Just raw JSON starting with { and ending with }.

Convert all measurements to millimetres (1 metre = 1000mm, 1 cm = 10mm).
Default wall thickness = 200mm if not stated.
Default ceiling height = 3000mm if not stated.
Default door width = 900mm if not stated.

Return exactly this format:
{"spaces":[{"name":"booth","length_mm":10000,"width_mm":8000,"height_mm":3000,"wall_thickness_mm":200,"doors":[{"wall":"south","position_from_left_mm":4550,"width_mm":900,"height_mm":2100}],"windows":[],"notes":""}],"assumptions":[],"warnings":[]}"""

def parse_brief(user_text):
    print(f"Parsing: '{user_text}'")
    
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_text}
        ]
    )
    
    raw = response.content[0].text.strip()
    
    # Remove markdown code blocks if present
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    raw = raw.strip()
    
    # Find JSON object
    start = raw.find('{')
    end = raw.rfind('}') + 1
    if start != -1 and end > start:
        raw = raw[start:end]
    
    try:
        parsed_data = json.loads(raw)
        print("Parsed successfully!")
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"Parse error: {e}")
        print(f"Raw response was: {raw}")
        return {"error": "Could not parse response"}

if __name__ == "__main__":
    test = "create an exhibition booth 10 metres long and 8 metres wide, walls 200mm thick, one door on the south wall"
    result = parse_brief(test)
    print("\nResult:")
    print(json.dumps(result, indent=2))