from pydantic import BaseModel, Field


class ChatReportRequest(BaseModel):
    text: str = Field(..., example="馬太鞍溪橋斷了，需要兩台怪手")
