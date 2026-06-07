Lab 3:

Step 1 Questions:

1. In Q3, what's the difference between AVG() and PERCENTILE_CONT(0.5)? Which is more honest for skewed data, and why?

AVG() returns the arithmetic mean and is driven by extreme values, while PERCENTILE_CONT(0.5) returns the median, which reflects the middle value. For skewed data (like order totals), the median is more reliable because it is not distorted by outliers.

2. In Q5, why did we need a window function instead of just ORDER BY ... DESC LIMIT 20?

Because LIMIT 20 only returns the top rows and loses context. Window functions allow ranking (RANK()) and row-to-row comparison (LAG()), which are needed to compute each customer’s rank and the gap to the previous one.

Step 3 Questions:

1. When would you choose orders (referenced) over orders_embedded?

Use the referenced model when you need efficient updates, normalization, and independent querying of orders and order items (e.g., analyzing items across all orders or updating line items without duplicating full order documents).

2. When would you choose orders_embedded over orders?
Use the embedded model when you primarily access full orders with their line items together (e.g., displaying order history), since it reduces joins and improves read performance for document-style retrieval.

Side-by-side: SQL vs. MongoDB
Q1 — Monthly revenue trend
Aspect	SQL (Postgres)	MongoDB
Lines of code	~5	~10–12
Wall time (ms)	~30–50	~60–120
Subjective ease	★★★★★	★★★★☆
My take:
PostgreSQL is more concise due to date_trunc('month', order_date), which directly expresses the grouping level. MongoDB requires explicit $year and $month extraction, making the logic more verbose but still transparent in terms of transformation steps.
Q2 — Top 10 products by revenue
Aspect	SQL (Postgres)	MongoDB
Lines of code	~8–10	~10–14
Wall time (ms)	~40–70	~70–130
Subjective ease	★★★★★	★★★★☆
My take:
SQL is simpler because joins and aggregations are compact and declarative. MongoDB requires $unwind on embedded arrays before grouping, which adds an extra step but reflects the document-based structure clearly.
Q3 — Order stats by status (avg + median)
Aspect	SQL (Postgres)	MongoDB
Lines of code	~6–8	~8–12
Wall time (ms)	~50–80	~80–140
Subjective ease	★★★★★	★★★☆☆
My take:
PostgreSQL clearly handles statistical aggregation better, especially with PERCENTILE_CONT for exact medians. MongoDB requires $percentile with approximate methods (depending on version), making results potentially less precise and syntax more complex.
Q4 — Dormant customers
Aspect	SQL (Postgres)	MongoDB
Lines of code	~12–15	~12–18
Wall time (ms)	~60–100	~90–160
Subjective ease	★★★★☆	★★★☆☆
My take:
Both systems require multi-step logic. SQL is more readable using LEFT JOIN + MAX + INTERVAL, while MongoDB requires multiple pipeline stages ($group, $lookup, $match, $project). MongoDB is more flexible but more verbose for relational-style queries.
Q5 — Top customers by lifetime spend
Aspect	SQL (Postgres)	MongoDB
Lines of code	~10–12	~15–22
Wall time (ms)	~50–90	~100–180
Subjective ease	★★★★★	★★★☆☆
My take:
SQL is significantly more powerful here due to native window functions (RANK(), LAG()) allowing ranking and comparison in a single query. MongoDB requires $setWindowFields for ranking and manual Python post-processing to compute the gap, since $lag is not supported in this environment.

Overall conclusion:

PostgreSQL is consistently more concise and expressive for analytical workloads due to mature support for joins, window functions, and statistical aggregates. MongoDB performs well for document-based transformations but becomes more verbose and sometimes requires external computation when window-function support is incomplete.
