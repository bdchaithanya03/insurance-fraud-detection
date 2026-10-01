import json
from datetime import date

import joblib

from backend.config import Config

INCIDENT_TYPES = [
    "Motor Accident", "Fire", "Theft", "Burglary", "Flood", "Earthquake",
    "Storm", "Medical/Health", "Death", "Property Damage",
    "Third-Party Liability", "Travel/Baggage Loss", "Other",
]
INCIDENT_CODES = {incident: index for index, incident in enumerate(INCIDENT_TYPES)}
INCIDENT_BASE_RISK = {
    "Motor Accident": 0.14, "Fire": 0.10, "Theft": 0.23, "Burglary": 0.22,
    "Flood": 0.08, "Earthquake": 0.06, "Storm": 0.09, "Medical/Health": 0.18,
    "Death": 0.05, "Property Damage": 0.13, "Third-Party Liability": 0.16,
    "Travel/Baggage Loss": 0.29, "Other": 0.20,
}
FEATURE_NAMES = [
    "amount_to_sum_insured_ratio", "policy_tenure_years", "reporting_delay_days",
    "past_claim_count", "police_report", "cause_of_loss",
]


def load_model():
    return joblib.load(Config.MODEL_PATH)


def load_metadata():
    with Config.MODEL_METADATA_PATH.open(encoding="utf-8") as metadata_file:
        return json.load(metadata_file)


def _policy_tenure(policy_number):
    return 0.5 + (sum((index + 1) * ord(character) for index, character in enumerate(policy_number)) % 195) / 10


def _has_police_report(description):
    terms = ("police", "report", "station", "fir", "case number", "incident number")
    description_lower = description.lower()
    return int(any(term in description_lower for term in terms))


def make_features(claim, claim_frequency_count):
    incident_date = date.fromisoformat(claim["incident_date"])
    reporting_delay = max((date.today() - incident_date).days, 0)
    amount = float(claim["claim_amount"])
    typical_sum_insured = {
        "Travel/Baggage Loss": 3500, "Medical/Health": 18000, "Death": 100000,
        "Motor Accident": 30000, "Other": 25000,
    }.get(claim["incident_type"], 45000)
    amount_ratio = min(amount / (amount + typical_sum_insured), 0.98)
    return [[amount_ratio, _policy_tenure(claim["policy_number"]), reporting_delay,
             claim_frequency_count, _has_police_report(claim["description"]),
             INCIDENT_CODES[claim["incident_type"]]]]


def _risk_details(model, features, claim):
    values = features[0]
    importances = dict(zip(FEATURE_NAMES, model.feature_importances_))
    signals = {
        "amount_to_sum_insured_ratio": min(max((values[0] - 0.55) / 0.43, 0), 1),
        "policy_tenure_years": min(max((2.5 - values[1]) / 2.5, 0), 1),
        "reporting_delay_days": min(max((values[2] - 45) / 135, 0), 1),
        "past_claim_count": min(values[3] / 4, 1),
        "police_report": 1 - values[4],
        "cause_of_loss": INCIDENT_BASE_RISK[claim["incident_type"]],
    }
    contributions = {name: importances[name] * signals[name] for name in FEATURE_NAMES}
    labels = {
        "amount_to_sum_insured_ratio": "High amount relative to estimated sum insured",
        "policy_tenure_years": "Short policy tenure",
        "reporting_delay_days": "Long reporting delay",
        "past_claim_count": "Multiple past claims on this policy",
        "police_report": "No police report indicated in the description",
        "cause_of_loss": f"Higher-risk incident pattern: {claim['incident_type']}",
    }
    ranked = sorted(contributions, key=contributions.get, reverse=True)
    return [labels[name] for name in ranked if contributions[name] >= 0.04][:3]


def predict(claim, claim_frequency_count):
    model = load_model()
    features = make_features(claim, claim_frequency_count)
    prediction = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]
    fraud_probability = float(probabilities[list(model.classes_).index(1)])
    confidence = round(float(max(probabilities)) * 100, 2)
    risk_score = round(fraud_probability * 100)
    severity = "Critical" if risk_score >= 80 else "High" if risk_score >= 60 else "Moderate" if risk_score >= 35 else "Low"
    return {
        "result": "Fraudulent" if prediction else "Genuine",
        "confidence": confidence,
        "risk_score": risk_score,
        "severity": severity,
        "flagged_reasons": _risk_details(model, features, claim) if prediction else [],
    }
