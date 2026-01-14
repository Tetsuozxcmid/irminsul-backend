from pydantic import BaseModel

class YandexCallbackDTO(BaseModel):
    code: str

class YandexCodeSchema(BaseModel):
    code: str