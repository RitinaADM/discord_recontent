import datetime
from enum import Enum
from typing import List

from beanie import PydanticObjectId
from pydantic import BaseModel, Field


class ParserStatuses(str, Enum):
    padding = 'padding'
    ready = 'ready'
    error = 'error'


class PosterAccountSchema(BaseModel):
    token: str
    proxy: str | None
    status: str
    created_at: datetime.datetime


class SlotSchema(BaseModel):
    parser_token: str = Field(description='Токен авторизации парсер аккаунта')
    parser_chatid: int = Field(description='Чат ид канала для парсинга')
    parser_proxy: str | None = Field(default='login:password@ip:port')
    poster_chatid: str = Field(description='Чат ид канала для постинга')
    poster_accounts: list[PosterAccountSchema] = []
    enable: bool = Field(default=False)
    timeout: int = Field(default=30)
    status: ParserStatuses = Field(default=ParserStatuses.padding)


class ParsedMessageSchema(BaseModel):
    id: str
    author_id: str
    content: str


class ParserConfig(BaseModel):
    token: str = Field(description='Токен авторизации')
    chatid: str = Field(description='Чат ид канала')
    proxy: str | None = Field(default='login:password@ip:port')


class PosterConfig(BaseModel):
    chatid: str = Field(default='Чат ид канала')
    accounts: list[PosterAccountSchema]


class SlotSchema(BaseModel):
    parser_config: ParserConfig
    poster_config: PosterConfig
    enable: bool
    timeout: int = Field(default=30)
    blacklist: List[str] = []
