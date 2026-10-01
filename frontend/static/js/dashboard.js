const statusFilter = document.getElementById('statusFilter');
const claimSearch = document.getElementById('claimSearch');
const rows = Array.from(document.querySelectorAll('#claimsTableBody tr[data-status]'));
const incidentType = document.getElementById('incident_type');
const otherIncidentGroup = document.getElementById('otherIncidentGroup');
const otherIncidentType = document.getElementById('other_incident_type');
const causeOfLoss = document.getElementById('cause_of_loss');
const otherCauseGroup = document.getElementById('otherCauseGroup');
const otherCauseOfLoss = document.getElementById('other_cause_of_loss');
const policyLookupForm = document.getElementById('policyLookupForm');
const policyLookupNumber = document.getElementById('policyLookupNumber');
const policyLookupError = document.getElementById('policyLookupError');
const policyLookupResult = document.getElementById('policyLookupResult');

function toggleOtherField(select, group, input) {
  const isOther = select && select.value === 'Other';
  group?.classList.toggle('d-none', !isOther);
  if (input) {
    input.required = isOther;
    if (!isOther) input.value = '';
  }
}

incidentType?.addEventListener('change', () => toggleOtherField(incidentType, otherIncidentGroup, otherIncidentType));
causeOfLoss?.addEventListener('change', () => toggleOtherField(causeOfLoss, otherCauseGroup, otherCauseOfLoss));

function filterClaims() {
  const status = statusFilter ? statusFilter.value : '';
  const query = claimSearch ? claimSearch.value.trim().toLowerCase() : '';
  rows.forEach((row) => {
    const matchesStatus = !status || row.dataset.status === status;
    const matchesQuery = !query || row.dataset.search.includes(query);
    row.hidden = !(matchesStatus && matchesQuery);
  });
}

if (statusFilter) {
  statusFilter.addEventListener('change', filterClaims);
}
if (claimSearch) {
  claimSearch.addEventListener('input', filterClaims);
}

function formatPolicyAmount(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value);
}

policyLookupForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const policyNumber = policyLookupNumber.value.trim();
  policyLookupError.classList.add('d-none');
  policyLookupResult.classList.add('d-none');
  try {
    const response = await fetch(`/api/policy/${encodeURIComponent(policyNumber)}`);
    const policy = await response.json();
    if (!response.ok) throw new Error(policy.error || 'Policy lookup failed.');
    document.querySelector('[data-policy-field="policyholder_name"]').textContent = policy.policyholder_name;
    document.querySelector('[data-policy-field="gender"]').textContent = policy.gender;
    document.querySelector('[data-policy-field="age"]').textContent = policy.age;
    document.querySelector('[data-policy-field="policy_type"]').textContent = policy.policy_type;
    document.querySelector('[data-policy-field="sum_insured"]').textContent = formatPolicyAmount(policy.sum_insured);
    document.querySelector('[data-policy-field="claims_history"]').textContent = `${policy.total_claims_count} claims / ${formatPolicyAmount(policy.total_claims_paid)} paid`;
    document.querySelector('[data-policy-field="remaining_coverage"]').textContent = formatPolicyAmount(policy.remaining_coverage);
    document.querySelector('[data-policy-field="max_claimable_amount"]').textContent = formatPolicyAmount(policy.max_claimable_amount);
    document.querySelector('[data-policy-field="status"]').textContent = policy.status;
    policyLookupResult.classList.remove('d-none');
  } catch (error) {
    policyLookupError.textContent = error.message;
    policyLookupError.classList.remove('d-none');
  }
});

document.querySelectorAll('.copy-tx').forEach((button) => {
  button.addEventListener('click', async () => {
    await navigator.clipboard.writeText(button.dataset.tx);
    button.innerHTML = '<i class="bi bi-check2"></i><span class="visually-hidden">Copied</span>';
    button.title = 'Copied';
  });
});
