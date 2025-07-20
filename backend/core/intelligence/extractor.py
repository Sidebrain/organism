import asyncio
from typing import Type, TypeVar

import instructor
from instructor.client import AsyncInstructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from core.config import OPENAI_API_KEY
from core.utils import time_it

async_openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

instructor_client = instructor.client.from_openai(async_openai_client)

# Change the bound to just BaseModel since all your models inherit from it
ModelT = TypeVar("ModelT", bound=BaseModel)


class People(BaseModel):
    name: str = Field(description="The name of the person")


class Places(BaseModel):
    name: str = Field(description="The name of the place")


class Questions(BaseModel):
    question: str = Field(description="Quesgtions that were raised")


class Topics(BaseModel):
    topic: str = Field(description="Topics that were discussed")


class Events(BaseModel):
    event: str = Field(description="Events that were discussed")


class Task(BaseModel):
    task: str = Field(description="The task that came up in the conversation")


class Extractor:
    def __init__(self, extractor_client: AsyncInstructor = instructor_client) -> None:
        self.extractor_client = extractor_client

    @time_it
    async def extract(self, text: str, model: Type[ModelT]) -> ModelT | None:
        response = await instructor_client.chat.completions.create(
            model="o4-mini",
            response_model=model,
            messages=[
                {"role": "user", "content": text},
            ],
        )
        return response

    async def extract_multiple(
        self, text: str, models: list[Type[BaseModel]]
    ) -> list[BaseModel | None]:
        tasks = [asyncio.create_task(self.extract(text, m)) for m in models]
        return await asyncio.gather(*tasks)

    @time_it
    async def base_extraction(self, text: str) -> list[BaseModel | None]:
        extracted_entities = await self.extract_multiple(
            text, [People, Places, Questions, Topics, Events, Task]
        )
        return extracted_entities
