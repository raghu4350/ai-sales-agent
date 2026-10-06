"""
evalution.py — Full text-based test. No phone call needed.

Run:
    python evalution.py

Tests:
    1. Sales qualification flow (6 turns)
    2. RAG product questions (2 turns)
    3. End of call → lead extraction → lead save
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # Fix Windows Unicode crash

from agent import get_agent_response, is_end_of_call, finalize_lead

# Use a fixed test call ID (simulates one phone call)
CALL_SID = "TEST_CALL_001"

# Full conversation script — same as the real phone scenario
conversation = [
    "I need health insurance for my parents.",
    "They are 58 and 62.",
    "Around five lakh.",
    "Around twenty five thousand per year.",
    "Within one week.",
    "Yes, please call me back.",
    "Are pre-existing diseases covered?",     # RAG test
    "Are dental implants covered?",           # RAG no-hallucination test
    "That's all, thank you.",                 # End call trigger
]

print("=" * 55)
print("  AI SALES AGENT — FULL TEXT TEST")
print("=" * 55)

for i, customer_input in enumerate(conversation, start=1):

    print(f"\n[Turn {i}]")
    print(f"  Customer : {customer_input}")

    # Check if this is an end-of-call message
    if is_end_of_call(customer_input):

        print("  [END OF CALL DETECTED]")
        print("\n  Finalizing lead...")

        finalize_lead(CALL_SID)

        print("\n  Agent    : Thank you for speaking with us.")
        print("             We have noted your details. Goodbye.")
        break

    # Get agent response
    reply = get_agent_response(CALL_SID, customer_input)

    print(f"  Agent    : {reply}")

print("\n" + "=" * 55)
print("  TEST COMPLETE")
print("  Check sales.db for saved lead.")
print("=" * 55)