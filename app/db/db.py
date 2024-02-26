import motor.motor_asyncio
from beanie import PydanticObjectId, Document
from pydantic import Field
from fastapi import HTTPException
from app.api.v1.discord.schemas import SlotSchema, ParsedMessageSchema

DATABASE_URL = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URL, uuidRepresentation="standard"
)
db = client["ARGSCore_Parser"]



class Slot(Document, SlotSchema):
    pass


class DBMessages(Document):
    slot: PydanticObjectId
    message: ParsedMessageSchema
    isPublish: bool
    resender: str | None


async def get_slot(parser_id) -> Slot:
    parser = await Slot.get(parser_id)
    if not parser:
        raise HTTPException(status_code=404, detail='Not Found')
    return parser