import os

from dotenv import load_dotenv
from groq import Groq

from rag_tool import get_product_context
from tool import calculate_lead_score, save_lead
from extracter import extract_lead_from_conversation
from email_sender import send_lead_email


# --------------------------------------------------
# 1. Load environment variables
# --------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")


# --------------------------------------------------
# 2. Groq client
# --------------------------------------------------

groq_client = Groq(
    api_key=GROQ_API_KEY
)


# --------------------------------------------------
# 3. System prompt
#
# Generic sales qualification agent.
# Health insurance is only the current demo dataset.
# --------------------------------------------------

SYSTEM_PROMPT = """
You are a professional AI sales qualification agent.

Your job is to qualify a customer as a sales lead through natural conversation.

You should gradually collect:
- What product or service the customer needs
- Budget
- Urgency (when they plan to purchase)
- Email address (to send them a summary)
- Whether they want a callback

Conversation rules:
1. Ask only ONE question at a time.
2. Keep replies short — 1 to 2 sentences only. This is a phone call.
3. Do NOT ask for information the customer already gave.
4. Remember the full conversation history.
5. Be polite and natural. Do NOT pressure the customer.
6. Do NOT invent product details. Only use what is provided in the product context.
7. If product information is provided in context, use it to answer questions accurately.
8. CRITICAL — PRODUCT SCOPE: You ONLY sell products that are explicitly listed in the
   product information provided to you. If a customer asks about any product NOT in that
   list (e.g. train insurance, life insurance, travel insurance, etc.), you must politely
   tell them: "I'm sorry, we don't currently offer that product. We offer Health Insurance
   and Car Insurance. Can I help you with either of those?"
9. NEVER claim to offer, provide, or recommend a product that is not in the product info.
10. Understand short answers from context. Examples:
    - If you just asked "What coverage?" and customer says "Five lakh" → coverage is 5 lakh.
    - If you just asked "What is your budget?" and customer says "25,000" → budget is 25,000.
11. Do NOT restart the conversation or repeat the greeting.
12. After collecting need, budget, urgency and callback — ask for their email address
    so you can send them a summary of the discussion.
"""


# --------------------------------------------------
# 4. Per-call conversation memory
#
# Each Twilio call gets its own history using CallSid.
# Stores only: system prompt + user messages + agent replies.
# RAG context is NEVER stored permanently in memory.
# --------------------------------------------------

conversation_memory = {}


# --------------------------------------------------
# 5. RAG keyword check
#
# Decide whether to retrieve product information.
# Simple keyword list — covers common product questions.
# --------------------------------------------------

PRODUCT_KEYWORDS = [
    "cover", "covered", "coverage",
    "insurance", "health insurance",
    "plan", "policy",
    "hospital", "hospitalization", "cashless",
    "premium", "price", "cost",
    "waiting period", "pre-existing",
    "disease", "illness",
    "eligibility", "eligible", "age limit",
    "benefit", "benefits",
    "dental", "implant",
    "claim", "network",
]


def should_use_rag(user_message):
    """Return True if the message contains a product-related keyword."""

    message = user_message.lower()

    return any(keyword in message for keyword in PRODUCT_KEYWORDS)


# --------------------------------------------------
# 6. Detect end-of-call phrases
# --------------------------------------------------

END_PHRASES = [
    "that's all",
    "thats all",
    "thank you",
    "thanks",
    "no thank you",
    "no thanks",
    "bye",
    "goodbye",
    "good bye",
    "end the call",
    "end call",
    "i'm done",
    "im done",
    "nothing else",
    "that will be all",
]


def is_end_of_call(user_message):
    """Return True if the customer is clearly finishing the call."""

    message = user_message.lower().strip()

    return any(phrase in message for phrase in END_PHRASES)


# --------------------------------------------------
# 7. Build conversation text for extractor
#
# Converts the memory list into a readable string.
# --------------------------------------------------

def build_conversation_text(messages):
    """Turn message list into a plain text conversation string."""

    lines = []

    for msg in messages:

        role = msg["role"]
        content = msg["content"]

        if role == "system":
            continue  # skip system prompt

        elif role == "user":
            lines.append(f"Customer: {content}")

        elif role == "assistant":
            lines.append(f"Agent: {content}")

    return "\n".join(lines)


# --------------------------------------------------
# 8. Finalize lead: extract, score, and save
# --------------------------------------------------

def finalize_lead(call_sid):
    """
    Called when the conversation ends.
    1. Extract lead data from conversation
    2. Calculate lead score
    3. Save to SQLite
    """

    messages = conversation_memory.get(call_sid, [])

    if not messages:
        print("No conversation found for:", call_sid)
        return

    conversation_text = build_conversation_text(messages)

    print("\n===== FINALIZING LEAD =====")
    print(conversation_text)

    # Step 1: Extract structured lead data
    lead = extract_lead_from_conversation(conversation_text)

    if lead is None:
        print("Lead extraction failed. Skipping save.")
        return

    print("\nExtracted Lead Data:")
    print(lead)

    # Step 2: Calculate lead score
    has_clear_need = lead.customer_need not in ["", "Not provided"]
    has_budget = lead.budget not in ["", "Not provided"]
    is_urgent = lead.urgency not in ["", "Not provided"]
    wants_callback = lead.callback_required

    lead_status = calculate_lead_score(
        has_clear_need=has_clear_need,
        has_budget=has_budget,
        urgent=is_urgent,
        wants_callback=wants_callback
    )

    print("\nLead Status:", lead_status)

    # Step 3: Save to database
    result = save_lead(
        customer_name=lead.customer_name,
        customer_email=lead.customer_email,
        customer_need=lead.customer_need,
        budget=lead.budget,
        urgency=lead.urgency,
        callback_required=str(lead.callback_required),
        lead_status=lead_status
    )

    print(result)

    # Step 4: Send summary email to customer
    send_lead_email(
        customer_email=lead.customer_email,
        customer_name=lead.customer_name,
        customer_need=lead.customer_need,
        budget=lead.budget,
        urgency=lead.urgency,
        callback_required=lead.callback_required,
        lead_status=lead_status
    )


