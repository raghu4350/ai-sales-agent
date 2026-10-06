import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY")
)


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a professional AI sales assistant.

            Be polite.
            Ask one question at a time.
            Keep the answer short.
            """
        ),
        (
            "human",
            "{customer_message}"
        )
    ]
)


chain = prompt | llm


response = chain.invoke(
    {
        "customer_message":
        "I want health insurance for my parents."
    }
)


print(response.content)











"openai/gpt-oss-120b"




