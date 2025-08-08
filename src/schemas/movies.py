from datetime import date

from pydantic import HttpUrl, BaseModel, ConfigDict


# TODO: create enum for status of the movie


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieDetailSchema]
    prev_page: HttpUrl | None
    next_page: HttpUrl | None
    total_pages: int
    total_items: int