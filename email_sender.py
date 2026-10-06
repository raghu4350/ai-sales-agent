"""
email_sender.py

Sends a professional HTML email to the CUSTOMER
with a summary of their inquiry after the call ends.

Setup required in .env:
    GMAIL_ADDRESS=your_gmail@gmail.com
    GMAIL_APP_PASSWORD=your_16_char_app_password

How to get Gmail App Password:
    Google Account → Security → 2-Step Verification
    → App Passwords → Mail → Generate
"""

import os
import smtplib
import ssl
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# --- FIX FOR RAILWAY: Force IPv4 ---
# Railway containers often fail with "Network is unreachable"
# because Python tries to connect to Gmail via IPv6.
old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo
# -----------------------------------

load_dotenv()

GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


# --------------------------------------------------
# send_lead_email
#
# Called automatically when the customer says
# goodbye and their email was collected.
#
# Sends a nicely formatted HTML summary to the
# CUSTOMER's email address.
# --------------------------------------------------

def send_lead_email(
    customer_email,
    customer_name,
    customer_need,
    budget,
    urgency,
    callback_required,
    lead_status
):
    """
    Send inquiry summary to the customer's email.
    Returns True on success, False on failure.
    """

    # Check credentials exist
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("EMAIL SKIPPED: Add GMAIL_ADDRESS and GMAIL_APP_PASSWORD to .env")
        return False

    # Check customer email was collected
    if not customer_email or customer_email in ["Not provided", "Unknown", "None", ""]:
        print("EMAIL SKIPPED: No valid customer email was collected during the call.")
        return False

    name = customer_name if customer_name and customer_name not in ["Unknown", "None", "Not provided"] else "Customer"
    callback_text = "Yes" if callback_required else "No"

    # --------------------------------------------------
    # Plain text version (for email clients without HTML)
    # --------------------------------------------------

    plain_text = f"""
Dear {name},

Thank you for speaking with our AI Sales Assistant today.
Below is a summary of the details we discussed during our call.

YOUR INQUIRY SUMMARY
====================
Full Name         : {name}
What You Need     : {customer_need}
Your Budget       : {budget}
When You Need It  : {urgency}
Callback Needed   : {callback_text}
Lead Priority     : {lead_status}

WHAT HAPPENS NEXT
=================
Our team has received your details and will contact you shortly.

If you have any questions, simply reply to this email.

Thank you for your time.

Best regards,
AI Sales Assistant Team
    """.strip()

    # --------------------------------------------------
    # HTML version (looks professional in inbox)
    # --------------------------------------------------

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{
      font-family: Arial, sans-serif;
      background-color: #f4f4f4;
      margin: 0;
      padding: 0;
    }}
    .container {{
      max-width: 580px;
      margin: 30px auto;
      background-color: #ffffff;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .header {{
      background-color: #1a73e8;
      color: white;
      padding: 30px 40px;
      text-align: center;
    }}
    .header h1 {{
      margin: 0;
      font-size: 22px;
      letter-spacing: 1px;
    }}
    .header p {{
      margin: 6px 0 0;
      font-size: 14px;
      opacity: 0.85;
    }}
    .body {{
      padding: 30px 40px;
    }}
    .greeting {{
      font-size: 16px;
      color: #333;
      margin-bottom: 20px;
    }}
    .section-title {{
      font-size: 13px;
      font-weight: bold;
      color: #1a73e8;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin: 24px 0 10px;
      border-bottom: 1px solid #e0e0e0;
      padding-bottom: 6px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    td {{
      padding: 10px 12px;
      font-size: 14px;
      color: #444;
      border-bottom: 1px solid #f0f0f0;
    }}
    td:first-child {{
      font-weight: bold;
      color: #555;
      width: 45%;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: bold;
    }}
    .badge-high   {{ background-color: #d4edda; color: #155724; }}
    .badge-medium {{ background-color: #fff3cd; color: #856404; }}
    .badge-low    {{ background-color: #f8d7da; color: #721c24; }}
    .next-steps {{
      background-color: #f0f7ff;
      border-left: 4px solid #1a73e8;
      padding: 14px 18px;
      border-radius: 4px;
      margin-top: 24px;
      font-size: 14px;
      color: #333;
    }}
    .footer {{
      background-color: #f9f9f9;
      text-align: center;
      padding: 18px;
      font-size: 12px;
      color: #999;
      border-top: 1px solid #eee;
    }}
  </style>
</head>
<body>
  <div class="container">

    <!-- Header -->
    <div class="header">
      <h1>🤖 AI Sales Assistant</h1>
      <p>Your Inquiry Summary</p>
    </div>

    <!-- Body -->
    <div class="body">

      <p class="greeting">Dear <strong>{name}</strong>,</p>
      <p style="font-size:14px; color:#555;">
        Thank you for speaking with our AI Sales Assistant.
        Here is a complete summary of the details we discussed during your call.
      </p>

      <!-- Inquiry Details -->
      <div class="section-title">📋 Your Inquiry Details</div>
      <table>
        <tr>
          <td>Full Name</td>
          <td>{name}</td>
        </tr>
        <tr>
          <td>What You Need</td>
          <td>{customer_need}</td>
        </tr>
        <tr>
          <td>Your Budget</td>
          <td>{budget}</td>
        </tr>
        <tr>
          <td>When You Need It</td>
          <td>{urgency}</td>
        </tr>
        <tr>
          <td>Callback Requested</td>
          <td>{callback_text}</td>
        </tr>
        <tr>
          <td>Lead Priority</td>
          <td>
            <span class="badge badge-{lead_status.lower()}">
              {lead_status}
            </span>
          </td>
        </tr>
      </table>

      <!-- Next Steps -->
      <div class="next-steps">
        <strong>📌 What happens next?</strong><br><br>
        Our team has received your details and will reach out to you shortly
        {"for the callback you requested." if callback_required else "with more information."}
        <br><br>
        If you have any questions, simply reply to this email.
      </div>

    </div>

    <!-- Footer -->
    <div class="footer">
      This is an automated summary from your AI Sales Assistant call.<br>
      © AI Sales Agent
    </div>

  </div>
</body>
</html>
    """.strip()

    # --------------------------------------------------
    # Send email via Gmail SMTP
    # --------------------------------------------------

    try:

        message = MIMEMultipart("alternative")
        message["From"]    = GMAIL_ADDRESS
        message["To"]      = customer_email
        message["Subject"] = f"Your Inquiry Summary — {customer_need}"

        # Attach both versions (email client picks the best one)
        message.attach(MIMEText(plain_text, "plain"))
        message.attach(MIMEText(html, "html"))

        # Use port 587 with STARTTLS (more compatible than 465 SSL)
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, customer_email, message.as_string())

        print(f"EMAIL: Sent successfully to {customer_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("EMAIL ERROR: Gmail login failed.")
        print("  → Make sure GMAIL_APP_PASSWORD is a 16-letter App Password, NOT your regular Gmail password.")
        print("  → Get it: Google Account → Security → 2-Step Verification → App Passwords")
        return False

    except smtplib.SMTPException as e:
        print(f"EMAIL ERROR: SMTP error — {e}")
        return False

    except Exception as e:
        print(f"EMAIL ERROR: {type(e).__name__}: {e}")
        return False
