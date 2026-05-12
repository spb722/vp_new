from collections import Counter
import importlib

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import graph
import pipeline
from reinforcer import DuplicateSeedError
from seeds import load_seeds

importlib.reload(graph)

app = FastAPI(title="VP Resolver API")


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
    return {
        "ok": result.get("ok", False),
        "parent_condition": result.get("final_parent_condition"),
        "error": result.get("error"),
        "selected_seed_id": result.get("selected_seed_id"),
        "top_candidates": result.get("top_candidates", []),
        "trajectory": result.get("trajectory", []),
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
