from pydantic import BaseModel


class ProcessRequest(BaseModel):
    text: str


class ProcessResponse(BaseModel):
    output: str