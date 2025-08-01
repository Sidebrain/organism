from typing import Literal, cast

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Message(BaseModel):
    role: Literal["user", "assistant", "human", "generative"]
    content: str

    def to_openai_message(
        self,
    ) -> ChatCompletionMessageParam:
        if self.role == "generative":
            return cast(
                ChatCompletionMessageParam,
                {"role": "assistant", "content": self.content},
            )
        elif self.role == "human":
            return cast(
                ChatCompletionMessageParam, {"role": "user", "content": self.content}
            )
        else:
            return cast(
                ChatCompletionMessageParam, {"role": self.role, "content": self.content}
            )


class ChatRequest(BaseModel):
    messages: list[Message]


class ChoiceDelta(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    content: str | None = None
    role: str | None = None


class Choice(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    index: int
    delta: ChoiceDelta
    finish_reason: str | None = None


class StreamingResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[Choice]
