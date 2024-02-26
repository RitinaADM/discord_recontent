import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.services.discord import run_slot
from . import schemas
from app.db.db import Slot, get_slot
router = APIRouter()


@router.post("/slots")
async def route_create(schema: schemas.SlotSchema) -> Slot:
    slot = await Slot(**schema.model_dump()).create()
    return slot


@router.get("/slots")
async def route_get() -> List[Slot]:
    slots = await Slot.find().to_list()
    return slots


@router.get("/slots/{parser_id}")
async def route_get(slot: Slot = Depends(get_slot)) -> Slot:
    return slot


@router.put("/slots/{parser_id}")
async def route_put(schema: schemas.SlotSchema, slot: Slot = Depends(get_slot)) -> Slot:
    await slot.update({'$set': schema.model_dump()})
    await slot.save()
    return slot


@router.delete("/slots/{parser_id}")
async def route_delete(slot: Slot = Depends(get_slot)):
    await slot.delete()
    return {'message': f'Slot with {slot.id} deleted successfully'}


@router.post("/slots/{parser_id}/run")
async def route_run(background_tasks: BackgroundTasks, slot: Slot = Depends(get_slot)):
    if slot.enable:
        return {"message": "Parser is not running"}

    slot.enable = True
    await slot.save()
    background_tasks.add_task(run_slot, slot)
    return {"message": "Parser is running"}


@router.post("/slots/{parser_id}/stop")
async def route_run(background_tasks: BackgroundTasks, slot: Slot = Depends(get_slot)):
    if not slot.enable:
        return {"message": "Попытка убить мертвого засчитана."}

    slot.enable = False
    await slot.save()
    return {"message": "Parser is stopped"}