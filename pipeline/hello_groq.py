import os, time
import httpx
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("GROQ_API_KEY")   
MODEL = "openai/gpt-oss-120b"    

t0 = time.perf_counter()
r = httpx.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {KEY}"},
    json={
        "model": MODEL,
        "messages": [{"role": "user", "content": "In one sentence, what is a transformer?"}],
        "max_tokens": 100,
        "reasoning_effort":"low"
    },
    timeout=30,
)
elapsed_ms = (time.perf_counter() - t0) * 1000

print("status:", r.status_code)
print(f"time: {elapsed_ms:.0f} ms")
if r.status_code != 200:
    print("error body:", r.text)
    raise SystemExit

print("status:", r.status_code)
print(f"time: {elapsed_ms:.0f} ms")
print("answer:", r.json()["choices"][0]["message"]["content"])
print("tokens:", r.json().get("usage"))
print("--- rate limit headers ---")
for k, v in r.headers.items():
    if "ratelimit" in k.lower() or "retry" in k.lower():
        print(k, ":", v)