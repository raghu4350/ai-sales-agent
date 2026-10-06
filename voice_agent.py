import os

from flask import Flask, request, Response
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse, Gather

from agent import (
    get_agent_response,
    is_end_of_call,
    finalize_lead,
    clear_call_memory
)


# --------------------------------------------------
# 1. Setup
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")

if not PUBLIC_BASE_URL:
    raise ValueError("PUBLIC_BASE_URL is missing from .env")

PUBLIC_BASE_URL = PUBLIC_BASE_URL.rstrip("/")


# --------------------------------------------------
# 2. Helper: Create a Gather (listen for speech)
#
# speech_timeout=2 → stop listening 2 sec after
#   the customer stops talking (natural pause)
# timeout=6 → wait up to 6 sec for them to start
# action_on_empty_result=True → don't hang up if
#   nothing is heard; send to /process-speech anyway
# --------------------------------------------------

def create_gather():
    return Gather(
        input="speech",
        action=f"{PUBLIC_BASE_URL}/process-speech",
        method="POST",
        language="en-IN",           # Indian English
        enhanced=True,              # Twilio high-accuracy Deepgram model
        speech_timeout="auto",      # Twilio decides when you stop speaking (more natural)
        timeout=8,                  # Wait up to 8 sec for caller to START speaking
        action_on_empty_result=True # Don't hang up on silence — re-prompt instead
    )


def xml_response(twiml):
    return Response(str(twiml), mimetype="text/xml")


# --------------------------------------------------
# 3. /voice — Called ONCE when call starts
#
# Greet the customer. Then listen.
# This route is NEVER called again during the call.
# --------------------------------------------------

@app.route("/voice", methods=["GET", "POST"])
def voice():

    print("\n===== CALL STARTED =====")

    response = VoiceResponse()

    gather = create_gather()

    gather.say(
        "Hello. I am your AI sales assistant. "
        "How can I help you today?",
        voice="Polly.Aditi",
        language="en-IN"
    )

    response.append(gather)

    return xml_response(response)


# --------------------------------------------------
# 4. /process-speech — Called after each customer turn
#
# Flow:
# 1. Read SpeechResult from Twilio
# 2. If nothing heard → ask to repeat
# 3. If end-of-call phrase → finalize lead + say goodbye
# 4. Otherwise → get agent reply → say it → listen again
# --------------------------------------------------

@app.route("/process-speech", methods=["POST"])
def process_speech():

    response = VoiceResponse()

    try:

        user_speech = request.form.get("SpeechResult", "").strip()
        confidence = request.form.get("Confidence", "")
        call_sid = request.form.get("CallSid", "unknown_call")

        print("\n===== CUSTOMER INPUT =====")
        print("Call SID  :", call_sid)
        print("Customer  :", user_speech)
        print("Confidence:", confidence)


        # ------------------------------------------
        # Case 1: Nothing heard → ask to repeat
        # ------------------------------------------

        if not user_speech:

            gather = create_gather()

            gather.say(
                "Sorry, I did not catch that. "
                "Could you please say that again?",
                voice="Polly.Aditi",
                language="en-IN"
            )

            response.append(gather)

            return xml_response(response)


        # ------------------------------------------
        # Case 2: End-of-call phrase detected
        # → finalize lead → save → goodbye → hang up
        # ------------------------------------------

        if is_end_of_call(user_speech):

            print("\n===== END OF CALL DETECTED =====")

            # Run the lead save pipeline in background
            try:
                finalize_lead(call_sid)
            except Exception as e:
                print("FINALIZE ERROR:", e)

            # Clear call memory
            clear_call_memory(call_sid)

            response.say(
                "Thank you for speaking with us. "
                "We have noted your details and will get back to you. "
                "Have a great day. Goodbye.",
                voice="Polly.Aditi",
                language="en-IN"
            )

            response.hangup()

            return xml_response(response)


        # ------------------------------------------
        # Case 3: Normal turn
        # → get agent reply → say it → listen again
        # ------------------------------------------

        agent_reply = get_agent_response(call_sid, user_speech)

        if not agent_reply:
            agent_reply = "Sorry, could you please repeat that?"

        agent_reply = agent_reply.strip()

        print("\n===== AGENT RESPONSE =====")
        print(agent_reply)

        # Build: Say the reply, then immediately Gather (listen)
        # This creates the loop: speak → listen → speak → listen
        gather = create_gather()

        gather.say(
            agent_reply,
            voice="Polly.Aditi",
            language="en-IN"
        )

        response.append(gather)

        return xml_response(response)


    except Exception as error:

        print("\n===== ERROR =====")
        print(type(error).__name__)
        print(str(error))

        gather = create_gather()

        gather.say(
            "Sorry, something went wrong on my end. "
            "Please say that again.",
            voice="Polly.Aditi",
            language="en-IN"
        )

        response.append(gather)

        return xml_response(response)


# --------------------------------------------------
# 5. Run Flask
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )