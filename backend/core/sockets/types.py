from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ChatRequest(BaseModel):
    # conversation_id: str
    message: str


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
