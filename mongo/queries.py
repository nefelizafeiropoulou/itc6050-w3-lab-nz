import time
def timed(label, func):
    t = time.time()
    result = list(func())
    print(f"{label:35s} {(time.time() - t) * 1000:7.1f} ms")
    return result
from pymongo import MongoClient
from pprint import pprint
client = MongoClient("mongodb://itc6050:itc6050@localhost:27017/?authSource=admin")
db = client["shop_lab"]
# ──────────────────────────────────────────────────────────────
# Q1 — Monthly revenue trend
# Equivalent of: GROUP BY date_trunc('month', order_date)
# ──────────────────────────────────────────────────────────────
print("\n--- Q1: Monthly revenue ---")
q1 = db.orders.aggregate([
    {"$group": {
    "_id": {
    "year": {"$year": "$order_date"},
    "month": {"$month": "$order_date"},
},
"orders": {"$sum": 1},
"revenue": {"$sum": "$total"},
}},
{"$sort": {"_id.year": 1, "_id.month": 1}},
])
for row in list(q1)[:5]:
    pprint(row)
# ──────────────────────────────────────────────────────────────
# Q2 — Top 10 products by revenue
# HINT: use orders_embedded — $unwind the items array,
# then $group by product_id and $sort.
# ──────────────────────────────────────────────────────────────
print("\n--- Q2: Top 10 products by revenue ---")
q2 = db.orders_embedded.aggregate([
    {"$unwind": "$items"},
    {"$group": {
        "_id": {
            "product_id": "$items.product_id"
        },
        "total_qty": {"$sum": "$items.quantity"},
        "revenue": {
            "$sum": {
                "$multiply": ["$items.quantity", "$items.unit_price_at_sale"]
            }
        }
    }},
    {"$sort": {"revenue": -1}},
    {"$limit": 10}
])

for row in q2:
    pprint(row)

# ──────────────────────────────────────────────────────────────
# Q3 — Order count + avg + median by status
# HINT: $group with $count, $avg.
# Median in Mongo: use $percentile (Mongo 7+) or $bucketAuto.
# ──────────────────────────────────────────────────────────────
print("\n--- Q3: Order count + avg + median by status ---")
q3 = db.orders.aggregate([
    {"$group": {
        "_id": "$status",
        "order_count": {"$sum": 1},
        "avg_total": {"$avg": "$total"},
        "median_total": {
            "$percentile": {
                "input": "$total",
                "p": [0.5],
                "method": "approximate"
            }
        }
    }},
    {"$sort": {"_id": 1}}
])

for row in q3:
    pprint(row)

# ──────────────────────────────────────────────────────────────
# Q4 — Dormant customers (no order in 90 days)
# HINT: aggregate orders to find max(order_date) per customer,
# then $lookup against customer, then $match.
# ──────────────────────────────────────────────────────────────
print("\n--- Q4: Dormant customers ---")

from datetime import datetime, timedelta

cutoff = datetime.utcnow() - timedelta(days=90)

q4 = db.orders.aggregate([
    {"$group": {
        "_id": "$customer_id",
        "last_order_date": {"$max": "$order_date"}
    }},
    {"$lookup": {
        "from": "customer",
        "localField": "_id",
        "foreignField": "customer_id",
        "as": "customer"
    }},
    {"$unwind": "$customer"},
    {"$match": {
        "$or": [
            {"last_order_date": {"$lt": cutoff}},
            {"last_order_date": None}
        ]
    }},
    {"$project": {
        "_id": 0,
        "email": "$customer.email",
        "last_order_date": 1,
        "days_dormant": {
            "$dateDiff": {
                "startDate": "$last_order_date",
                "endDate": "$$NOW",
                "unit": "day"
            }
        }
    }},
    {"$sort": {"days_dormant": -1}}
])

for row in q4:
    pprint(row)

# ──────────────────────────────────────────────────────────────
# Q5 — Top 20 customers by lifetime spend
# Note: MongoDB doesn't have window functions — you'll need
# $setWindowFields (Mongo 5+) which is the closest equivalent.
# ──────────────────────────────────────────────────────────────
print("\n--- Q5: Top customers by lifetime spend ---")

q5 = db.orders.aggregate([
    {"$group": {
        "_id": "$customer_id",
        "lifetime_spend": {"$sum": "$total"}
    }},
    {"$lookup": {
        "from": "customer",
        "localField": "_id",
        "foreignField": "customer_id",
        "as": "customer"
    }},
    {"$unwind": "$customer"},

    {"$sort": {"lifetime_spend": -1}},

    {"$setWindowFields": {
        "sortBy": {"lifetime_spend": -1},
        "output": {
            "rank": {"$rank": {}}
        }
    }},

    {"$limit": 20}
])

results = list(q5)

# compute gap manually
for i, row in enumerate(results):
    if i == 0:
        row["gap_to_previous"] = None
    else:
        row["gap_to_previous"] = (
            results[i-1]["lifetime_spend"] - row["lifetime_spend"]
        )

for row in results:
    pprint({
        "rank": row["rank"],
        "email": row["customer"]["email"],
        "lifetime_spend": row["lifetime_spend"],
        "gap_to_previous": row["gap_to_previous"]
    })