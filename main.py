"""
main.py — Manual text-based testing. No phone call needed.

Run:
    python main.py

Type your messages and the agent replies.
When you type "bye", "thank you" or "exit":
    - Lead is extracted
    - Lead is scored
    - Lead is saved to sales.db
    - Summary email is sent to customer's email

This uses the SAME agent.py logic as the voice call.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from agent import get_agent_response, is_end_of_call, finalize_lead, clear_call_memory

# Simulate a single "call" with a fixed session ID
CALL_SID = "MANUAL_TEST_001"

print("=" * 55)
print("  AI SALES AGENT — MANUAL TEXT TEST")
print("  Type your message and press Enter.")
print("  Say 'bye' or 'thank you' to end the session.")
print("=" * 55)
print()

while True:

    # Get customer input
    try:
        user_input = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\n[Session interrupted]")
        break

    # Skip empty input
    if not user_input:
        continue

    # Hard exit for testing (won't trigger lead save)
    if user_input.lower() == "exit":
        print("\n[Exited without saving lead]")
        break

    # Check if this is an end-of-call phrase
    if is_end_of_call(user_input):

        print("\nAgent: Thank you for speaking with us.")
        print("       We have noted your details and will be in touch. Goodbye!")

        print("\n" + "-" * 40)
        print("Finalizing your lead...")
        print("-" * 40)

        finalize_lead(CALL_SID)
        clear_call_memory(CALL_SID)

        print("\n" + "=" * 55)
        print("  SESSION ENDED")
        print("  Lead saved to sales.db")
        print("  Summary email sent to customer (if email was given)")
        print("=" * 55)
        break

    # Normal turn — get agent response
    reply = get_agent_response(CALL_SID, user_input)

    print(f"\nAgent: {reply}\n")