# --------------------------------------------------
# 9. Clear memory after call ends
# --------------------------------------------------

def clear_call_memory(call_sid):
    """Remove conversation memory for this call."""

    if call_sid in conversation_memory:
        del conversation_memory[call_sid]
        print("Memory cleared for:", call_sid)


# --------------------------------------------------
# 10. Main agent function
# --------------------------------------------------

def get_agent_response(call_sid, user_message):
    """
    Process one customer message and return the agent reply.

    Flow:
    1. Create memory for new call if needed
    2. Append customer message to memory
    3. Build request = memory + optional RAG context (NOT stored in memory)
    4. Call Groq LLM
    5. Append agent reply to memory
    6. Return agent reply
    """

    # Create memory for a new call
    if call_sid not in conversation_memory:

        conversation_memory[call_sid] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    messages = conversation_memory[call_sid]

    # Append current customer message
    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    # Build request messages = permanent memory (copy)
    request_messages = list(messages)

    # Keep rag_context so we can use it as fallback if LLM returns empty
    rag_context = None

    # Temporarily add RAG context if relevant (NOT saved to memory)
    if should_use_rag(user_message):

        try:

            rag_context = get_product_context(user_message)

            print("\nRAG CONTEXT:", rag_context)

            # Add raw chunks as temporary system message (NOT stored in memory)
            request_messages.append(
                {
                    "role": "system",
                    "content": (
                        "PRODUCT KNOWLEDGE BASE (this is the ONLY source of truth):\n"
                        f"{rag_context}\n\n"
                        "STRICT INSTRUCTIONS — follow these exactly:\n"
                        "1. We ONLY sell two products: Health Insurance and Car Insurance.\n"
                        "2. If the customer asks about ANY other product (train insurance, "
                        "life insurance, travel insurance, bike insurance, pet insurance, etc.), "
                        "you MUST say: 'I'm sorry, we don't currently offer that product. "
                        "We offer Health Insurance and Car Insurance. "
                        "Can I help you with either of those?'\n"
                        "3. If the question IS about our products but the answer is not in "
                        "the knowledge base above, say: "
                        "'That specific detail is not available in our current product information.'\n"
                        "4. NEVER use your general world knowledge to answer product questions.\n"
                        "5. NEVER invent, guess, or assume any product features or availability."
                    )
                }
            )

        except Exception as error:

            print(
                "\nRAG ERROR:",
                type(error).__name__,
                str(error)
            )

    # --------------------------------------------------
    # Trim conversation if it gets too long.
    # Keep: system prompt (index 0) + last 10 messages.
    # This prevents the LLM from hitting context limits.
    # --------------------------------------------------

    MAX_HISTORY = 10  # number of user+agent turns to keep

    if len(request_messages) > MAX_HISTORY + 1:
        # Always keep system prompt at index 0
        system_msg = request_messages[0]
        recent_msgs = request_messages[-(MAX_HISTORY):]
        request_messages = [system_msg] + recent_msgs

    # --------------------------------------------------
    # Call Groq LLM — attempt 1
    # --------------------------------------------------

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=request_messages,
        temperature=0.3,
        max_tokens=150
    )

    raw_content = response.choices[0].message.content

    print("\nLLM RAW CONTENT:", repr(raw_content))

    agent_reply = (raw_content or "").strip()

    # --------------------------------------------------
    # If LLM returned empty — retry once with a simple prompt.
    # This handles cases where the model refuses to reply
    # due to context confusion or policy.
    # --------------------------------------------------

    if not agent_reply:

        print("WARNING: LLM returned empty. Retrying with simple prompt...")

        retry_messages = [
            {
                "role": "system",
                "content": (
                    "You are a polite AI sales assistant on a phone call. "
                    "Reply in 1-2 short sentences. Always reply with something helpful."
                )
            },
            {
                "role": "user",
                "content": user_message
            }
        ]

        retry_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=retry_messages,
            temperature=0.5,
            max_tokens=100
        )

        raw_retry = retry_response.choices[0].message.content

        print("RETRY CONTENT:", repr(raw_retry))

        agent_reply = (raw_retry or "").strip()

    # Final fallback if retry also returned empty
    if not agent_reply:
        if rag_context:
            agent_reply = "I'm sorry, that specific detail is not in our current product information."
        else:
            agent_reply = "Could you please rephrase that? I want to make sure I help you correctly."

    # Save only the agent reply to permanent memory (NOT the RAG context)
    messages.append(
        {
            "role": "assistant",
            "content": agent_reply
        }
    )

    print("\nAGENT REPLY  :", agent_reply)
    print("MEMORY LENGTH:", len(messages))

    return agent_reply