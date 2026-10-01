from contextlib import contextmanager
from datetime import datetime
import csv
from pathlib import Path

import mysql.connector

from backend.config import Config

MEMORY_CLAIMS = []
MEMORY_ACTIVITY_LOGS = []
MEMORY_POLICIES = []
POLICY_DATA_PATH = Path(__file__).resolve().parent.parent / "database" / "policies.csv"


@contextmanager
def get_connection():
    connection = mysql.connector.connect(**Config.MYSQL_CONFIG)
    try:
        yield connection
    finally:
        connection.close()


def init_database():
    if Config.USE_MEMORY_DB:
        MEMORY_CLAIMS.clear()
        MEMORY_ACTIVITY_LOGS.clear()
        MEMORY_POLICIES.clear()
        if POLICY_DATA_PATH.exists():
            with POLICY_DATA_PATH.open(newline="", encoding="utf-8") as policy_file:
                MEMORY_POLICIES.extend(csv.DictReader(policy_file))
        return
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS activity_logs")
        cursor.execute("DROP TABLE IF EXISTS claims")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS policies (
                policy_number VARCHAR(20) PRIMARY KEY,
                policyholder_name VARCHAR(160) NOT NULL,
                gender VARCHAR(10) NOT NULL,
                date_of_birth DATE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(160) NOT NULL,
                address VARCHAR(240) NOT NULL,
                city VARCHAR(80) NOT NULL,
                state VARCHAR(80) NOT NULL,
                pincode VARCHAR(10) NOT NULL,
                age INT NOT NULL,
                policy_type VARCHAR(20) NOT NULL,
                sum_insured DECIMAL(12, 2) NOT NULL,
                policy_start_date DATE NOT NULL,
                policy_end_date DATE NOT NULL,
                total_claims_count INT NOT NULL DEFAULT 0,
                total_claims_paid DECIMAL(12, 2) NOT NULL DEFAULT 0,
                premium DECIMAL(12, 2) NOT NULL,
                status ENUM('Active', 'Lapsed', 'Cancelled') NOT NULL,
                INDEX idx_policyholder_name (policyholder_name)
            ) ENGINE=InnoDB
            """
        )
        cursor.execute(
            """
            CREATE TABLE claims (
                id INT AUTO_INCREMENT PRIMARY KEY,
                claim_id VARCHAR(40) NOT NULL UNIQUE,
                claimant_name VARCHAR(160) NOT NULL,
                policy_number VARCHAR(80) NOT NULL,
                incident_type VARCHAR(80) NOT NULL,
                cause_of_loss VARCHAR(80) NOT NULL,
                claim_amount DECIMAL(12, 2) NOT NULL,
                policy_sum_insured DECIMAL(12, 2) NOT NULL,
                policy_start_date DATE NOT NULL,
                incident_date DATE NOT NULL,
                claim_filing_date DATE NOT NULL,
                incident_location VARCHAR(240) NOT NULL,
                past_claims_on_policy INT NOT NULL DEFAULT 0,
                police_report ENUM('Yes', 'No') NOT NULL,
                description TEXT NOT NULL,
                claim_description TEXT NOT NULL,
                ml_result ENUM('Genuine', 'Fraudulent') NOT NULL,
                confidence DECIMAL(5, 2) NOT NULL,
                risk_score INT NOT NULL DEFAULT 0,
                fraud_risk VARCHAR(20) NOT NULL,
                fraud_score INT NOT NULL DEFAULT 0,
                verification_status VARCHAR(40) NOT NULL,
                verification_reason TEXT NOT NULL,
                severity VARCHAR(20) NOT NULL DEFAULT 'Low',
                status ENUM('Pending', 'Approved', 'Rejected', 'Flagged') NOT NULL,
                blockchain_tx_hash VARCHAR(100) NULL,
                blockchain_block_number BIGINT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_policy_number (policy_number),
                INDEX idx_claimant_name (claimant_name)
            ) ENGINE=InnoDB
            """
        )
        cursor.execute(
            """
            CREATE TABLE activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                claim_id INT NOT NULL,
                risk_score INT NOT NULL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                triggered_signals TEXT NOT NULL,
                blockchain_tx_hash VARCHAR(100) NULL,
                FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE,
                INDEX idx_claim_id (claim_id),
                INDEX idx_logged_at (logged_at)
            ) ENGINE=InnoDB
            """
        )
        connection.commit()


def get_policy(policy_number):
    if Config.USE_MEMORY_DB:
        return next(
            (policy for policy in MEMORY_POLICIES if policy["policy_number"] == policy_number),
            None,
        )
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM policies WHERE policy_number = %s", (policy_number,))
        return cursor.fetchone()


def create_verified_claim(claim):
    if Config.USE_MEMORY_DB:
        claim_id = len(MEMORY_CLAIMS) + 1
        MEMORY_CLAIMS.append({**claim, "id": claim_id})
        return claim_id
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO claims (
                claim_id, claimant_name, policy_number, incident_type, cause_of_loss,
                claim_amount, policy_sum_insured, policy_start_date, incident_date,
                claim_filing_date, incident_location, past_claims_on_policy, police_report,
                description, claim_description, ml_result, confidence, risk_score,
                fraud_risk, fraud_score, verification_status, verification_reason, severity, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            tuple(claim.get(field) for field in (
                "claim_id", "claimant_name", "policy_number", "incident_type", "cause_of_loss",
                "claim_amount", "policy_sum_insured", "policy_start_date", "incident_date",
                "claim_filing_date", "incident_location", "past_claims_on_policy", "police_report",
                "description", "claim_description", "ml_result", "confidence", "risk_score",
                "fraud_risk", "fraud_score", "verification_status", "verification_reason", "severity", "status",
            )),
        )
        connection.commit()
        return cursor.lastrowid


def claim_frequency(policy_number):
    if Config.USE_MEMORY_DB:
        return sum(claim["policy_number"] == policy_number for claim in MEMORY_CLAIMS)
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM claims WHERE policy_number = %s", (policy_number,))
        return cursor.fetchone()[0]


def create_claim(claim):
    if Config.USE_MEMORY_DB:
        claim_id = len(MEMORY_CLAIMS) + 1
        MEMORY_CLAIMS.append({**claim, "id": claim_id})
        return claim_id
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO claims (
                claimant_name, policy_number, incident_type, cause_of_loss,
                claim_amount, policy_sum_insured, policy_start_date, incident_date,
                claim_filing_date, past_claims_on_policy, police_report, description,
                ml_result, confidence, risk_score, severity, status,
                blockchain_tx_hash, blockchain_block_number
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                claim["claimant_name"], claim["policy_number"], claim["incident_type"], claim["cause_of_loss"],
                claim["claim_amount"], claim["policy_sum_insured"], claim["policy_start_date"], claim["incident_date"],
                claim["claim_filing_date"], claim["past_claims_on_policy"], claim["police_report"], claim["description"],
                claim["ml_result"], claim["confidence"], claim["risk_score"], claim["severity"], claim["status"],
                claim.get("blockchain_tx_hash"), claim.get("blockchain_block_number"),
            ),
        )
        connection.commit()
        return cursor.lastrowid


def create_activity_log(claim_id, risk_score, triggered_signals, blockchain_tx_hash=None):
    if Config.USE_MEMORY_DB:
        MEMORY_ACTIVITY_LOGS.append(
            {
                "id": len(MEMORY_ACTIVITY_LOGS) + 1,
                "claim_id": claim_id,
                "risk_score": risk_score,
                "logged_at": datetime.now(),
                "triggered_signals": "; ".join(triggered_signals),
                "blockchain_tx_hash": blockchain_tx_hash,
                "claimant_name": next(claim["claimant_name"] for claim in MEMORY_CLAIMS if claim["id"] == claim_id),
                "policy_number": next(claim["policy_number"] for claim in MEMORY_CLAIMS if claim["id"] == claim_id),
            }
        )
        return
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (claim_id, risk_score, triggered_signals, blockchain_tx_hash) VALUES (%s, %s, %s, %s)",
            (claim_id, risk_score, "; ".join(triggered_signals), blockchain_tx_hash),
        )
        connection.commit()


def get_activity_logs():
    if Config.USE_MEMORY_DB:
        return list(reversed(MEMORY_ACTIVITY_LOGS))
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT a.*, c.claimant_name, c.policy_number FROM activity_logs a JOIN claims c ON c.id = a.claim_id ORDER BY a.logged_at DESC, a.id DESC"
        )
        return cursor.fetchall()


def update_blockchain_receipt(claim_id, transaction_hash, block_number):
    if Config.USE_MEMORY_DB:
        for claim in MEMORY_CLAIMS:
            if claim["id"] == claim_id:
                claim.update(
                    status="Approved",
                    blockchain_tx_hash=transaction_hash,
                    blockchain_block_number=block_number,
                )
                return
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE claims SET status = %s, blockchain_tx_hash = %s, blockchain_block_number = %s WHERE id = %s",
            ("Approved", transaction_hash, block_number, claim_id),
        )
        connection.commit()


def reconcile_claim_statuses():
    if Config.USE_MEMORY_DB:
        for claim in MEMORY_CLAIMS:
            if claim.get("blockchain_tx_hash"):
                claim["status"] = "Approved"
            elif claim["ml_result"] == "Fraudulent":
                claim["status"] = "Flagged"
            elif claim["risk_score"] >= 40:
                claim["status"] = "Rejected"
            else:
                claim["status"] = "Pending"
        return
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE claims
            SET status = CASE
                WHEN blockchain_tx_hash IS NOT NULL THEN 'Approved'
                WHEN ml_result = 'Fraudulent' THEN 'Flagged'
                WHEN risk_score >= 40 THEN 'Rejected'
                ELSE 'Pending'
            END
            """
        )
        connection.commit()


def get_claims():
    reconcile_claim_statuses()
    if Config.USE_MEMORY_DB:
        return list(reversed(MEMORY_CLAIMS))
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM claims ORDER BY created_at DESC, id DESC")
        return cursor.fetchall()
