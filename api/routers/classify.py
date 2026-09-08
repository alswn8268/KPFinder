from fastapi import APIRouter

from app import organizer
from app.llm_client import OllamaError
from app.similar import find_similar_documents
from api.serialization import entries_to_models, model_to_template, models_to_entries
from api.schemas import (
    AssignmentInfo,
    ClassifyRequest,
    ClassifyResponse,
    SimilarPairModel,
    SimilarRequest,
    SummarizeRequest,
    SummarizeResponse,
)

router = APIRouter(prefix="/api", tags=["classify"])


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    entries = models_to_entries(req.entries)
    organizer.summarize_entries(entries, req.root, req.model)
    return SummarizeResponse(entries=entries_to_models(entries))


@router.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    entries = models_to_entries(req.entries)
    template = model_to_template(req.template)
    user_rules = [r.model_dump() for r in req.user_rules] or None

    ai_failed = False
    error_detail = ""
    try:
        result = organizer.classify_entries(
            entries, template, req.model, use_ai=req.use_ai, user_rules=user_rules
        )
    except OllamaError as exc:
        ai_failed = True
        error_detail = str(exc)
        result = organizer.classify_entries(
            entries, template, req.model, use_ai=False, user_rules=user_rules
        )

    assignments = {src: AssignmentInfo(**info) for src, info in result["assignments"].items()}
    return ClassifyResponse(
        categories=result.get("categories", []),
        assignments=assignments,
        notes=result.get("notes", ""),
        ai_failed=ai_failed,
        error_detail=error_detail,
    )


@router.post("/similar", response_model=list[SimilarPairModel])
def similar(req: SimilarRequest):
    entries = models_to_entries(req.entries)
    pairs = find_similar_documents(entries)
    return [
        SimilarPairModel(a=a.relative_path, b=b.relative_path, score=score) for a, b, score in pairs
    ]
