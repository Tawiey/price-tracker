import logging
import os
from urllib.parse import unquote

from flask import Flask, jsonify, redirect, render_template, request, url_for

from . import database
from .scrapers import amazon, takealot

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates")


@app.before_request
def _ensure_db():
    database.init_db()


@app.route("/")
def index():
    products = database.get_latest_prices()
    last_updated = database.get_last_updated()
    scrape_count = database.get_scrape_count()
    return render_template(
        "index.html",
        products=products,
        last_updated=last_updated or "Never",
        scrape_count=scrape_count,
        is_vercel=bool(os.environ.get("VERCEL")),
    )


@app.route("/scrape", methods=["POST"])
def scrape():
    from config import (
        AMAZON_SEARCHES,
        MAX_PRICE_ZAR,
        TAKEALOT_SEARCHES,
    )

    all_products = []

    for query in TAKEALOT_SEARCHES:
        found = takealot.scrape(query, max_price=MAX_PRICE_ZAR)
        logger.info("Takealot %r → %d products", query, len(found))
        all_products.extend(found)

    for query in AMAZON_SEARCHES:
        found = amazon.scrape(query, max_price=MAX_PRICE_ZAR)
        logger.info("Amazon %r → %d products", query, len(found))
        all_products.extend(found)

    # Deduplicate: keep first occurrence of each (store, title) pair
    seen: set[tuple] = set()
    unique = []
    for p in all_products:
        key = (p["store"], p["title"])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    if unique:
        database.save_prices(unique)
        logger.info("Saved %d unique products", len(unique))

    return redirect(url_for("index"))


@app.route("/api/history")
def price_history():
    store = request.args.get("store", "")
    title = unquote(request.args.get("title", ""))
    if not store or not title:
        return jsonify({"error": "store and title are required"}), 400

    rows = database.get_price_history(store, title)
    return jsonify(
        [
            {
                "price": row["price"],
                "currency": row["currency"],
                "date": row["scraped_at"][:10],
            }
            for row in rows
        ]
    )
