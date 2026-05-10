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
    location_id      TEXT PRIMARY KEY,
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
    patent_id    TEXT PRIMARY KEY,
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
    patent_id TEXT REFERENCES patents(patent_id) ON DELETE CASCADE,
    abstract  TEXT
);

-- 4. Applications
CREATE TABLE applications (
    application_id          TEXT PRIMARY KEY,
    patent_id               TEXT REFERENCES patents(patent_id) ON DELETE CASCADE,
    patent_application_type TEXT,
    filing_date             DATE,
    filing_year             INTEGER,
    series_code             TEXT,
    rule_47_flag            TEXT
);

-- 5. Inventors
CREATE TABLE inventors (
    inventor_id TEXT  PRIMARY KEY,
    name        TEXT,
    gender_code TEXT,
    location_id TEXT REFERENCES locations(location_id)
);

-- 6. Companies
CREATE TABLE companies (
    company_id    TEXT PRIMARY KEY,
    name          TEXT,
    assignee_type TEXT,
    location_id   TEXT REFERENCES locations(location_id)
);

-- 7. Patent-Inventor (Junction)
CREATE TABLE patent_inventor (
    patent_id   TEXT REFERENCES patents(patent_id) ON DELETE CASCADE,
    inventor_id TEXT REFERENCES inventors(inventor_id) ON DELETE CASCADE,
    PRIMARY KEY (patent_id, inventor_id)
);

-- 8. Patent-Assignee (Junction)
CREATE TABLE patent_assignee (
    patent_id  TEXT REFERENCES patents(patent_id) ON DELETE CASCADE,
    company_id TEXT REFERENCES companies(company_id) ON DELETE CASCADE,
    PRIMARY KEY (patent_id, company_id)
);

-- 9. Examiners
CREATE TABLE patent_examiner (
    patent_id      TEXT REFERENCES patents(patent_id) ON DELETE CASCADE,
    examiner_name  TEXT,
    examiner_role  TEXT,
    art_group      TEXT
);
CREATE INDEX idx_application_id ON applications(application_id);