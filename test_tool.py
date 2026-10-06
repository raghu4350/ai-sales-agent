from tool import save_lead, get_all_leads
from tool import calculate_lead_score


status = calculate_lead_score(
    has_clear_need=True,
    has_budget=True,
    urgent=True,
    wants_callback=True
)

print(status)


result = save_lead(
    customer_name="Ravi",
    customer_need="Health Insurance",
    budget="25000",
    urgency="1 week",
    callback_required="Yes",
    lead_status="HIGH"
)

print(result)


print("\nAll Leads:")

leads = get_all_leads()

print(leads)