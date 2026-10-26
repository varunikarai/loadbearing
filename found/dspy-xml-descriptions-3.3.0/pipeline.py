"""Extract a return policy as structured output with DSPy, using its XML adapter.

The caller describes the output and each of its fields to the model. In dspy 3.3.1 and
later, the XML adapter writes a nested output's structure as bare tags, so the
descriptions of the fields inside it never reach the model; dspy 3.3.0 still sent them.
The model is DSPy's own DummyLM, which records what it was sent, so no API key is
needed and what the model was told is the output.
"""

import json
import sys

sys.path.insert(0, "deps")  # installed by the target's setup, frozen into the checkpoint

import dspy
from dspy.utils import DummyLM
from pydantic import Field, create_model

request = json.load(open(sys.argv[1]))

Policy = create_model(
    "Policy",
    __doc__=request.get("policy_description", ""),
    days=(int, Field(description=request.get("days_description", ""))),
    refundable=(bool, Field(description=request.get("refundable_description", ""))),
)


class ReturnPolicy(dspy.Signature):
    """Answer the customer from the retrieved policy passages."""

    question: str = dspy.InputField()
    passages: str = dspy.InputField()
    policy: Policy = dspy.OutputField(desc="The return policy that applies to this question")


adapter = dspy.XMLAdapter()
lm = DummyLM([{"policy": {"days": 14, "refundable": False}}], adapter=adapter)
dspy.configure(lm=lm, adapter=adapter)
dspy.Predict(ReturnPolicy)(question=request.get("question", ""), passages=request.get("passages", ""))
told = {message["role"]: message["content"] for message in lm.history[-1]["messages"]}
print(json.dumps({"model_was_told": told}, sort_keys=True))
