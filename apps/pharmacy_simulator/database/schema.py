"""SQLite schema for patient records."""

PATIENTS_TABLE = """
CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL DEFAULT '',
    last_name TEXT NOT NULL DEFAULT '',
    middle_name TEXT NOT NULL DEFAULT '',
    dob TEXT NOT NULL DEFAULT '',
    gender TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    address_line1 TEXT NOT NULL DEFAULT '',
    address_line2 TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    province TEXT NOT NULL DEFAULT '',
    postal_code TEXT NOT NULL DEFAULT '',
    health_card TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,
    animal INTEGER NOT NULL DEFAULT 0,
    deceased_date TEXT NOT NULL DEFAULT '',
    delivery_type TEXT NOT NULL DEFAULT '',
    delivery_route TEXT NOT NULL DEFAULT '',
    price_group TEXT NOT NULL DEFAULT '',
    comments TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    last_modified_at TEXT NOT NULL
);
"""

FAMILY_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS family_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    member_patient_id TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL DEFAULT '',
    relationship TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);
"""

INDEX_FAMILY_PATIENT = """
CREATE INDEX IF NOT EXISTS idx_family_patient_id ON family_members(patient_id);
"""

PATIENT_INSURANCE_TABLE = """
CREATE TABLE IF NOT EXISTS patient_insurance (
    patient_id TEXT PRIMARY KEY,
    plan_type TEXT NOT NULL DEFAULT '',
    carrier TEXT NOT NULL DEFAULT '',
    policy_number TEXT NOT NULL DEFAULT '',
    group_number TEXT NOT NULL DEFAULT '',
    expiry_date TEXT NOT NULL DEFAULT '',
    relationship TEXT NOT NULL DEFAULT '',
    cardholder_name TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);
"""

PATIENT_ALLERGIES_TABLE = """
CREATE TABLE IF NOT EXISTS patient_allergies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    allergy_name TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    date_reported TEXT NOT NULL DEFAULT '',
    comments TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);
"""

INDEX_ALLERGIES_PATIENT = """
CREATE INDEX IF NOT EXISTS idx_allergies_patient_id ON patient_allergies(patient_id);
"""

PATIENT_COMMUNICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS patient_communications (
    patient_id TEXT PRIMARY KEY,
    language TEXT NOT NULL DEFAULT '',
    refill_type TEXT NOT NULL DEFAULT '',
    pickup_preference TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);
"""

COMMUNICATION_METHODS_TABLE = """
CREATE TABLE IF NOT EXISTS communication_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    message_type TEXT NOT NULL DEFAULT '',
    notification_type TEXT NOT NULL DEFAULT '',
    phone_number TEXT NOT NULL DEFAULT '',
    email_address TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);
"""

INDEX_COMM_METHODS_PATIENT = """
CREATE INDEX IF NOT EXISTS idx_comm_methods_patient_id ON communication_methods(patient_id);
"""

INBOX_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS inbox_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL DEFAULT 'Upload',
    subject TEXT NOT NULL DEFAULT '',
    sender TEXT NOT NULL DEFAULT '',
    file_name TEXT NOT NULL DEFAULT '',
    file_path TEXT NOT NULL DEFAULT '',
    received_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'New'
);
"""

INDEX_INBOX_RECEIVED = """
CREATE INDEX IF NOT EXISTS idx_inbox_received_at ON inbox_documents(received_at DESC);
"""

SCHEMA_STATEMENTS = (
    PATIENTS_TABLE,
    FAMILY_MEMBERS_TABLE,
    INDEX_FAMILY_PATIENT,
    PATIENT_INSURANCE_TABLE,
    PATIENT_ALLERGIES_TABLE,
    INDEX_ALLERGIES_PATIENT,
    PATIENT_COMMUNICATIONS_TABLE,
    COMMUNICATION_METHODS_TABLE,
    INDEX_COMM_METHODS_PATIENT,
    INBOX_DOCUMENTS_TABLE,
    INDEX_INBOX_RECEIVED,
)
