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