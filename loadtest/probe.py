import os,time,json,csv,httpx,datetime
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
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = f"results/probe_raw_{stamp}.csv"

COLUMNS = ["i", "question", "start_time", "status", "first_chunk_ms",
           "first_content_ms", "total_ms", "tokens_in", "tokens_out",
           "reasoning_tokens", "finish_reason", "remaining_requests",
           "remaining_tokens", "error"
        ]

rows = []

for i, q in enumerate(QUESTIONS):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": q}],
        "max_tokens": 500,
        "stream": True,
        "reasoning_effort":"low",
        "stream_options":{"include_usage":True}
    }
    start_time = datetime.datetime.now().isoformat()
    t0 = time.perf_counter()
    first_chunk = first_content = None
    status = usage = finish = None
    rem_req = rem_tok = None
    error = ""
    try:
        with httpx.stream("POST", URL, headers={"Authorization": f"Bearer {KEY}"},
                          json=body, timeout=60) as r:
            status = r.status_code
            rem_req = r.headers.get("x-ratelimit-remaining-requests")
            rem_tok = r.headers.get("x-ratelimit-remaining-tokens")
            if status != 200:
                r.read()
                error = r.text[:300]
                print(i, "ERROR", status, error)
                print({k: v for k, v in r.headers.items()
                       if "ratelimit" in k.lower() or "retry" in k.lower()})
            else:
                for line in r.iter_lines():
                    if not line.startswith("data: ") or line.endswith("[DONE]"):
                        continue
                    now = (time.perf_counter() - t0) * 1000
                    chunk = json.loads(line[6:])
                    if chunk.get("usage"):
                        usage = chunk["usage"]
                    if not chunk.get("choices"):
                        continue  
                    if first_chunk is None:
                        first_chunk = now
                    choice = chunk["choices"][0]
                    delta = choice.get("delta", {})
                    if first_content is None and delta.get("content"):
                        first_content = now
                    if choice.get("finish_reason"):
                        finish = choice["finish_reason"]
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        print(i, "EXC", error)

    total = (time.perf_counter() - t0) * 1000
    tin = usage.get("prompt_tokens") if usage else None
    tout = usage.get("completion_tokens") if usage else None
    reasoning = None
    if usage:
        reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")

    rows.append([i, q, start_time, status, first_chunk, first_content, total,
                 tin, tout, reasoning, finish, rem_req, rem_tok, error])
    print(f"{i} status={status} first_chunk={first_chunk and round(first_chunk)} "
          f"first_content={first_content and round(first_content)} total={round(total)} "
          f"in={tin} out={tout} reasoning={reasoning} finish={finish}")
    time.sleep(1)

with open(out_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(COLUMNS)
    w.writerows(rows)
print("saved", out_path)

