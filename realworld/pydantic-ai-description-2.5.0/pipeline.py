"""Ask a pydantic-ai agent for structured output, a fruit or a vehicle.

The caller names the output and describes it to the model. pydantic-ai issue #6262: for
a union NativeOutput, the description sent to the model was the last member's docstring,
not the one given. The model here is pydantic-ai's own FunctionModel, which reports what
the agent sent it, so no API key is needed and what the model was told is the output.
"""

import json
import sys

sys.path.insert(0, "deps")  # installed by the target's setup, frozen into the checkpoint

from pydantic import BaseModel
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel


class Fruit(BaseModel):
    """A fruit"""

    name: str
    color: str


class Vehicle(BaseModel):
    """A vehicle"""

    name: str
    wheels: int


request = json.load(open(sys.argv[1]))
told = {}


def model(messages, info):
    told["output_name"] = info.model_request_parameters.output_object.name
    told["output_description"] = info.model_request_parameters.output_object.description
    told["prompt"] = messages[-1].parts[-1].content
    answer = {"kind": "Fruit", "data": {"name": "banana", "color": "yellow"}}
    return ModelResponse(parts=[TextPart(content=json.dumps({"result": answer}))])


agent = Agent(
    FunctionModel(function=model),
    output_type=NativeOutput([Fruit, Vehicle], name=request["output_name"], description=request.get("output_description")),
)
agent.run_sync(request["question"])
print(json.dumps({"model_was_told": told}, sort_keys=True))
