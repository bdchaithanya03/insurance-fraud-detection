from datetime import date, datetime
from pathlib import Path
import re
import uuid

from flask import Flask, jsonify, render_template, request

from backend.config import Config
from backend.currency import format_inr
from backend.db import (
    create_verified_claim,
    get_policy,
    init_database,
)
from backend.ml_model import INCIDENT_TYPES, predict

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.config.from_object(Config)
app.jinja_env.filters["inr"] = format_inr
init_database()

CAUSE_OF_LOSS_TYPES = [
    "Accident", "Theft", "Fire", "Natural Disaster", "Medical",
    "Property Damage", "Death", "Other",
]
POLICY_DEFAULT_INCIDENT_TYPE = {
    "Motor": "Motor Accident",
    "Health": "Medical/Health",
    "Home": "Property Damage",
    "Travel": "Travel/Baggage Loss",
}


@app.get("/")
def dashboard():
    try:
        return render_template("policy_search.html")
    except Exception as error:
        return render_template("policy_search.html", error=str(error))


def policy_payload(policy):
    return {
        "policy_number": policy["policy_number"],
        "policyholder_name": policy["policyholder_name"],
        "gender": policy["gender"],
        "date_of_birth": str(policy["date_of_birth"]),
        "age": int(policy["age"]),
        "phone": policy["phone"],
        "email": policy["email"],
        "address": policy["address"],
        "city": policy["city"],
        "state": policy["state"],
        "pincode": policy["pincode"],
        "policy_type": policy["policy_type"],
        "status": policy["status"],
        "policy_start_date": str(policy["policy_start_date"]),
        "policy_end_date": str(policy["policy_end_date"]),
        "sum_insured": float(policy["sum_insured"]),
        "premium": float(policy["premium"]),
        "total_claims_count": int(policy["total_claims_count"]),
        "total_claims_paid": float(policy["total_claims_paid"]),
    }


@app.post("/policy/search")
def search_policy():
    policy_number = request.form.get("policy_number", "").strip().upper()
    if not policy_number:
        return render_template("policy_search.html", error="Please enter a policy number."), 400
    if not re.fullmatch(r"POL\d{5,}", policy_number):
        return render_template("policy_search.html", error="Please enter a valid policy number."), 400
    policy = get_policy(policy_number)
    if policy is None:
        return render_template(
            "policy_search.html",
            error="No existing policy was found with this policy number. New policy registration is not available through this system.",
            searched_policy=policy_number,
        ), 404
    return render_template("policy_search.html", policy=policy_payload(policy))


@app.get("/policy/<policy_number>/verify")
def verification_page(policy_number):
    policy = get_policy(policy_number.strip().upper())
    if policy is None:
        return render_template(
            "policy_search.html",
            error="No existing policy was found with this policy number. New policy registration is not available through this system.",
        ), 404
    sum_insured = float(policy["sum_insured"])
    claim_amount_options = sorted({round(sum_insured * percent / 100, 2) for percent in (10, 25, 50, 75, 100)})
    return render_template(
        "policy_verification.html",
        policy=policy_payload(policy),
        incident_types=INCIDENT_TYPES,
        cause_of_loss_types=CAUSE_OF_LOSS_TYPES,
        default_incident_type=POLICY_DEFAULT_INCIDENT_TYPE.get(policy["policy_type"], ""),
        claim_amount_options=claim_amount_options,
        today=date.today().isoformat(),
    )


@app.get("/api/policy/<policy_number>")
def policy_lookup(policy_number):
    policy = get_policy(policy_number.strip().upper())
    if policy is None:
        return {"error": "Policy not found. Check the policy number and try again."}, 404
    payload = policy_payload(policy)
    payload["remaining_coverage"] = max(payload["sum_insured"] - payload["total_claims_paid"], 0)
    payload["max_claimable_amount"] = payload["remaining_coverage"]
    return payload


POLICY_COVERAGE = {
    "Motor": {"Motor Accident", "Theft", "Burglary", "Third-Party Liability"},
    "Health": {"Medical/Health", "Death"},
    "Home": {"Fire", "Theft", "Burglary", "Flood", "Earthquake", "Storm", "Property Damage"},
    "Travel": {"Travel/Baggage Loss"},
}


