from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

print("Sending test to Claude...")

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Reply with exactly: CONNECTION SUCCESSFUL"}
    ]
)

print("Claude replied:", response.content[0].text)
print("Everything is working!")