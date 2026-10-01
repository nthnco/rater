"""Request/response models: our API contract. The frontend never sees raw TMDB JSON."""

from datetime import date

from pydantic import BaseModel, EmailStr, Field

# --- auth ---


class SignupRequest(BaseModel):
    email: EmailStr
    # NIST SP 800-63B: enforce a minimum length, no composition rules; cap length so huge
    # inputs can't be used to make hashing expensive.
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class UserOut(BaseModel):
    """What we expose about a user. Never includes password_hash."""

    id: int
    email: str
    region: str


# --- streaming services ---


class ServiceOut(BaseModel):
    id: int  # TMDB provider_id
    name: str
    logo_path: str | None


class UpdateServicesRequest(BaseModel):
    service_ids: list[int] = Field(max_length=50)  # replaces the whole set; [] means none


# --- movies ---


class MovieSearchResult(BaseModel):
    tmdb_id: int
    title: str
    year: int | None
    poster_path: str | None


class PersonOut(BaseModel):
    id: int
    name: str


class ProviderOut(BaseModel):
    id: int
    name: str
    logo_path: str | None


class MovieDetail(BaseModel):
    tmdb_id: int
    title: str
    year: int | None
    release_date: date | None
    overview: str | None
    poster_path: str | None
    runtime_min: int | None
    genres: list[str]
    directors: list[PersonOut]
    top_cast: list[PersonOut]
    vote_average: float | None
    vote_count: int | None
    providers_region: str
    providers: list[ProviderOut]  # flat-rate (subscription); source: JustWatch via TMDB
