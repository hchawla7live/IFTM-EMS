
-- =====================================================
-- IFTM EMS
-- Initial Master Data
-- Version: 0.1
-- =====================================================

-- ENQUIRY SOURCES

INSERT OR IGNORE INTO enquiry_sources (source_name)
VALUES
    ('Phone'),
    ('Website'),
    ('WhatsApp'),
    ('Social Media'),
    ('Walk-in'),
    ('Educational Fair'),
    ('Faculty Referral'),
    ('School Referral'),
    ('Progression'),
    ('Other');


-- ACADEMIC PROGRAMMES

-- Department of Computer Science and Engineering

INSERT OR IGNORE INTO programmes
    (programme_name, department_name)
VALUES
    ('B.Tech CSE', 'Department of Computer Science and Engineering'),
    ('B.Tech AI', 'Department of Computer Science and Engineering'),
    ('M.Tech CSE', 'Department of Computer Science and Engineering'),
    ('PhD CSE', 'Department of Computer Science and Engineering');


-- Department of Computer Applications

INSERT OR IGNORE INTO programmes
    (programme_name, department_name)
VALUES
    ('BCA', 'Department of Computer Applications'),
    ('MCA', 'Department of Computer Applications'),
    ('PGDCA', 'Department of Computer Applications');


-- =====================================================
-- END OF SEED DATA
-- =====================================================
