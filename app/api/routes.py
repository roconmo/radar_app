from fastapi import APIRouter, HTTPException
from app.models.schemas import RawArticle, ProcessResponse
from app.services import normalizer, deduplicator, history, insights

router = APIRouter()


@router.post("/process", response_model=ProcessResponse)
def process_articles(raw_articles: list[RawArticle]):
    if not raw_articles:
        raise HTTPException(status_code=400, detail="No se recibieron artículos")

    normalized = normalizer.normalize(raw_articles)
    deduped = deduplicator.deduplicate(normalized)
    checked = history.mark_new_articles(deduped)

    new_only = [a for a in checked if a.is_new]
    generated = insights.generate_insights(new_only)

    history.save_run(
        articles_received=len(raw_articles),
        articles_after_dedup=len(deduped),
        new_articles=new_only,
        insights=generated,
    )

    return ProcessResponse(
        articles_received=len(raw_articles),
        articles_after_dedup=len(deduped),
        new_articles=len(new_only),
        insights=generated,
    )
