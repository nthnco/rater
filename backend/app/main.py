from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import auth, me, movies, services
from app.services.tmdb import TMDBNotFoundError, TMDBUnavailableError

app = FastAPI(title="Rater")
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(movies.router)
app.include_router(services.router)


@app.exception_handler(TMDBNotFoundError)
def tmdb_not_found(_: Request, __: TMDBNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Movie not found"})


@app.exception_handler(TMDBUnavailableError)
def tmdb_unavailable(_: Request, __: TMDBUnavailableError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": "Movie data provider unavailable"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
