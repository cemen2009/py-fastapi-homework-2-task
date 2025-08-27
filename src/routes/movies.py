from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path, Body, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud import (
    get_movies,
    create_movie,
    get_movie,
    update_movie,
    delete_movie,
)
from database import get_db
from schemas import MovieListResponseSchema, MovieDetailResponseSchema, MoviePatchSchema
from schemas.movies import MovieCreateSchema, MovieUpdateSchema


router = APIRouter()


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={404: {"detail": "No movies found"}}
)
async def get_movies_handler(
        request: Request,
        db: AsyncSession = Depends(get_db),
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=20)] = 10,
):
    result = await get_movies(
        request=request,
        db=db,
        page=page,
        per_page=per_page
    )
    return result


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    responses={404: {"detail": "Movie not found"}}
)
async def get_movie_handler(
        movie_id: Annotated[int, Path()],
        db: AsyncSession = Depends(get_db)
):
    movie = await get_movie(movie_id, db)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie_handler(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db)
):
    new_movie = await create_movie(movie, db)
    return new_movie


@router.put("/movies/{movie_id}", response_model=None)
async def update_movie_handler(
        movie_id: Annotated[int, Path()],
        update_movie_data: Annotated[MovieUpdateSchema, Body()],
        db: AsyncSession = Depends(get_db)
):
    response = await update_movie(movie_id, update_movie_data, db)
    return response


@router.patch("/movies/{movie_id}", response_model=None)
async def patch_movie_handler(
        movie_id: Annotated[int, Path()],
        updated_movie_data: Annotated[MoviePatchSchema, Body()],
        db: AsyncSession = Depends(get_db)
):
    response = await update_movie(movie_id, updated_movie_data, db)
    return response


@router.delete("/movies/{movie_id}", response_model=None)
async def delete_movie_handler(
        movie_id: Annotated[int, Path()],
        db: AsyncSession = Depends(get_db)
):
    await delete_movie(movie_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
