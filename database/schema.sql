CREATE DATABASE IF NOT EXISTS insurance_fraud;
USE insurance_fraud;

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
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS claims (
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
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    claim_id INT NOT NULL,
    risk_score INT NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_signals TEXT NOT NULL,
    blockchain_tx_hash VARCHAR(100) NULL,
    FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE,
    INDEX idx_claim_id (claim_id),
    INDEX idx_logged_at (logged_at)
) ENGINE=InnoDB;
