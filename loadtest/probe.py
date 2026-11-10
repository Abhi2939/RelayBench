import os,time,json,csv,httpx
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("GROQ_API_KEY")
MODEL = "openai/gpt-oss-120b"
URL = "https://api.groq.com/openai/v1/chat/completions"

QUESTIONS = [
    "What is self-attention?",
    "What is multi-head attention?",
    "Why does the Transformer use positional encoding?",
    "What is Moshi?",
    "What is the Mimi codec?",
    "What is dynamic chunking?",
    "What is a residual connection?",
    "What does the decoder do?",
    "What is full-duplex dialogue?",
    "What is a hierarchical sequence model?",
]

os.makedirs("results",exist_ok=True)
rows = []

for i, q in enumerate(QUESTIONS):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": q}],
        "max_tokens": 200,
        "stream": True,
    }
    t0 = time.perf_counter()
    first_chunk = first_content = None
    status = None
    try:
        with httpx.stream("POST", URL, headers={"Authorization": f"Bearer {KEY}"},
                          json=body, timeout=60) as r:
            status = r.status_code
            if status != 200:
                r.read()
                print(i, "ERROR", status, r.text[:200])
                print({k: v for k, v in r.headers.items()
                       if "ratelimit" in k.lower() or "retry" in k.lower()})
            else:
                for line in r.iter_lines():
                    if not line.startswith("data: ") or line.endswith("[DONE]"):
                        continue
                    now = (time.perf_counter() - t0) * 1000
                    if first_chunk is None:
                        first_chunk = now
                    delta = json.loads(line[6:])["choices"][0]["delta"]
                    if first_content is None and delta.get("content"):
                        first_content = now
    except Exception as e:
        print(i, "EXC", e)
    total = (time.perf_counter() - t0) * 1000
    rows.append([i, q, status, first_chunk, first_content, total])
    print(f"{i} status={status} first_chunk={first_chunk} first_content={first_content} total={total:.0f}")
    time.sleep(1)

with open("results/probe_raw.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["i", "question", "status", "first_chunk_ms", "first_content_ms", "total_ms"])
    w.writerows(rows)

