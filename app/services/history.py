import sqlite3
import json
from pathlib import Path
from datetime import datetime
from app.models.schemas import NormalizedArticle, Insight
from app.core.config import settings


def _get_conn() -> sqlite3.Connection:
    Path(settings.history_db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.history_db_path)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS seen_urls (
            url TEXT PRIMARY KEY,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            articles_received INTEGER,
            articles_after_dedup INTEGER,
            new_articles INTEGER,
            insights_generated INTEGER
        );

        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER REFERENCES pipeline_runs(id),
            title TEXT,
            url TEXT,
            source TEXT,
            published_at TIMESTAMP,
            content TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER REFERENCES pipeline_runs(id),
            title TEXT,
            summary TEXT,
            relevance TEXT,
            sources TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()


def mark_new_articles(articles: list[NormalizedArticle]) -> list[NormalizedArticle]:
    conn = _get_conn()
    _cleanup_old_urls(conn)
    result = []
    for article in articles:
        row = conn.execute(
            "SELECT url FROM seen_urls WHERE url = ? AND seen_at > datetime('now', ? || ' days')",
            (article.url, f"-{settings.url_retention_days}"),
        ).fetchone()
        if row:
            article.is_new = False
        else:
            conn.execute(
                "INSERT OR REPLACE INTO seen_urls (url, seen_at) VALUES (?, CURRENT_TIMESTAMP)",
                (article.url,),
            )
            article.is_new = True
        result.append(article)
    conn.commit()
    conn.close()
    return result


def _cleanup_old_urls(conn: sqlite3.Connection):
    conn.execute(
        "DELETE FROM seen_urls WHERE seen_at < datetime('now', ? || ' days')",
        (f"-{settings.url_retention_days}",),
    )
    conn.commit()


def save_run(
    articles_received: int,
    articles_after_dedup: int,
    new_articles: list[NormalizedArticle],
    insights: list[Insight],
) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO pipeline_runs (articles_received, articles_after_dedup, new_articles, insights_generated) VALUES (?,?,?,?)",
        (articles_received, articles_after_dedup, len(new_articles), len(insights)),
    )
    run_id = cur.lastrowid

    for a in new_articles:
        conn.execute(
            "INSERT INTO articles (run_id, title, url, source, published_at, content) VALUES (?,?,?,?,?,?)",
            (run_id, a.title, a.url, a.source,
             a.published_at.isoformat() if a.published_at else None,
             a.content[:2000]),
        )

    for ins in insights:
        conn.execute(
            "INSERT INTO insights (run_id, title, summary, relevance, sources, tags) VALUES (?,?,?,?,?,?)",
            (run_id, ins.title, ins.summary, ins.relevance,
             json.dumps(ins.sources), json.dumps(ins.tags)),
        )

    conn.commit()
    conn.close()
    return run_id
