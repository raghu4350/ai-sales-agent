import os
import sqlite3


# --------------------------------------------------
# DB_PATH — configurable via environment variable.
# Must match the value set in database.py.
#
# Local dev    : defaults to "sales.db" (project root)
# Railway      : set DB_PATH=/data/sales.db in dashboard
# --------------------------------------------------

DB_PATH = os.getenv("DB_PATH", "sales.db")


# Tool 1: Save a lead into database
def save_lead(
    customer_name,
    customer_email,
    customer_need,
    budget,
    urgency,
    callback_required,
    lead_status
):

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO leads (
            customer_name,
            customer_email,
            customer_need,
            budget,
            urgency,
            callback_required,
            lead_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_name,
            customer_email,
            customer_need,
            budget,
            urgency,
            callback_required,
            lead_status
        )
    )

    connection.commit()
    connection.close()

    return "Lead saved successfully."


# Tool 2: Get all leads from database
def get_all_leads():

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM leads")

    rows = cursor.fetchall()

    connection.close()

    return rows


# Tool 3: Calculate lead score
def calculate_lead_score(
    has_clear_need,
    has_budget,
    urgent,
    wants_callback
):

    score = 0

    if has_clear_need:
        score += 2

    if has_budget:
        score += 2

    if urgent:
        score += 2

    if wants_callback:
        score += 2

    if score >= 6:
        return "HIGH"

    elif score >= 3:
        return "MEDIUM"

    else:
        return "LOW"