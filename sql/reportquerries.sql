- Q1: TOP INVENTORS — who has filed the most patents?
SELECT
    inv.name,
    inv.country,
    COUNT(pi.patent_id) AS patent_count
FROM inventors inv
JOIN patent_inventor pi ON inv.inventor_id = pi.inventor_id
GROUP BY inv.inventor_id, inv.name, inv.country
ORDER BY patent_count DESC
LIMIT 20;


-- Q2: TOP COMPANIES — which assignees own the most patents?
SELECT
    c.name,
    COUNT(pa.patent_id) AS patent_count
FROM companies c
JOIN patent_assignee pa ON c.company_id = pa.company_id
GROUP BY c.company_id, c.name
ORDER BY patent_count DESC
LIMIT 20;


-- Q3: TOP COUNTRIES — by number of patents filed
SELECT
    inv.country,
    COUNT(pi.patent_id) AS patent_count,
    ROUND(
        COUNT(pi.patent_id) * 100.0 /
        SUM(COUNT(pi.patent_id)) OVER(), 2
    ) AS share_pct
FROM inventors inv
JOIN patent_inventor pi ON inv.inventor_id = pi.inventor_id
WHERE inv.country NOT IN ('Unknown', '')
GROUP BY inv.country
ORDER BY patent_count DESC
LIMIT 20;


-- Q4: TRENDS OVER TIME — annual patent filing volume
SELECT
    year,
    COUNT(*) AS patents_filed,
    SUM(COUNT(*)) OVER (ORDER BY year) AS running_total
FROM patents
WHERE year BETWEEN 1976 AND 2024
GROUP BY year
ORDER BY year;


-- Q5: JOIN QUERY — patents enriched with inventor and company
SELECT
    p.patent_id,
    p.title,
    p.year,
    inv.name        AS inventor_name,
    inv.country,
    c.name          AS company_name
FROM patents p
JOIN patent_inventor pi  ON p.patent_id = pi.patent_id
JOIN inventors inv       ON pi.inventor_id = inv.inventor_id
LEFT JOIN patent_assignee pa ON p.patent_id = pa.patent_id
LEFT JOIN companies c    ON pa.company_id = c.company_id
WHERE p.year = 2023
LIMIT 5000;


-- Q6: CTE QUERY — top inventor per country (multi-step logic)
WITH inventor_totals AS (
    -- Step 1: count patents per inventor
    SELECT
        inv.inventor_id,
        inv.name,
        inv.country,
        COUNT(pi.patent_id) AS patent_count
    FROM inventors inv
    JOIN patent_inventor pi ON inv.inventor_id = pi.inventor_id
    WHERE inv.country NOT IN ('Unknown', '')
    GROUP BY inv.inventor_id, inv.name, inv.country
),
country_leaders AS (
    -- Step 2: rank inventors within each country
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY country
            ORDER BY patent_count DESC
        ) AS rn
    FROM inventor_totals
)
-- Step 3: keep only the top inventor from each country
SELECT name, country, patent_count
FROM country_leaders
WHERE rn = 1
ORDER BY patent_count DESC
LIMIT 30;


-- Q7: RANKING QUERY — inventors ranked with window functions
SELECT
    inv.name,
    inv.country,
    COUNT(pi.patent_id)                                       AS patent_count,
    RANK()        OVER (ORDER BY COUNT(pi.patent_id) DESC)   AS rank,
    DENSE_RANK()  OVER (ORDER BY COUNT(pi.patent_id) DESC)   AS dense_rank,
    PERCENT_RANK() OVER (ORDER BY COUNT(pi.patent_id) DESC)  AS pct_rank,
    NTILE(10)    OVER (ORDER BY COUNT(pi.patent_id) DESC)   AS decile
FROM inventors inv
JOIN patent_inventor pi ON inv.inventor_id = pi.inventor_id
GROUP BY inv.inventor_id, inv.name, inv.country
ORDER BY patent_count DESC
LIMIT 100;