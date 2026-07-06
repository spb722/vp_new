from collections import Counter
import importlib

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import config
import graph
import pipeline
from reinforcer import DuplicateSeedError
from seeds import load_seeds
from vp_logging import print_vp_resolve_log

importlib.reload(graph)

app = FastAPI(title="VP Resolver API")


@app.on_event("startup")
def validate_startup_config():
    config.validate_runtime_config()


class ResolveRequest(BaseModel):
    input: str
    client_name: str | None = None


class ReinforceRequest(BaseModel):
    original_input: str
    parent_condition: str
    client_name: str | None = None


def reload_seed_state() -> dict:
    seeds = load_seeds()
    graph._seeds = seeds
    pipeline.seeds = seeds

    by_source = Counter(seed.get("source", "unknown") for seed in seeds)
    return {
        "ok": True,
        "seed_count": len(seeds),
        "sources": dict(sorted(by_source.items())),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/resolve")
def resolve(req: ResolveRequest):
    result = graph.run_vp_graph(req.input, client_name=req.client_name)
    print_vp_resolve_log(req, result)
    top_candidates = [
        {
            "seed_id": candidate.get("seed_id"),
            "score": candidate.get("score"),
            "warnings": candidate.get("warnings", []),
        }
        for candidate in result.get("top_candidates", [])
    ]
    return {
        "ok": result.get("ok", False),
        "parent_condition": result.get("final_parent_condition"),
        "error": result.get("error"),
        "selected_seed_id": result.get("selected_seed_id"),
        "top_candidates": top_candidates,
        "trajectory": result.get("trajectory", []),
        "decomposition_verified": result.get("decomposition_verified"),
        "decomposition_attempts": result.get("decomposition_attempt", 0),
        "decomposition_attempt_log": result.get("decomposition_attempt_log", []),
    }


@app.post("/reinforce")
def reinforce(req: ReinforceRequest):
    try:
        result = pipeline.reinforce_from_condition(
            original_input=req.original_input,
            parent_condition=req.parent_condition,
            client_name=req.client_name,
        )
    except DuplicateSeedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    reload_info = reload_seed_state()
    return {
        **result,
        "reload": reload_info,
    }


@app.post("/reload-seeds")
def reload_seeds():
    return reload_seed_state()
