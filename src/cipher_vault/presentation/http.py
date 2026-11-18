"""HTTP routes; they translate requests and hold no game rules."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Health(BaseModel):
    """Typed health response."""

    status: Literal["ok"] = "ok"


@router.get("/health", response_model=Health)
def health() -> Health:
    """Answer GET with a typed status for liveness checks."""
    return Health()
