"""
Synthetic e-commerce product review dataset generator.

Produces a CSV with the same schema/shape as the reference dataset
(synthetic_ecommerce_reviews_300k.csv), but with a fresh, original
product catalog and freshly generated review text. Distributions
(rating, sentiment, price ranges, date ranges, helpful-vote counts)
are modeled on the reference file's observed statistics.

Usage:
    python generate_dataset.py --rows 8000 --out reviews.csv
"""

import argparse
import csv
import random
from datetime import date, timedelta

random.seed(42)

# ---------------------------------------------------------------------------
# Product catalog (original names/brands, same category shape as reference)
# ---------------------------------------------------------------------------
PRODUCTS = [
    # (name, brand, manufacturer, category, primaryCategory, price_min, price_max)
    ("Orbiton Tab Air 11",        "Orbiton",  "Orbiton Devices",   "Tablets",           "Electronics", 210, 290),
    ("Orbiton Tab Mini 8",        "Orbiton",  "Orbiton Devices",   "Tablets",           "Electronics", 125, 175),
    ("Halcyon Doorbell X",        "Halcyon",  "Halcyon Home",      "Smart Home",        "Electronics", 82,  116),
    ("Halcyon Cam Outdoor",       "Halcyon",  "Halcyon Home",      "Smart Home",        "Electronics", 58,  82),
    ("Drakewell K6 Mechanical",   "Drakewell","Drakewell Computing","Keyboards",        "Computers",   52,  76),
    ("Drakewell Glide S1",        "Drakewell","Drakewell Computing","Mice",             "Computers",   34,  50),
    ("Lumacore View 25",          "Lumacore", "Lumacore Display",  "Monitors",          "Computers",   130, 186),
    ("Lumacore View 28Q",         "Lumacore", "Lumacore Display",  "Monitors",          "Computers",   198, 280),
    ("Sonivo Hush Pro",           "Sonivo",   "Sonivo Audio",      "Headphones",        "Electronics", 165, 232),
    ("Sonivo Breeze 2",           "Sonivo",   "Sonivo Audio",      "Headphones",        "Electronics", 106, 150),
    ("Nimbus Cast Stick",         "Nimbus",   "Nimbus Devices",    "Streaming Devices", "Electronics", 32,  46),
    ("Nimbus Cast Box Pro",       "Nimbus",   "Nimbus Devices",    "Streaming Devices", "Electronics", 65,  92),
    ("Echofield Hub One",         "Echofield","Echofield Labs",    "Smart Speakers",    "Electronics", 73,  104),
    ("Echofield Mini",            "Echofield","Echofield Labs",    "Smart Speakers",    "Electronics", 40,  57),
    ("Bindly Page Light",         "Bindly",   "Bindly Reading Co.","E-Readers",         "Electronics", 90,  128),
    ("Bindly Page Glow HD",       "Bindly",   "Bindly Reading Co.","E-Readers",         "Electronics", 115, 163),
    ("Ampera 20K PowerBank",      "Ampera",   "Ampera Mobility",   "Chargers & Power",  "Electronics", 45,  64),
    ("Ampera 65W Fast Charger",   "Ampera",   "Ampera Mobility",   "Chargers & Power",  "Electronics", 37,  53),
    ("Gridlynx Smart Plug 4-Pack","Gridlynx", "Gridlynx Systems",  "Smart Home",        "Electronics", 24,  34),
    ("Gridlynx Light Strip Pro",  "Gridlynx", "Gridlynx Systems",  "Smart Home",        "Electronics", 32,  46),
]

FIRST_NAMES = ["Ananya", "Priya", "Meera", "Aarav", "Kabir", "Yash", "Sana", "Ishita",
               "Tanya", "Riya", "Nisha", "Simran", "Arjun", "Neha", "Rohan", "Vikram",
               "Diya", "Kavya", "Aditya", "Zara"]
LAST_NAMES = ["Iyer", "Nair", "Pillai", "Jain", "Kapoor", "Bose", "Gupta", "Sharma",
              "Mehta", "Roy", "Ghosh", "Saha", "Mishra", "Reddy", "Rao", "Singh",
              "Chopra", "Bhat", "Menon", "Das"]

# Sentence pools, mirroring the reference dataset's templated style
OPENERS = [
    "The device handles everyday use without any trouble.",
    "The product arrived in good condition and set up quickly.",
    "Build quality feels solid for the price point.",
    "First impressions were positive right out of the box.",
    "It integrated easily with the rest of my setup.",
    "The design is compact and looks good on a shelf or desk.",
]
FEATURE_LINES = [
    "The {cat} features are practical and easy to use day to day.",
    "Battery life has been {battery_adj} for my usage pattern.",
    "The display has {display_adj} clarity for the price.",
    "The sound quality is {sound_adj} for casual use.",
    "Setup took only a few minutes and the app worked as expected.",
    "It connects reliably and hasn't dropped a connection so far.",
]
MID_POSITIVE = [
    "Overall, this has been a great purchase.",
    "It exceeded my expectations for something in this price range.",
    "The difference compared to my old device is noticeable.",
    "It does what I need without unnecessary extra fuss.",
    "I've been happy with it after a few weeks of regular use.",
]
MID_NEUTRAL = [
    "After some everyday use, it feels functional but not exceptional.",
    "It gets the job done, though nothing about it stands out.",
    "I have not found a major deal-breaker, but nothing wows me either.",
    "It's a reasonable option if you're not looking for premium features.",
]
MID_NEGATIVE = [
    "The experience has been frustrating and inconsistent.",
    "I ran into more issues than I expected for this price.",
    "It has not held up as well as I had hoped after regular use.",
    "There are a few rough edges that make it hard to recommend.",
]
CLOSERS_POSITIVE = [
    "I tested it over multiple days before writing this review.",
    "My household uses it almost every day.",
    "I would buy this again without hesitation.",
    "Would recommend it to anyone comparing options in this category.",
]
CLOSERS_NEUTRAL = [
    "I would suggest comparing a few options first.",
    "Your experience may vary depending on how you plan to use it.",
    "It's worth checking current reviews before deciding.",
]
CLOSERS_NEGATIVE = [
    "I would not buy this model again.",
    "I'm considering returning it if things don't improve.",
    "Would not recommend it at the current price.",
]

