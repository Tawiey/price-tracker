import sqlite3
import os
from contextlib import contextmanager

DATABASE_PATH = "data/prices.db"


@contextmanager
def _get_conn():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                store       TEXT    NOT NULL,
                title       TEXT    NOT NULL,
                price       REAL    NOT NULL,
                currency    TEXT    NOT NULL DEFAULT 'ZAR',
                url         TEXT,
                scraped_at  TEXT    NOT NULL,
                search_query TEXT
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_store_title ON price_history(store, title)"
        )


def save_prices(products):
    with _get_conn() as conn:
        conn.executemany(
            """
            INSERT INTO price_history
                (store, title, price, currency, url, scraped_at, search_query)
            VALUES
                (:store, :title, :price, :currency, :url, :scraped_at, :search_query)
            """,
            products,
        )


def get_latest_prices():
    """Return one row per (store, title) with the most recent price plus all-time stats."""
    with _get_conn() as conn:
        return conn.execute(
            """
            SELECT
                p1.store,
                p1.title,
                p1.price,
                p1.currency,
                p1.url,
                p1.scraped_at,
                stats.min_price,
                stats.max_price,
                stats.record_count
            FROM price_history p1
            JOIN (
                SELECT store, title,
                       MIN(price)  AS min_price,
                       MAX(price)  AS max_price,
                       COUNT(*)    AS record_count,
                       MAX(scraped_at) AS last_seen
                FROM price_history
                GROUP BY store, title
            ) stats ON p1.store = stats.store
                    AND p1.title = stats.title
                    AND p1.scraped_at = stats.last_seen
            ORDER BY p1.currency, p1.price ASC
            """
        ).fetchall()


def get_price_history(store, title):
    with _get_conn() as conn:
        return conn.execute(
            """
            SELECT price, currency, scraped_at
            FROM price_history
            WHERE store = ? AND title = ?
            ORDER BY scraped_at ASC
            """,
            (store, title),
        ).fetchall()


def get_scrape_count():
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(DISTINCT DATE(scraped_at)) AS n FROM price_history"
        ).fetchone()
        return row["n"] if row else 0


def get_last_updated():
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(scraped_at) AS ts FROM price_history"
        ).fetchone()
        return row["ts"][:10] if row and row["ts"] else None
