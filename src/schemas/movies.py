from datetime import date

from pydantic import HttpUrl, BaseModel


# TODO: create enum for status of the movie


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str


class MovieListResponseSchema(BaseModel):
    movies: list[MovieDetailSchema]
    prev_page: HttpUrl | None
    next_page: HttpUrl | None
    total_pages: int
    total_items: int