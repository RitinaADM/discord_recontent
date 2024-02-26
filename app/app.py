import os
from pathlib import Path

from beanie import init_beanie
from fastapi import Depends, FastAPI, HTTPException, Request
from starlette.responses import HTMLResponse
from app.api.v1.discord.router import router as discord_router
from app.db.db import db, Slot, DBMessages
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()


parsers_manager = []

app.include_router(discord_router, prefix='/discord', tags=['discord'])


fake_posts_db = [{
    'title': 'Первый пост',
    'content': 'Здарова заебал.',
    'author': 'RitinaADM',
    'publication_date': '2023-06-20',
    'comments': [
        {'author': 'Пабло', 'content': 'копипиздер брат'},
        {'author': 'Мама', 'content': 'Шапку надень.'}
    ],
    'status': 'published'
},{
    'title': 'Second Blog Post',
    'content': 'Content of the second blog post.',
    'author': 'Jane Smith',
    'publication_date': None,
    'comments': [],
    'status': 'draft'
}]

"""@app.get("/", response_class=HTMLResponse)
async def read_posts(request: Request):
    return templates.TemplateResponse(request=request,
                                      name="blog.html",
                                      context={"request": request,
                                               "posts": fake_posts_db})"""


@app.get("/about")
def about():
    return "dev https://t.me/RitinaADM"


@app.on_event("startup")
async def on_startup():
    await init_beanie(
        database=db,
        document_models=[
            Slot,
            DBMessages

        ],
    )
