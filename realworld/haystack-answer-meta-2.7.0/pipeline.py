"""Build the answer a RAG pipeline returns, with Haystack's AnswerBuilder.

The caller attaches where the answer came from as runtime meta. Haystack issue #8542:
AnswerBuilder dropped runtime meta when the reply was a ChatMessage, keeping only the
generator's own meta.
"""

import json
import sys

sys.path.insert(0, "deps")  # installed by the target's setup, frozen into the checkpoint

from haystack.components.builders import AnswerBuilder
from haystack.dataclasses import ChatMessage

request = json.load(open(sys.argv[1]))
reply = ChatMessage.from_assistant(request["reply"], meta={"model": "nemotron"})
meta = [request["meta"]] if "meta" in request else None
answers = AnswerBuilder().run(query=request["query"], replies=[reply], meta=meta)["answers"]
print(json.dumps({"answers": [{"data": a.data, "query": a.query, "meta": a.meta} for a in answers]}, sort_keys=True, default=str))
