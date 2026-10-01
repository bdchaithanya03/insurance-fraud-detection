from backend.currency import format_inr
from backend.ml_model import severity_for_risk


def test_format_inr_uses_indian_grouping():
    assert format_inr(100000) == "₹1,00,000.00"
    assert format_inr(123456789.5) == "₹12,34,56,789.50"


def test_severity_for_risk_matches_required_ranges():
    assert severity_for_risk(15) == "Low"
    assert severity_for_risk(45) == "Medium"
    assert severity_for_risk(75) == "High"
    assert severity_for_risk(90) == "Critical"
