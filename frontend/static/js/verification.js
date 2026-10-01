const form = document.getElementById('claimVerificationForm');
const result = document.getElementById('verificationResult');
const resultBody = document.getElementById('resultBody');
const errorBox = document.getElementById('claimError');

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value);
}

function outcomeClass(outcome) {
  if (outcome === 'ELIGIBLE') return 'result-success';
  if (outcome === 'PARTIALLY ELIGIBLE') return 'result-warning';
  if (outcome === 'ADDITIONAL VERIFICATION REQUIRED') return 'result-danger';
  return 'result-danger';
}

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Verifying claim';
  errorBox.classList.add('d-none');
  result.classList.add('d-none');
  try {
    const response = await fetch(form.action, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Claim verification failed.');
    const risk = `<div class="risk-panel"><div><span>Fraud Risk Assessment</span><strong>${data.fraud_risk} Risk</strong></div><div class="risk-score">${data.risk_score}%<small>Risk Score</small></div></div>`;
    let details = `<div class="result-grid"><div><span>Policy Number</span><strong>${data.policy_number}</strong></div><div><span>Policy Sum Insured</span><strong>${money(data.policy_sum_insured)}</strong></div><div><span>Requested Claim Amount</span><strong>${money(data.requested_claim_amount)}</strong></div><div><span>Eligible Amount</span><strong>${money(data.eligible_amount)}</strong></div></div>`;
    if (data.outcome === 'NOT ELIGIBLE' || data.outcome === 'ADDITIONAL VERIFICATION REQUIRED') details += `<p class="result-reason"><strong>Reason:</strong> ${data.reason}</p>`;
    if (data.outcome === 'PARTIALLY ELIGIBLE') details += `<p class="result-reason"><strong>Maximum Covered Amount:</strong> ${money(data.policy_sum_insured)}<br>${data.reason}</p>`;
    if (data.risk_reasons?.length) details += `<p class="result-reason"><strong>Risk indicators:</strong> ${data.risk_reasons.join('; ')}</p>`;
    if (data.outcome === 'ADDITIONAL VERIFICATION REQUIRED') details += '<p class="review-note"><i class="bi bi-exclamation-triangle-fill"></i> Claim requires additional verification. It has not been automatically approved.</p>';
    resultBody.innerHTML = `<div class="result-head ${outcomeClass(data.outcome)}"><i class="bi ${data.outcome === 'ELIGIBLE' ? 'bi-check-circle-fill' : data.outcome === 'PARTIALLY ELIGIBLE' ? 'bi-exclamation-circle-fill' : 'bi-x-circle-fill'}"></i><div><span>Claim Status</span><h3>${data.outcome}</h3></div></div>${details}${risk}<p class="claim-reference">Verification reference: ${data.claim_id}</p>`;
    result.classList.remove('d-none');
    result.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove('d-none');
  } finally {
    button.disabled = false;
    button.innerHTML = '<i class="bi bi-shield-check me-2"></i>Verify Claim Eligibility';
  }
});
