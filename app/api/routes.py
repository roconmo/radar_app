from fastapi import APIRouter, HTTPException
from app.models.schemas import ArticleOut, ProcessRequest, ProcessResponse
from app.services import normalizer, deduplicator, history, insights

router = APIRouter()


@router.post("/process", response_model=ProcessResponse)
def process_articles(request: ProcessRequest):
    raw_articles = request.articles
    if not raw_articles:
        raise HTTPException(status_code=400, detail="No se recibieron artículos")

    normalized = normalizer.normalize(raw_articles)
    deduped = deduplicator.deduplicate(normalized)
    checked = history.mark_new_articles(deduped)

    new_only = [a for a in checked if a.is_new]
    analysis, raw_blob, insight_list = insights.generate_insights(new_only)

    history.save_run(
        articles_received=len(raw_articles),
        articles_after_dedup=len(deduped),
        new_articles=new_only,
        insights=insight_list,
    )

    return ProcessResponse(
        articles_received=len(raw_articles),
        articles_after_dedup=len(deduped),
        new_articles=len(new_only),
        analysis=analysis,
        raw_news_blob=raw_blob,
        insights=insight_list,
        new_articles_list=[
            ArticleOut(
                title=a.title,
                url=a.url,
                source=a.source,
                published_at=a.published_at.isoformat() if a.published_at else None,
                analizada=i < insights.MAX_ARTICLES,
            )
            for i, a in enumerate(new_only)
        ],
    )
