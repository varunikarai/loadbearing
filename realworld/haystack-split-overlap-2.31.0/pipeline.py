"""Chunk a support document for retrieval with Haystack's RecursiveDocumentSplitter.

The calling code reads every setting from the request and passes it straight to the
splitter. Haystack issue #11767: when none of the separators occurs in the text, the
splitter's fallback path returned fixed-size chunks without applying split_overlap.
"""

import json
import sys

sys.path.insert(0, "deps")  # installed by the target's setup, frozen into the checkpoint

from haystack import Document
from haystack.components.preprocessors import RecursiveDocumentSplitter

request = json.load(open(sys.argv[1]))
splitter = RecursiveDocumentSplitter(
    split_length=request.get("split_length", 200),
    split_overlap=request.get("split_overlap", 0),
    separators=["\n\n", "\n"],
    split_unit="char",
)
chunks = splitter.run([Document(content=request["text"], meta={"source": request.get("source")})])["documents"]
print(json.dumps({"chunks": [c.content for c in chunks]}))
