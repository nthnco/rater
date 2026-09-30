from fastapi import FastAPI

app = FastAPI(title="Rater")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
