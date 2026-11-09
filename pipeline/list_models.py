import os, httpx
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("GROQ_API_KEY")

r = httpx.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {KEY}"},
    timeout=30,
)

print("status:",r.status_code)

if r.status_code == 200:
    for m in r.json()["data"]:
        print(m["id"])

else:
    print(r.text)

