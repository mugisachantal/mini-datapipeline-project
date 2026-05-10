-- Drop in reverse dependency order
DROP TABLE IF EXISTS patent_examiner CASCADE;
DROP TABLE IF EXISTS patent_assignee CASCADE;
DROP TABLE IF EXISTS patent_inventor CASCADE;
DROP TABLE IF EXISTS applications    CASCADE;
DROP TABLE IF EXISTS patent_abstracts CASCADE;
DROP TABLE IF EXISTS inventors       CASCADE;
DROP TABLE IF EXISTS companies       CASCADE;
DROP TABLE IF EXISTS locations       CASCADE;
DROP TABLE IF EXISTS patents         CASCADE;

-- 1. Locations
CREATE TABLE locations (
    location_id      TEXT ,
    disambig_city    TEXT,
    disambig_state   TEXT,
    disambig_country TEXT,
    latitude         NUMERIC,
    longitude        NUMERIC,
    county           TEXT,
    state_fips       TEXT,
    county_fips      TEXT
);

-- 2. Patents
CREATE TABLE patents (
    patent_id    TEXT  ,
    title        TEXT,
    patent_type  TEXT,
    wipo_kind    TEXT,
    num_claims   INTEGER,
    withdrawn    TEXT, -- Keeping as text to avoid boolean cast errors during bulk load
    filename     TEXT,
    filing_date  DATE,
    year         INTEGER
);

-- 3. Patent Abstracts
CREATE TABLE patent_abstracts (
    patent_id TEXT,
    abstract  TEXT
);

-- 4. Applications
CREATE TABLE applications (
    application_id          TEXT ,
    patent_id               TEXT ,
    patent_application_type TEXT,
    filing_date             DATE,
    filing_year             INTEGER,
    series_code             TEXT,
    rule_47_flag            TEXT
);

-- 5. Inventors
CREATE TABLE inventors (
    inventor_id TEXT  ,
    name        TEXT,
    gender_code TEXT,
    location_id TEXT 
);

-- 6. Companies
CREATE TABLE companies (
    company_id    TEXT ,
    name          TEXT,
    assignee_type TEXT,
    location_id   TEXT 
);

-- 7. Patent-Inventor (Junction)
CREATE TABLE patent_inventor (
    patent_id   TEXT ,
    inventor_id TEXT 
);

-- 8. Patent-Assignee (Junction)
CREATE TABLE patent_assignee (
    patent_id  TEXT ,
    company_id TEXT 
);

-- 9. Examiners
CREATE TABLE patent_examiner (
    patent_id      TEXT ,
    examiner_name  TEXT,
    examiner_role  TEXT,
    art_group      TEXT
);

-- Increase memory to use RAM instead of Disk for sorting 9.4M rows
SET maintenance_work_mem = '1GB';

-- ==========================================
-- 1. PRIMARY KEYS (Rebuilds the foundation)
-- ==========================================
ALTER TABLE locations       ADD PRIMARY KEY (location_id);
ALTER TABLE patents         ADD PRIMARY KEY (patent_id);
ALTER TABLE applications    ADD PRIMARY KEY (application_id);
ALTER TABLE inventors       ADD PRIMARY KEY (inventor_id);
ALTER TABLE companies       ADD PRIMARY KEY (company_id);
ALTER TABLE patent_inventor ADD PRIMARY KEY (patent_id, inventor_id);
ALTER TABLE patent_assignee ADD PRIMARY KEY (patent_id, company_id);

-- ==========================================
-- 2. FOREIGN KEYS (Restores relationships)
-- ==========================================

-- Patent Abstracts -> Patents
ALTER TABLE patent_abstracts 
    ADD CONSTRAINT fk_abstract_patent FOREIGN KEY (patent_id) 
    REFERENCES patents(patent_id) ON DELETE CASCADE;

-- Applications -> Patents
ALTER TABLE applications 
    ADD CONSTRAINT fk_app_patent FOREIGN KEY (patent_id) 
    REFERENCES patents(patent_id) ON DELETE CASCADE;

-- Inventors -> Locations
ALTER TABLE inventors 
    ADD CONSTRAINT fk_inv_loc FOREIGN KEY (location_id) 
    REFERENCES locations(location_id);

-- Companies -> Locations
ALTER TABLE companies 
    ADD CONSTRAINT fk_comp_loc FOREIGN KEY (location_id) 
    REFERENCES locations(location_id);

-- Patent-Inventor Junction -> Parents
ALTER TABLE patent_inventor 
    ADD CONSTRAINT fk_pi_patent FOREIGN KEY (patent_id) 
    REFERENCES patents(patent_id) ON DELETE CASCADE;

ALTER TABLE patent_inventor 
    ADD CONSTRAINT fk_pi_inventor FOREIGN KEY (inventor_id) 
    REFERENCES inventors(inventor_id) ON DELETE CASCADE;

-- Patent-Assignee Junction -> Parents
ALTER TABLE patent_assignee 
    ADD CONSTRAINT fk_pa_patent FOREIGN KEY (patent_id) 
    REFERENCES patents(patent_id) ON DELETE CASCADE;

ALTER TABLE patent_assignee 
    ADD CONSTRAINT fk_pa_company FOREIGN KEY (company_id) 
    REFERENCES companies(company_id) ON DELETE CASCADE;

-- Patent Examiner -> Patents
ALTER TABLE patent_examiner 
    ADD CONSTRAINT fk_exam_patent FOREIGN KEY (patent_id) 
    REFERENCES patents(patent_id) ON DELETE CASCADE;

-- ==========================================
-- 3. ADDITIONAL INDEXES
-- ==========================================
CREATE INDEX idx_application_id ON applications(application_id);
CREATE INDEX idx_app_patent_id ON applications(patent_id);
CREATE INDEX idx_exam_patent_id ON patent_examiner(patent_id);

CREATE INDEX idx_patents_year ON patents(year);
CREATE INDEX idx_patents_filing_date ON patents(filing_date);

-- Join support for inventors
CREATE INDEX idx_inventors_location_id ON inventors(location_id);

-- Join support for companies
CREATE INDEX idx_companies_location_id ON companies(location_id);

-- Patent-Inventor Junction
CREATE INDEX idx_pi_inventor_id ON patent_inventor(inventor_id);
CREATE INDEX idx_pi_patent_id ON patent_inventor(patent_id);

-- Patent-Assignee Junction
CREATE INDEX idx_pa_company_id ON patent_assignee(company_id);
CREATE INDEX idx_pa_patent_id ON patent_assignee(patent_id);

-- Patent-Inventor Junction
CREATE INDEX idx_pi_inventor_id ON patent_inventor(inventor_id);
CREATE INDEX idx_pi_patent_id ON patent_inventor(patent_id);

-- Patent-Assignee Junction
CREATE INDEX idx_pa_company_id ON patent_assignee(company_id);
CREATE INDEX idx_pa_patent_id ON patent_assignee(patent_id);










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