@app.post("/claims/verify")
def verify_claim():
    form = request.form
    policy_number = form.get("policy_number", "").strip().upper()
    if not re.fullmatch(r"POL\d{5,}", policy_number):
        return jsonify({"error": "Please enter a valid policy number."}), 400
    policy = get_policy(policy_number)
    if policy is None:
        return jsonify({"error": "REJECT - Policy does not exist"}), 404
    required = ("incident_type", "cause_of_loss", "claim_amount", "incident_date", "incident_location", "police_report", "claim_description")
    if any(not form.get(field, "").strip() for field in required):
        return jsonify({"error": "Complete every current claim field before verifying."}), 400
    incident_type = POLICY_DEFAULT_INCIDENT_TYPE.get(str(policy["policy_type"]), "")
    cause_of_loss = form["cause_of_loss"]
    police_report = form["police_report"]
    if not incident_type or form["incident_type"] != incident_type:
        return jsonify({"error": "Incident type is fixed by the existing policy type."}), 400
    if incident_type not in INCIDENT_TYPES or cause_of_loss not in CAUSE_OF_LOSS_TYPES or police_report not in {"Yes", "No"}:
        return jsonify({"error": "Choose a supported incident type and cause of loss."}), 400
    try:
        claim_amount = float(form["claim_amount"])
        incident_date = datetime.strptime(form["incident_date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Enter a valid claim amount and incident date."}), 400
    if claim_amount <= 0:
        return jsonify({"error": "Claim amount must be greater than zero."}), 400

    policy_start = datetime.strptime(str(policy["policy_start_date"]), "%Y-%m-%d").date()
    policy_end = datetime.strptime(str(policy["policy_end_date"]), "%Y-%m-%d").date()
    sum_insured = float(policy["sum_insured"])
    coverage_reason = ""
    outcome = "ELIGIBLE"
    eligible_amount = min(claim_amount, sum_insured)
    if policy["status"] != "Active":
        outcome, coverage_reason = "NOT ELIGIBLE", "Policy is not active"
    elif not policy_start <= incident_date <= policy_end:
        outcome, coverage_reason = "NOT ELIGIBLE", "Incident is outside the policy coverage period"
    elif incident_type not in POLICY_COVERAGE.get(policy["policy_type"], set()):
        outcome, coverage_reason = "NOT ELIGIBLE", "Incident type is not covered by this policy"
    elif claim_amount > sum_insured:
        outcome, coverage_reason = "PARTIALLY ELIGIBLE", "Requested claim exceeds the policy sum insured"

    model_claim = {
        "claim_amount": claim_amount,
        "policy_sum_insured": sum_insured,
        "policy_start_date": str(policy["policy_start_date"]),
        "incident_date": str(incident_date),
        "claim_filing_date": date.today().isoformat(),
        "past_claims_on_policy": int(policy["total_claims_count"]),
        "police_report": police_report,
        "incident_type": incident_type,
        "cause_of_loss": cause_of_loss,
        "description": form["claim_description"].strip(),
    }
    prediction = predict(model_claim, int(policy["total_claims_count"]))
    fraud_score = int(prediction["risk_score"])
    fraud_risk = "High" if fraud_score >= 70 else "Medium" if fraud_score >= 40 else "Low"
    if fraud_risk == "High" and outcome == "ELIGIBLE":
        outcome = "ADDITIONAL VERIFICATION REQUIRED"
        coverage_reason = "Claim requires additional verification due to high fraud risk"
    claim_record = {
        "claim_id": f"CLM-{uuid.uuid4().hex[:12].upper()}",
        "claimant_name": policy["policyholder_name"], "policy_number": policy_number,
        "incident_type": incident_type, "cause_of_loss": cause_of_loss,
        "claim_amount": claim_amount, "policy_sum_insured": sum_insured,
        "policy_start_date": str(policy["policy_start_date"]), "incident_date": str(incident_date),
        "claim_filing_date": date.today().isoformat(), "incident_location": form["incident_location"].strip(),
        "past_claims_on_policy": int(policy["total_claims_count"]), "police_report": police_report,
        "description": form["claim_description"].strip(), "claim_description": form["claim_description"].strip(),
        "ml_result": prediction["result"], "confidence": prediction["confidence"],
        "risk_score": fraud_score, "fraud_risk": fraud_risk, "fraud_score": fraud_score,
        "verification_status": outcome, "verification_reason": coverage_reason or "Policy and claim details verified",
        "severity": prediction["severity"], "status": outcome,
    }
    create_verified_claim(claim_record)
    return jsonify({
        "outcome": outcome, "reason": coverage_reason or "Policy and claim details verified",
        "policy_number": policy_number, "policy_sum_insured": sum_insured,
        "requested_claim_amount": claim_amount, "eligible_amount": eligible_amount if outcome in {"ELIGIBLE", "PARTIALLY ELIGIBLE"} else 0,
        "fraud_risk": fraud_risk, "risk_score": fraud_score,
        "risk_reasons": prediction["flagged_reasons"], "claim_id": claim_record["claim_id"],
    })


if __name__ == "__main__":
    if Path(Config.MODEL_PATH).exists():
        init_database()
    app.run(debug=True)
