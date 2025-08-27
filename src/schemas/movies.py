import datetime
from decimal import Decimal
from typing import Literal

from pydantic import HttpUrl, BaseModel, ConfigDict

from src.database.models import MovieStatusEnum
from schemas.actors import ActorSchema
from schemas.countries import CountrySchema
from schemas.genres import GenreSchema
from schemas.languages import LanguageSchema


class MovieBaseSchema(BaseModel):
    name: str
    date: datetime.date
    score: float
    overview: str
    status: Literal[
        MovieStatusEnum.IN_PRODUCTION,
        MovieStatusEnum.POST_PRODUCTION,
        MovieStatusEnum.RELEASED
    ]
    budget: Decimal
    revenue: Decimal
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieDetailResponseSchema(MovieBaseSchema):
    id: int
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(MovieBaseSchema):
    pass


class MovieUpdateSchema(MovieBaseSchema):
    pass


class MoviePatchSchema(BaseModel):
    name: str | None = None
    date: datetime.date | None = None
    score: float | None = None
    overview: str | None = None
    status: Literal[
        MovieStatusEnum.IN_PRODUCTION,
        MovieStatusEnum.POST_PRODUCTION,
        MovieStatusEnum.RELEASED
    ] | None = None
    budget: Decimal | None = None
    revenue: Decimal | None = None
    country: str | None = None
    genres: list[str] | None = None
    actors: list[str] | None = None
    languages: list[str] | None = None
