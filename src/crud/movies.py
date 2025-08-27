import math

from fastapi import HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from starlette.responses import JSONResponse

from crud.utils.resolve_movie_relations import resolve_movie_relations
from database import MovieModel
from schemas import (
    MovieListItemSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    MoviePatchSchema
)


async def get_movies(
        db: AsyncSession,
        request: Request,
        page: int,
        per_page: int
) -> dict:
    # calculating offset and fetching movies ordering by ID in descending order
    offset = (page - 1) * per_page
    movie_result = await db.execute(
        select(MovieModel)
        .order_by(*MovieModel.default_order_by())
        .offset(offset)
        .limit(per_page)
    )
    movies = movie_result.scalars().all()

    if not movies:
        raise HTTPException(
            status_code=404,
            detail="No movies found."
        )

    # get validated schema instances from raw db models
    movie_items = [MovieListItemSchema.model_validate(movie) for movie in movies]

    count_result = await db.execute(select(func.count()).select_from(MovieModel))

    total_items = count_result.scalar()
    total_pages = math.ceil(total_items / per_page)

    base_url = str(request.url.path).split('?')[0]
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None

    return {
        "movies": movie_items,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


async def get_movie(movie_id: int, db: AsyncSession) -> MovieModel | None:
    stmt = select(MovieModel).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.languages)
    ).where(MovieModel.id == movie_id)

    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    return movie


async def create_movie(movie_data: MovieCreateSchema, db: AsyncSession) -> MovieModel:
    payload = movie_data.model_dump()

    existing = await db.execute(select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.date == movie_data.date
    )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie_data.name}' and release date '{movie_data.date}' already exists."
        )

    # get data for relations of the movie model
    try:
        relation_data = await resolve_movie_relations(payload, db)
    except DBAPIError:
        # raise HTTPException(status_code=422, detail="Country code must be at most 3 characters long")
        raise HTTPException(status_code=422, detail="Invalid relation data")

    # create movie ORM-object with non-relations data (without genres, actors, country, languages)
    relation_fields = ["country", "genres", "actors", "languages"]
    new_movie_obj = MovieModel(**{
        key: value for key, value in payload.items()
        if key not in relation_fields
    })

    # fill the movie ORM-object with relations data (genres, actors, country, languages)
    # new_movie_obj.genres = relation_data["genres"]
    # new_movie_obj.actors = relation_data["actors"]
    # new_movie_obj.country = relation_data["country"]
    # new_movie_obj.languages = relation_data["languages"]
    for field in relation_fields:
        setattr(new_movie_obj, field, relation_data[field])

    # save the movie
    db.add(new_movie_obj)
    await db.commit()
    await db.refresh(new_movie_obj)

    stmt = select(MovieModel).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    ).where(MovieModel.id == new_movie_obj.id)
    result = await db.execute(stmt)

    return result.scalar_one()


async def update_movie(
        movie_id: int,
        updated_movie_data: MovieUpdateSchema | MoviePatchSchema,
        db: AsyncSession
) -> JSONResponse:
    # get movie from db
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the give ID was not found"
        )

    # exclude_unset for correct working of both update and patch schemas
    data = updated_movie_data.model_dump(exclude_unset=True)

    relation_fields = ["country", "genres", "actors", "languages"]
    relation_data = await resolve_movie_relations(data, db)

    # set data for each relation field if it was updated
    for field in relation_fields:
        if field in relation_data:
            setattr(movie, field, relation_data[field])

    # remove relation fields data
    for field in relation_fields:
        data.pop(field, None)

    # set non-relation fields
    for field, value in data.items():
        setattr(movie, field, value)

    try:
        await db.commit()
    except IntegrityError:
        print(f"DEBUG LOG: caught an integrity error while updating the movie")
        raise HTTPException(status_code=422, detail="Film with this name and date already exists")

    await db.refresh(movie)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "Movie updated successfully."
        }
    )


async def delete_movie(movie_id: int, db: AsyncSession) -> None:
    # fetch movie from db
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if not movie:
        print("DEBUG LOG: There is no movie")
        raise HTTPException(
            status_code=404,
            detail="Movie with the give ID was not found"
        )
    print("DEBUG LOG: There is a movie")

    await db.delete(movie)
    await db.commit()
