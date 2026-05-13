"""FastAPI HTTP surface."""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.logging_setup import configure_logging
from ..core.paths import DEFAULT_LEADS_PATH
from ..core.pipeline import RunResponse
from ..services import OverrideService, RunService
from ..services.override_service import OverrideRecordError
from ..storage import db_settings, get_session, init_db


configure_logging(os.getenv("ALLICA_LOG_LEVEL", "INFO"))
log = logging.getLogger("allica.api")


# Request models
class RunRequest(BaseModel):
    leads: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Inbound leads. If omitted, the bundled sample dataset is used.",
    )
    draft_email: bool = Field(
        default=True,
        description="Whether to draft a first-touch email for eligible leads.",
    )
    prefer_llm: bool = Field(
        default=False,
        description=(
            "If true and an LLM API key is set, use an LLM to draft emails. "
            "Output is always passed through the safety post-processor."
        ),
    )


class FeedbackRequest(BaseModel):
    corrected_owner: str = Field(
        ...,
        description='New owner: "Growth-Inbound" | "Triage" | "Manual-Review" | "Decline".',
    )
    operator_id: Optional[str] = Field(
        default=None, description="Identifier of the operator submitting the override."
    )
    reason: Optional[str] = Field(default=None, description="Optional free-text rationale.")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    init_db()
    log.info(
        "app_started db_url=%s auto_migrate=%s",
        "sqlite" if db_settings().is_sqlite else "configured",
        db_settings().auto_migrate,
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Allica GTM Assistant",
        version="0.2.0",
        description="Inbound UK SME lead triage: validate, enrich, score, route, draft email.",
        lifespan=_lifespan,
    )

    # CORS — open by default (dev / co-located), allowlist in prod.
    # Set ALLICA_CORS_ORIGINS to a comma-separated list of origins, e.g.
    #   ALLICA_CORS_ORIGINS=https://app.example.com,https://staging.example.com
    raw_origins = os.getenv("ALLICA_CORS_ORIGINS", "*").strip()
    cors_origins = (
        ["*"] if raw_origins == "*" else [o.strip() for o in raw_origins.split(",") if o.strip()]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "allica-gtm",
            "storage": "sqlite" if db_settings().is_sqlite else "configured",
        }

    @app.post("/run", response_model=RunResponse)
    def run(
        req: RunRequest, session: Session = Depends(get_session)
    ) -> RunResponse:
        try:
            leads = req.leads
            if leads is None:
                leads = json.loads(DEFAULT_LEADS_PATH.read_text(encoding="utf-8"))
            payload_for_hash = {
                "leads": leads,
                "draft_email": req.draft_email,
                "prefer_llm": req.prefer_llm,
            }
            service = RunService(session)
            response, _run_id, _cached = service.execute(
                payload_for_hash,
                leads=leads,
                draft_email=req.draft_email,
                prefer_llm=req.prefer_llm,
            )
            return response
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail=f"Missing data file: {exc}") from exc
        except json.JSONDecodeError as exc:
            log.warning("run_default_leads_invalid_json: %s", exc)
            raise HTTPException(
                status_code=500,
                detail="Bundled default leads file is not valid JSON.",
            ) from exc
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
        except SQLAlchemyError:
            log.exception("run_storage_failed")
            raise HTTPException(
                status_code=503,
                detail="Storage temporarily unavailable; retry shortly.",
            ) from None
        except OSError as exc:
            log.warning("run_read_error: %s", exc)
            raise HTTPException(
                status_code=500,
                detail="Could not read lead data from disk.",
            ) from exc
        except Exception as exc:  # noqa: BLE001
            log.exception("run_failed_unexpected")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while processing the run.",
            ) from exc

    @app.get("/runs")
    def list_runs(
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0, le=10_000),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        service = RunService(session)
        runs = service.list_recent(limit=limit, offset=offset)
        return {"runs": runs, "has_more": len(runs) == limit}

    @app.get("/runs/{run_id}")
    def get_run(
        run_id: str, session: Session = Depends(get_session)
    ) -> dict[str, Any]:
        service = RunService(session)
        run = service.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"run {run_id} not found")
        return run

    @app.get("/leads/history")
    def lead_history(
        external_id: Optional[str] = Query(None, description="External lead id, e.g. L-2001"),
        company: Optional[str] = Query(None, description="Company name to search by"),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        if not external_id and not company:
            raise HTTPException(
                status_code=400,
                detail="Provide at least one of external_id or company.",
            )
        service = RunService(session)
        return {
            "results": service.history_for_lead(external_id=external_id, company=company)
        }

    @app.post("/leads/{lead_result_id}/feedback")
    def record_feedback(
        lead_result_id: str,
        body: FeedbackRequest,
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        service = OverrideService(session)
        try:
            return service.record(
                lead_result_id=lead_result_id,
                corrected_owner=body.corrected_owner,
                operator_id=body.operator_id,
                reason=body.reason,
            )
        except OverrideRecordError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/sample")
    def sample() -> JSONResponse:
        """Bundled sample dataset (handy for demos and the Next.js console)."""
        return JSONResponse(json.loads(DEFAULT_LEADS_PATH.read_text(encoding="utf-8")))

    @app.get("/")
    def root() -> dict[str, Any]:
        """Service identity. The operator UI lives in the separate Next.js
        frontend (see solution/frontend/) which talks to this API."""
        return {
            "service": "allica-gtm",
            "version": "0.2.0",
            "endpoints": [
                "/run",
                "/runs",
                "/runs/{id}",
                "/leads/history",
                "/leads/{id}/feedback",
                "/sample",
                "/health",
                "/docs",
            ],
        }

    return app


app = create_app()
