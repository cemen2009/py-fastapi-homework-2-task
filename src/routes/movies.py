from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema


router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={404: {"detail": "No movies found"}}
)
async def get_movies(db: AsyncSession = Depends(get_db)):
    per_page = 10
    page = 1
    result = await db.execute(select(MovieModel).limit(per_page).offset(page * per_page))
    movies = result.scalars()
    return movies
