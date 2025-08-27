import asyncpg.exceptions
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    ActorModel,
    LanguageModel,
    GenreModel,
    CountryModel,
    Base
)


async def get_or_create_entities(db: AsyncSession, model: Base, names: list[str], code_field: str = None) -> list:
    """
    This function created to optimize get_or_create_entities() function.
    It checks if entity exists and creates one if not.
    There's a special logic for country entity: default search of entities is build on name,
    but you can specify code_field for search by that certain field.
    For example code_field="code", it should search country by their code (and not name) field.
    """
    if names is None:
        return []

    # if there is specified code (e.g. "code" for CountryModel) and only one element in the names list
    if code_field is not None and len(names) == 1:
        # create SQL statement and get one result or None if there's no result
        existing_stmt = select(model).where(getattr(model, code_field) == names[0])
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        # if entity (country) with specified code_field then return it in a list
        if existing:
            return [existing]

        # create entity if there are no entity with specified code_field

        # WARNING: it could break limitation for 3 letters per one country code
        # limitation for codes: 0<length<=3; I need to TEST IT !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        new_entity = model(**{code_field: names[0], "name": names[0]})

        db.add(new_entity)  # mark the object as pending (to be inserted)
        try:
            await db.flush()    # execute the SQL INSERT immediately so object gets id and constraints are checked
        except DBAPIError as e:
            if isinstance(e.orig, asyncpg.exceptions.StringDataRightTruncationError):
                print("ERROR LOG: Length of country code is too long (maximum is 3 characters)")
                # here we should raise custom exception but that's not a point of current task

            raise e

        return [new_entity]

    # if it's default search parameter (name) then fetch existing objects from db

    existing_stmt = select(model).where(model.name.in_(names))
    existing_result = await db.execute(existing_stmt)
    existing: list = existing_result.scalars().all()
    # existing = existing_result.scalars().all()

    existing_names = {e.name for e in existing}

    # {set of names to exist} - {set of names that exist} = {names that doesn't exist}
    missing_names = set(names) - existing_names

    # create ORM-objects that should exist
    new_entities = [model(name=name) for name in missing_names]
    if new_entities:
        db.add_all(new_entities)
        await db.flush()

    return existing + new_entities


async def resolve_movie_relations(movie_data: dict, db: AsyncSession) -> dict[
    str,
    CountryModel | list[Base]
]:
    """
    This function resolves relations between movies and country, genres, actors and languages.
    It returns dict that contain ORM-ready objects for each relation.
    """
    relations = {}

    if "country" in movie_data:
        country_list = [movie_data["country"]]

        # it can cause an error if date is breaking any constraint
        countries = await get_or_create_entities(db, CountryModel, country_list, code_field="code")

        if not countries:
            raise HTTPException(status_code=400, detail="Invalid country code")

        relations["country"] = countries[0]

    if "genres" in movie_data:
        relations["genres"] = await get_or_create_entities(db, GenreModel, movie_data["genres"])

    if "actors" in movie_data:
        relations["actors"] = await get_or_create_entities(db, ActorModel, movie_data["actors"])

    if "languages" in movie_data:
        relations["languages"] = await get_or_create_entities(db, LanguageModel, movie_data["languages"])

    return relations