# NovaCart — synthetic e-commerce demo

A small e-commerce demo with a synthetic product-review dataset in the
backend and a `/reviews` API endpoint you can hit directly, plus a simple
storefront UI that consumes it.

## What's included

```
ecommerce_project/
├── .vscode/
│   ├── launch.json           # F5 to run/debug app.py
│   └── settings.json
├── data/
│   ├── generate_dataset.py   # regenerate/resize the synthetic dataset
│   └── reviews.csv           # 8,000 generated reviews (20 products)
├── backend/
│   ├── app.py                # Flask app: pages + JSON API
│   ├── requirements.txt
│   ├── templates/
│   │   ├── base.html         # shared layout: nav, search, cart drawer, footer
│   │   ├── index.html        # homepage: hero, filters, product grid
│   │   ├── product.html      # product detail page + reviews
│   │   └── 404.html
│   └── static/
│       ├── css/style.css
│       └── js/
│           ├── cart.js       # cart drawer + nav search (shared)
│           ├── home.js       # homepage filters/sort/grid
│           └── product.js    # review list, pagination, add-to-cart
└── README.md
```

The frontend is now a proper multi-page site rather than a single panel:
a homepage with a hero, category/rating filters and sort, and a real
`/product/<slug>` detail page per product with a rating breakdown,
filterable paginated reviews, and a working (localStorage-backed) cart
drawer + nav search — no build step, no framework, just Flask templates
and vanilla JS/CSS.

The dataset was generated to match the shape of the reference file you
uploaded: same columns (`id, dateAdded, dateUpdated, name, brand,
manufacturer, categories, primaryCategories, reviews.date,
reviews.didPurchase, reviews.doRecommend, reviews.numHelpful,
reviews.rating, reviews.title, reviews.text, reviews.username, sentiment,
productPrice`), a similar rating/sentiment mix (~63% positive / 15% neutral
/ 22% negative), similar price ranges per product, and templated review
text in the same style — but with an original 20-product catalog
(NovaCart-branded fictional electronics) and freshly generated text, so
it's not a copy of the source data.

## Running it

```bash
cd ecommerce_project/backend
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** for the storefront, or hit the API
directly.

## Opening it in VS Code

1. `code ecommerce_project` (or File → Open Folder) to open the whole
   project — not just `backend/` — so the `.vscode/` config and the
   `data/` folder are both visible.
2. Install the **Python** extension (Microsoft) if you don't have it —
   VS Code will prompt you the first time you open a `.py` file.
3. Open a terminal in VS Code (`` Ctrl+` `` / `` Cmd+` ``) and create a
   virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```
4. Select that environment as the interpreter: `Cmd/Ctrl+Shift+P` →
   "Python: Select Interpreter" → pick `.venv`.
5. Run it either way:
   - **Debugger (recommended)**: press `F5` — a launch config is already
     set up (`.vscode/launch.json`) to run `backend/app.py` with the
     debugger attached, so you can set breakpoints in the Flask routes.
   - **Terminal**: `cd backend && python app.py`
6. Open `http://localhost:5000` in your browser. Flask's debug/reload
   mode is on, so editing any `.py`, template, or you can just refresh
   the browser after editing `static/css/style.css` or the JS files
   (no reload needed for static assets).

Optional but handy extensions: **Live Server** isn't needed here (Flask
serves everything), but **Thunder Client** or **REST Client** are nice
for poking at `/reviews` and `/products` from inside VS Code instead of
the browser or curl.

## API

### `GET /reviews`
Returns paginated reviews. Query params (all optional):

| param        | description                                  |
|--------------|-----------------------------------------------|
| `product`    | exact product name, e.g. `Lumacore View 25`   |
| `category`   | `Electronics` or `Computers`                   |
| `rating`     | exact rating, 1–5                              |
| `min_rating` | minimum rating, inclusive                      |
| `sentiment`  | `positive` / `neutral` / `negative`            |
| `page`       | page number (default 1)                        |
| `page_size`  | results per page (default 25, max 200)         |

### `GET /products`
Also accepts `?q=` for a name/brand search (used by the nav search box).

```bash
curl "http://localhost:5000/reviews?category=Computers&min_rating=4&page=1"
```

Response shape:
```json
{
  "total": 1009,
  "page": 1,
  "page_size": 25,
  "total_pages": 41,
  "reviews": [ { "id": "...", "productName": "...", "rating": 4, "text": "...", ... } ]
}
```

### `GET /reviews/<id>`
A single review by id.

### `GET /products`
Aggregated per-product info (avg rating, price range, review count).
Optional `?category=` filter.

### `GET /categories`
List of the two top-level categories present in the data.

## Regenerating / resizing the dataset

```bash
cd ecommerce_project/data
python generate_dataset.py --rows 20000 --out reviews.csv
```

Then restart the backend — it loads `data/reviews.csv` into memory at
startup.

## Notes

- This is a self-contained demo: everything runs from CSV in memory, no
  database setup required.
- The Flask dev server is fine for local use; for anything beyond that,
  put it behind a production WSGI server (gunicorn, uwsgi, etc).
