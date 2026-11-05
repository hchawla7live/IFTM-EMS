
-- =====================================================
-- IFTM EMS
-- Initial Database Schema
-- Database: SQLite
-- Version: 0.1
-- =====================================================

PRAGMA foreign_keys = ON;

-- 1. APPLICATION USERS
CREATE TABLE IF NOT EXISTS app_users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. ENQUIRY SOURCES
CREATE TABLE IF NOT EXISTS enquiry_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1))
);

-- 3. PROGRAMMES
CREATE TABLE IF NOT EXISTS programmes (
    programme_id INTEGER PRIMARY KEY AUTOINCREMENT,
    programme_name TEXT NOT NULL,
    department_name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    UNIQUE (programme_name, department_name)
);

-- 4. STUDENT MASTER
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_name TEXT NOT NULL,
    father_name TEXT NOT NULL,
    mobile_number TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,

    erp_student_unique_id TEXT UNIQUE,
    roll_number TEXT,

    student_type TEXT NOT NULL DEFAULT 'NEW_PROSPECT'
        CHECK (
            student_type IN (
                'NEW_PROSPECT',
                'EXISTING_STUDENT'
            )
        ),

    created_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by_user_id)
        REFERENCES app_users(user_id),

    CHECK (length(trim(student_name)) > 0),
    CHECK (length(trim(father_name)) > 0),
    CHECK (length(trim(mobile_number)) > 0),
    CHECK (length(trim(address)) > 0),
    CHECK (length(trim(city)) > 0)
);

-- 5. ENQUIRIES
CREATE TABLE IF NOT EXISTS enquiries (
    enquiry_id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    programme_id INTEGER,

    entered_by_user_id INTEGER NOT NULL,
    referrer_details TEXT,

    enquiry_status TEXT NOT NULL DEFAULT 'NEW',
    enquiry_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)
        REFERENCES students(student_id),

    FOREIGN KEY (source_id)
        REFERENCES enquiry_sources(source_id),

    FOREIGN KEY (programme_id)
        REFERENCES programmes(programme_id),

    FOREIGN KEY (entered_by_user_id)
        REFERENCES app_users(user_id)
);

-- 6. AUDIT LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,

    action_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES app_users(user_id)
);

-- =====================================================
-- DATABASE INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_student_mobile
    ON students(mobile_number);

CREATE INDEX IF NOT EXISTS idx_student_name
    ON students(student_name);

CREATE INDEX IF NOT EXISTS idx_enquiry_student
    ON enquiries(student_id);

CREATE INDEX IF NOT EXISTS idx_enquiry_source
    ON enquiries(source_id);

CREATE INDEX IF NOT EXISTS idx_enquiry_date
    ON enquiries(enquiry_date);


-- =====================================================
-- 7. CALLING ACTIVITIES
-- =====================================================

CREATE TABLE IF NOT EXISTS calling_activities (

    call_activity_id INTEGER PRIMARY KEY AUTOINCREMENT,

    enquiry_id INTEGER NOT NULL,

    call_datetime TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    call_outcome TEXT NOT NULL,

    remarks TEXT,

    next_follow_up_date TEXT,

    recorded_by_user_id INTEGER NOT NULL,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (enquiry_id)
        REFERENCES enquiries(enquiry_id),

    FOREIGN KEY (recorded_by_user_id)
        REFERENCES app_users(user_id),

    CHECK (
        call_outcome IN (
            'ANSWERED',
            'NO_ANSWER',
            'BUSY',
            'SWITCHED_OFF',
            'INVALID_NUMBER',
            'CALL_BACK_REQUESTED',
            'OTHER'
        )
    )
);


-- =====================================================
-- CALLING ACTIVITY INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_calling_enquiry
    ON calling_activities(enquiry_id);

CREATE INDEX IF NOT EXISTS idx_calling_follow_up
    ON calling_activities(next_follow_up_date);

CREATE INDEX IF NOT EXISTS idx_calling_datetime
    ON calling_activities(call_datetime);


-- =====================================================
-- END OF SCHEMA
-- =====================================================