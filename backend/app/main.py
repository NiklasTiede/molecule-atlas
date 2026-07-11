from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.candidates import router as candidate_router
from app.api.evidence import router as evidence_router
from app.models.api import HealthResponse

app = FastAPI(
    title="Molecule Atlas API",
    version="0.1.0",
    description="Candidate review API for small-molecule datasets.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)

app.include_router(candidate_router)
app.include_router(evidence_router)


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse()
