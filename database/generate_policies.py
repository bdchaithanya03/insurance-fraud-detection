"""Generate believable synthetic Indian insurance policy records."""

import csv
import calendar
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260919
RECORD_COUNT = 1100
OUTPUT_PATH = Path(__file__).with_name("policies.csv")
TODAY = date(2026, 9, 19)

FIRST_NAMES = [
    "Aarav", "Aditi", "Aditya", "Akash", "Amrita", "Ananya", "Arjun", "Arun",
    "Bhavna", "Chaitanya", "Deepak", "Devika", "Diya", "Farhan", "Gaurav", "Isha",
    "Ishaan", "Jaya", "Karan", "Kavya", "Lakshmi", "Manish", "Meera", "Mohan",
    "Neha", "Nikhil", "Pooja", "Pranav", "Rahul", "Riya", "Rohan", "Sahil",
    "Sanjay", "Shreya", "Sneha", "Tanvi", "Varun", "Vikram", "Yash", "Zoya",
]
LAST_NAMES = [
    "Bhat", "Chatterjee", "Deshmukh", "Iyer", "Jain", "Kapoor", "Khan", "Kulkarni",
    "Malhotra", "Menon", "Mehta", "Mishra", "Nair", "Patel", "Pillai", "Rao",
    "Reddy", "Saxena", "Shah", "Sharma", "Shetty", "Singh", "Srinivasan", "Verma",
]

POLICY_TYPES = ("Motor", "Health", "Home", "Travel")
TYPE_WEIGHTS = (42, 38, 14, 6)
GENDERS = ("Male", "Female", "Other")
GENDER_WEIGHTS = (54, 44, 2)
STATUS_WEIGHTS = (85, 12, 3)


def weighted_age(rng):
    bucket = rng.choices(("young", "working", "senior"), weights=(10, 76, 14), k=1)[0]
    ranges = {"young": (18, 24), "working": (25, 55), "senior": (56, 75)}
    return rng.randint(*ranges[bucket])


def money_for_policy(policy_type, rng):
    ranges = {
        "Motor": (100_000, 1_000_000),
        "Health": (200_000, 2_500_000),
        "Home": (1_000_000, 5_000_000),
        "Travel": (50_000, 500_000),
    }
    low, high = ranges[policy_type]
    return round(rng.randint(low // 500, high // 500) * 500, 2)


def make_dates(rng):
    start = TODAY - timedelta(days=rng.randint(30, 5 * 365))
    duration = rng.choices((365, 730, 1095), weights=(48, 38, 14), k=1)[0]
    return start, start + timedelta(days=duration)


def make_contact_details(age, index, rng):
    locations = [
        ("Mumbai", "Maharashtra", "400001"), ("Bengaluru", "Karnataka", "560001"),
        ("Chennai", "Tamil Nadu", "600001"), ("Delhi", "Delhi", "110001"),
        ("Kolkata", "West Bengal", "700001"), ("Hyderabad", "Telangana", "500001"),
        ("Pune", "Maharashtra", "411001"), ("Ahmedabad", "Gujarat", "380001"),
    ]
    city, state, pincode = rng.choice(locations)
    birth_year = TODAY.year - age
    birth_month = rng.randint(1, 12)
    birth_day = rng.randint(1, calendar.monthrange(birth_year, birth_month)[1])
    if (birth_month, birth_day) > (TODAY.month, TODAY.day):
        birth_year -= 1
    birth_date = date(birth_year, birth_month, birth_day)
    return {
        "date_of_birth": birth_date.isoformat(),
        "phone": f"+91 {rng.randint(7000000000, 9999999999)}",
        "email": f"policyholder{10001 + index}@example.in",
        "address": f"{rng.randint(1, 180)}, {rng.choice(['MG Road', 'Lake View Road', 'Station Road', 'Park Street'])}",
        "city": city,
        "state": state,
        "pincode": pincode,
    }


def make_record(index, rng):
    age = weighted_age(rng)
    policy_type = rng.choices(POLICY_TYPES, weights=TYPE_WEIGHTS, k=1)[0]
    sum_insured = money_for_policy(policy_type, rng)
    claims_count = rng.choices((0, 1, 2, 3, 4, 5, 6), weights=(64, 16, 9, 6, 3, 1, 0.2), k=1)[0]
    status = rng.choices(("Active", "Lapsed", "Cancelled"), weights=STATUS_WEIGHTS, k=1)[0]
    start_date, end_date = make_dates(rng)
    contact_details = make_contact_details(age, index, rng)
    if status == "Active":
        end_date = max(end_date, TODAY + timedelta(days=rng.randint(1, 365)))
    if claims_count:
        paid_ratio = rng.uniform(0.08, min(0.72, 0.16 + claims_count * 0.11))
        total_claims_paid = round(sum_insured * paid_ratio / 500) * 500
    else:
        total_claims_paid = 0
    return {
        "policy_number": f"POL{10001 + index}",
        "policyholder_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
        "gender": rng.choices(GENDERS, weights=GENDER_WEIGHTS, k=1)[0],
        "age": age,
        **contact_details,
        "policy_type": policy_type,
        "sum_insured": f"{sum_insured:.2f}",
        "policy_start_date": start_date.isoformat(),
        "policy_end_date": end_date.isoformat(),
        "total_claims_count": claims_count,
        "total_claims_paid": f"{min(total_claims_paid, sum_insured):.2f}",
        "premium": f"{round(sum_insured * rng.uniform(0.012, 0.048) / 100) * 100:.2f}",
        "status": status,
    }


def validate(records):
    assert len(records) >= 1000
    policy_numbers = [record["policy_number"] for record in records]
    assert len(policy_numbers) == len(set(policy_numbers))
    assert all(record["status"] in {"Active", "Lapsed", "Cancelled"} for record in records)
    assert len({record["email"] for record in records}) == len(records)
    assert all(18 <= int(record["age"]) <= 75 for record in records)
    assert all(
        TODAY.year - int(record["date_of_birth"][:4])
        - ((TODAY.month, TODAY.day) < tuple(map(int, record["date_of_birth"][5:].split("-"))))
        == int(record["age"])
        for record in records
    )
    assert all(float(record["total_claims_paid"]) <= float(record["sum_insured"]) for record in records)
    gender_counts = {gender: sum(record["gender"] == gender for record in records) for gender in GENDERS}
    status_counts = {status: sum(record["status"] == status for record in records) for status in ("Active", "Lapsed", "Cancelled")}
    assert 50 <= gender_counts["Male"] / len(records) * 100 <= 58
    assert 40 <= gender_counts["Female"] / len(records) * 100 <= 50
    assert 0.5 <= gender_counts["Other"] / len(records) * 100 <= 3
    assert 80 <= status_counts["Active"] / len(records) * 100 <= 90
    assert 8 <= status_counts["Lapsed"] / len(records) * 100 <= 16
    assert 1 <= status_counts["Cancelled"] / len(records) * 100 <= 6
    assert sum(int(record["total_claims_count"]) == 0 for record in records) >= len(records) * 0.60
    assert sum(int(record["total_claims_count"]) >= 5 for record in records) < len(records) * 0.02
    return gender_counts, status_counts


def main():
    rng = random.Random(SEED)
    records = [make_record(index, rng) for index in range(RECORD_COUNT)]
    gender_counts, status_counts = validate(records)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"Generated {len(records)} policies at {OUTPUT_PATH}")
    print(f"Gender distribution: {gender_counts}")
    print(f"Status distribution: {status_counts}")
    print("Validation: unique policy numbers, age bounds, and claim payment bounds passed")


if __name__ == "__main__":
    main()
