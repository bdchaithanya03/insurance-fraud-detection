# 🛡️ Insurance Policy Verification System

### AI-Powered Insurance Claim Verification using Flask & Machine Learning

A simple web-based system that **searches existing insurance policies and verifies claim requests** using policy details, eligibility rules, and a **Random Forest fraud detection model**.

> 🚫 No policy creation or editing — only verification of existing policies.

---

## ✨ Features

* 🔎 **Search Existing Policies**
* 👤 **Read-only Policyholder Details**
* 📋 **Automatic Policy Type Detection**
* 📅 **Coverage Date Verification**
* 💰 **Claim Amount & Sum Insured Validation**
* 🤖 **Random Forest Fraud Detection**
* ⚠️ **Additional Verification for High-Risk Claims**
* 🗄️ **MySQL / In-Memory Database**
* ⛓️ **Solidity & Blockchain Components**

---

## 🔄 How It Works

```text
🔎 Search Policy
       ↓
📄 View Policy Details
       ↓
📝 Enter Claim Details
       ↓
✅ Check Policy Eligibility
       ↓
🤖 Fraud Risk Analysis
       ↓
📊 Verification Result
```

---

## 📊 Verification Results

| Result                                  | Meaning                                      |
| --------------------------------------- | -------------------------------------------- |
| 🟢 **ELIGIBLE**                         | Claim satisfies policy conditions            |
| 🟡 **PARTIALLY ELIGIBLE**               | Claim exceeds sum insured                    |
| 🔴 **NOT ELIGIBLE**                     | Policy or claim conditions are not satisfied |
| 🟠 **ADDITIONAL VERIFICATION REQUIRED** | High fraud risk detected                     |

---

## 🛠️ Technology Stack

**Frontend:** HTML • CSS • JavaScript

**Backend:** Python • Flask

**Database:** MySQL

**Machine Learning:** scikit-learn • Random Forest • pandas • NumPy

**Blockchain:** Solidity • Truffle • Ganache • Web3.py

---

## 📁 Project Structure

```text
Insurance-Policy-Verification-System/
│
├── backend/          → Flask application
├── frontend/         → HTML, CSS & JavaScript
├── database/         → MySQL schema & policy data
├── ml/               → Fraud detection model
├── blockchain/       → Solidity & Truffle files
├── tests/            → Project tests
│
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1️⃣ Create Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run

```bash
USE_MEMORY_DB=1 python -m backend.run
```

### 4️⃣ Open

```text
http://127.0.0.1:5000
```

---

## 🧠 Machine Learning

The system uses a **Random Forest classifier** to identify potentially fraudulent claims.

Train the model using:

```bash
python ml/train.py
```

---

## 🔐 Important

* Policy information is retrieved directly from the database.
* Policyholder details cannot be edited through the application.
* The system does not create or register new policies.
* All included policy and claim data is **synthetic**.
* This project is intended for **academic and educational purposes**.

---

## 🎯 Project Goal

To create a simple and reliable system that helps verify:

**“Can this existing insurance policy cover the current claim?”**

while also identifying claims that may require **additional fraud verification**.

---

### 👨‍💻 Developed by

**B D Chaithanya**
BCA Student | St. Philomena's College, Mysore

⭐ *If you find this project useful, consider giving it a star!*