TITLES_BY_SENTIMENT = {
    "positive": ["Great purchase", "Better than expected", "Excellent value", "Very impressed",
                 "Highly recommended", "Happy with it", "Solid product"],
    "neutral":  ["Mixed results", "It is okay", "Decent but basic", "Average experience",
                 "Does the job"],
    "negative": ["Disappointed", "Too many issues", "Not worth the price",
                 "Frustrating to use", "Would not recommend"],
}

RATING_BY_SENTIMENT = {
    "positive": [4, 5],
    "neutral": [3],
    "negative": [1, 2],
}

# Overall sentiment mix modeled on the reference file (~63% pos, 22% neg, 15% neutral)
SENTIMENT_WEIGHTS = [("positive", 0.63), ("neutral", 0.15), ("negative", 0.22)]


def weighted_choice(pairs):
    r = random.random()
    upto = 0
    for val, w in pairs:
        upto += w
        if r <= upto:
            return val
    return pairs[-1][0]


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def make_username(used: set) -> str:
    for _ in range(20):
        name = f"{random.choice(FIRST_NAMES).lower()}{random.choice(LAST_NAMES).lower()}{random.randint(100, 999)}"
        if name not in used:
            used.add(name)
            return name
    return f"user{random.randint(10000, 99999)}"


def make_review_text(category: str, sentiment: str) -> str:
    cat_lower = category.lower()
    opener = random.choice(OPENERS)
    feature = random.choice(FEATURE_LINES).format(
        cat=cat_lower,
        battery_adj=random.choice(["excellent", "solid", "about what I expected", "a bit weak"]),
        display_adj=random.choice(["impressive", "decent", "uneven", "sharp"]),
        sound_adj=random.choice(["great", "fine", "underwhelming", "surprisingly good"]),
    )
    if sentiment == "positive":
        mid = random.choice(MID_POSITIVE)
        closer = random.choice(CLOSERS_POSITIVE)
    elif sentiment == "neutral":
        mid = random.choice(MID_NEUTRAL)
        closer = random.choice(CLOSERS_NEUTRAL)
    else:
        mid = random.choice(MID_NEGATIVE)
        closer = random.choice(CLOSERS_NEGATIVE)
    return f"{opener} {feature} {mid} {closer}"


def generate(rows: int, out_path: str):
    start_added = date(2023, 1, 1)
    end_added = date(2026, 9, 15)
    used_usernames = set()

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "dateAdded", "dateUpdated", "name", "brand", "manufacturer",
            "categories", "primaryCategories", "reviews.date", "reviews.didPurchase",
            "reviews.doRecommend", "reviews.numHelpful", "reviews.rating",
            "reviews.title", "reviews.text", "reviews.username", "sentiment",
            "productPrice",
        ])

        for i in range(1, rows + 1):
            product = random.choice(PRODUCTS)
            name, brand, manufacturer, category, primary_cat, pmin, pmax = product
            date_added = random_date(start_added, end_added)
            date_updated = date_added  # mirrors reference (always equal)

            review_date = date_added - timedelta(days=random.randint(0, 25))
            if review_date < start_added:
                review_date = date_added

            sentiment = weighted_choice(SENTIMENT_WEIGHTS)
            rating = random.choice(RATING_BY_SENTIMENT[sentiment])
            did_purchase = random.random() < 0.93
            do_recommend = sentiment != "negative" and random.random() < 0.92
            num_helpful = min(41, max(0, int(random.expovariate(1 / 2.8))))
            title = random.choice(TITLES_BY_SENTIMENT[sentiment])
            text = make_review_text(category, sentiment)
            username = make_username(used_usernames)
            price = round(random.uniform(pmin, pmax), 2)

            writer.writerow([
                f"syn2-{i:07d}",
                date_added.isoformat(),
                date_updated.isoformat(),
                name, brand, manufacturer,
                f"{category}; Electronics & Accessories",
                primary_cat,
                review_date.isoformat(),
                str(did_purchase).lower(),
                str(do_recommend).lower(),
                num_helpful,
                rating,
                title,
                text,
                username,
                sentiment,
                f"{price:.2f}",
            ])

    print(f"Wrote {rows} rows to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=8000)
    parser.add_argument("--out", type=str, default="reviews.csv")
    args = parser.parse_args()
    generate(args.rows, args.out)
