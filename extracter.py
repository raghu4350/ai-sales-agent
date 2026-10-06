import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from models import LeadData


load_dotenv()


# --------------------------------------------------
# LLM with structured output
# Uses Pydantic LeadData model to extract lead info
# --------------------------------------------------

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY")
)

structured_llm = llm.with_structured_output(LeadData)


# --------------------------------------------------
# extract_lead_from_conversation
#
# Takes the full conversation history as a string
# and extracts structured lead data from it.
#
# Returns a LeadData object (Pydantic model).
# Returns None if extraction fails.
# --------------------------------------------------

def extract_lead_from_conversation(conversation_text):

    try:

        prompt = f"""
Extract the lead information from this sales conversation.

Fill in what you can find. If some information is missing,
use "Not provided" for text fields.
For callback_required, use True if the customer said yes to a callback.

Conversation:
{conversation_text}
"""

        result = structured_llm.invoke(prompt)

        return result

    except Exception as error:

        print(
            "EXTRACTOR ERROR:",
            type(error).__name__,
            str(error)
        )

        return None