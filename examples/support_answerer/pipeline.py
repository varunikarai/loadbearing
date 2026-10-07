"""Support answerer over retrieved policy text: the LLM demo target.

Intended behaviour: answer the customer's question from the retrieved policy
passages, and say whether the item can still be returned and within how many
days. Nothing about the request's id, user or arrival time should matter.

The planted bug is the kind that ships: the retriever was changed to write
`passages`, and this step still reads `context`. Nothing throws. The prompt
just says there is no policy text, and the model answers from what most shops
do, fluently and wrongly.

Standard library only. Calls Nemotron on Nebius Token Factory at temperature 0.
"""

import json
import os
import re
import sys
import urllib.request

BASE_URL = os.environ.get("TOKEN_FACTORY_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
MODEL = os.environ.get("NEMOTRON_NANO_MODEL", "")

SYSTEM = (
    "You answer customer support questions for an online shop, using only the policy text "
    "you are given. Reply with one JSON object and nothing else: "
    '{"answer": "<one or two sentences to the customer>", '
    '"can_return": <true, false, or null if unknown>, '
    '"return_window_days": <the return window in days, or null if unknown>}'
)


def build_prompt(request: dict) -> str:
    # The retriever puts what it found here.
    context = request.get("context", "")
    return (
        f"Policy text:\n{context or '(none)'}\n\n"
        f"Customer question:\n{request.get('question', '')}"
    )


def ask(prompt: str) -> str:
    body = {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": 400,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {os.environ['NEBIUS_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        text = json.load(resp)["choices"][0]["message"].get("content") or ""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def answer(request: dict) -> dict:
    reply = ask(build_prompt(request))
    start, end = reply.find("{"), reply.rfind("}")
    try:
        parsed = json.loads(reply[start : end + 1])
    except ValueError:
        parsed = {"answer": reply}
    return {
        "answer": parsed.get("answer", ""),
        "can_return": parsed.get("can_return"),
        "return_window_days": parsed.get("return_window_days"),
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as fh:
        print(json.dumps(answer(json.load(fh)), sort_keys=True))
