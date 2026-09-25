"""
Synthetic e-commerce demo backend.

Loads data/reviews.csv into memory at startup and exposes a small
REST API plus a simple storefront frontend that consumes it.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000
"""

import csv
import os
from collections import defaultdict
from statistics import mean

from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "reviews.csv")

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    # Allow the /reviews API to be hit from other origins/tools without
    # needing the flask-cors package as a dependency.
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

REVIEWS = []       # list of dicts, one per review row
PRODUCTS = {}       # name -> aggregated product info
SLUG_TO_NAME = {}   # url-friendly slug -> exact product name


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("&", "and")


def load_data():
    global REVIEWS, PRODUCTS
    REVIEWS = []
    products = defaultdict(lambda: {
        "name": None, "brand": None, "manufacturer": None,
        "categories": None, "primaryCategories": None,
        "prices": [], "ratings": [], "review_count": 0,
    })

    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            review = {
                "id": row["id"],
                "productName": row["name"],
                "brand": row["brand"],
                "manufacturer": row["manufacturer"],
                "categories": row["categories"],
                "primaryCategory": row["primaryCategories"],
                "date": row["reviews.date"],
                "didPurchase": row["reviews.didPurchase"] == "true",
                "doRecommend": row["reviews.doRecommend"] == "true",
                "numHelpful": int(row["reviews.numHelpful"]),
                "rating": int(row["reviews.rating"]),
                "title": row["reviews.title"],
                "text": row["reviews.text"],
                "username": row["reviews.username"],
                "sentiment": row["sentiment"],
                "productPrice": float(row["productPrice"]),
            }
            REVIEWS.append(review)

            p = products[row["name"]]
            p["name"] = row["name"]
            p["brand"] = row["brand"]
            p["manufacturer"] = row["manufacturer"]
            p["categories"] = row["categories"]
            p["primaryCategories"] = row["primaryCategories"]
            p["prices"].append(float(row["productPrice"]))
            p["ratings"].append(int(row["reviews.rating"]))
            p["review_count"] += 1

    PRODUCTS = {}
    for name, p in products.items():
        histogram = {str(star): p["ratings"].count(star) for star in range(1, 6)}
        PRODUCTS[name] = {
            "name": p["name"],
            "slug": slugify(p["name"]),
            "brand": p["brand"],
            "manufacturer": p["manufacturer"],
            "categories": p["categories"],
            "primaryCategories": p["primaryCategories"],
            "avgPrice": round(mean(p["prices"]), 2),
            "minPrice": round(min(p["prices"]), 2),
            "maxPrice": round(max(p["prices"]), 2),
            "avgRating": round(mean(p["ratings"]), 2),
            "reviewCount": p["review_count"],
            "ratingHistogram": histogram,
        }

    global SLUG_TO_NAME
    SLUG_TO_NAME = {p["slug"]: name for name, p in PRODUCTS.items()}

    print(f"Loaded {len(REVIEWS)} reviews across {len(PRODUCTS)} products.")


# ---------------------------------------------------------------------------
# Routes: frontend (server-rendered pages)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    stats = {
        "total_reviews": len(REVIEWS),
        "total_products": len(PRODUCTS),
        "avg_rating": round(mean(r["rating"] for r in REVIEWS), 2) if REVIEWS else 0,
    }
    return render_template("index.html", stats=stats)


@app.route("/product/<slug>")
def product_detail(slug):
    name = SLUG_TO_NAME.get(slug)
    if not name:
        return render_template("404.html", slug=slug), 404
    product = PRODUCTS[name]
    return render_template("product.html", product=product)


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html", slug=None), 404


# ---------------------------------------------------------------------------
# Routes: API
# ---------------------------------------------------------------------------
@app.route("/products")
def get_products():
    """List all products with aggregated rating/price info."""
    items = list(PRODUCTS.values())
    category = request.args.get("category")
    if category:
        items = [p for p in items if p["primaryCategories"].lower() == category.lower()]
    q = request.args.get("q")
    if q:
        q = q.lower()
        items = [p for p in items if q in p["name"].lower() or q in p["brand"].lower()]
    items.sort(key=lambda p: p["name"])
    return jsonify({"count": len(items), "products": items})


@app.route("/reviews")
def get_reviews():
    """
    Return reviews, with optional filtering and pagination.

    Query params:
      product     - exact product name filter
      category    - primaryCategories filter (Electronics / Computers)
      rating      - exact rating filter (1-5)
      sentiment   - positive / neutral / negative
      min_rating  - minimum rating (inclusive)
      page        - page number, default 1
      page_size   - results per page, default 25 (max 200)
    """
    results = REVIEWS

    product = request.args.get("product")
    if product:
        results = [r for r in results if r["productName"].lower() == product.lower()]

    category = request.args.get("category")
    if category:
        results = [r for r in results if r["primaryCategory"].lower() == category.lower()]

    rating = request.args.get("rating", type=int)
    if rating:
        results = [r for r in results if r["rating"] == rating]

    min_rating = request.args.get("min_rating", type=int)
    if min_rating:
        results = [r for r in results if r["rating"] >= min_rating]

    sentiment = request.args.get("sentiment")
    if sentiment:
        results = [r for r in results if r["sentiment"].lower() == sentiment.lower()]

    total = len(results)
    page = max(1, request.args.get("page", default=1, type=int))
    page_size = min(200, max(1, request.args.get("page_size", default=25, type=int)))
    start = (page - 1) * page_size
    end = start + page_size
    page_items = results[start:end]

    return jsonify({
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
        "reviews": page_items,
    })


@app.route("/reviews/<review_id>")
def get_review(review_id):
    for r in REVIEWS:
        if r["id"] == review_id:
            return jsonify(r)
    return jsonify({"error": "review not found"}), 404


@app.route("/categories")
def get_categories():
    cats = sorted({r["primaryCategory"] for r in REVIEWS})
    return jsonify({"categories": cats})


if __name__ == "__main__":
    load_data()
    app.run(debug=True, port=5000)
else:
    # also load when imported (e.g. by a WSGI server)
    load_data()
