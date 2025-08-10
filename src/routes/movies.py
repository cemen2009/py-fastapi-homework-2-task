from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema, MovieDetailResponseSchema


router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={404: {"detail": "No movies found"}}
)
async def get_movies(
        request: Request,
        db: AsyncSession = Depends(get_db),
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
):
    # calculating offset and fetching movies ordering by ID in descending order
    offset = (page - 1) * per_page
    result = await db.execute(
        select(MovieModel)
        .order_by(desc(MovieModel.id))
        .offset(offset)
        .limit(per_page)
    )
    movies = result.scalars().all()

    if movies is None:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    result_count = await db.execute(select(func.count()).select_from(MovieModel))

    total_items = result_count.scalar()
    total_pages = total_items // per_page + 1 if total_items % per_page != 0 else total_items / per_page

    base_url = str(request.url).split('?')[0]
    next_page = f"{base_url}?per_page={per_page}&page={page + 1}" if page < total_pages else None
    prev_page = f"{base_url}?per_page={per_page}&page={page - 1}" if page > 1 else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema
)
async def create_movie(
        movie: MovieDetailResponseSchema,
        db: AsyncSession = Depends(get_db)
):
    ...
