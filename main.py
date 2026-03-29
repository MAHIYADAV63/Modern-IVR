from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import os
import json
import random
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Gemini AI setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Session + booking storage
sessions = {}
BOOKING_FILE = "temp_booking.json"


def load_bookings():
    if os.path.exists(BOOKING_FILE):
        try:
            with open(BOOKING_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_bookings(data):
    with open(BOOKING_FILE, "w") as f:
        json.dump(data, f, indent=4)


bookings = load_bookings()


@app.get("/")
async def root():
    return {"message": "Server Running"}


# -------------------- IVR START --------------------

@app.api_route("/voice", methods=["GET", "POST"])
async def voice():
    response = VoiceResponse()

    gather = Gather(
        input="speech dtmf",
        action="/process-intent",
        method="POST",
        speechTimeout="auto"
    )

    gather.say("Welcome to Smart IVR. You can ask about PNR status, train timing, or booking.")

    response.append(gather)
    return Response(str(response), media_type="application/xml")


# -------------------- DATA FUNCTIONS --------------------

def get_pnr_status(pnr):
    with open("irctc.json") as f:
        data = json.load(f)

    if pnr in data:
        ticket = data[pnr]
        return f"Your ticket is {ticket['status']} in coach {ticket['coach']} seat {ticket['seat']}."

    return "PNR not found."


def get_train_timing(train_no):
    with open("irctc.json") as f:
        data = json.load(f)

    if train_no in data:
        train = data[train_no]
        return f"Train departs at {train['departure']} and arrives at {train['arrival']}."

    return "Train not found."


# -------------------- AI INTENT --------------------

def detect_intent(user_text):
    prompt = f"""
    Identify intent:
    PNR_STATUS
    TRAIN_TIMING
    BOOK_TICKET
    CANCEL_TICKET
    UNKNOWN

    User: {user_text}
    """

    res = model.generate_content(prompt)
    return res.text.strip()


# -------------------- MAIN PROCESS --------------------

@app.post("/process-intent")
async def process_intent(
    SpeechResult: str = Form(None),
    Digits: str = Form(None)
):
    user_text = SpeechResult.lower() if SpeechResult else ""

    intent = detect_intent(user_text)

    if intent == "PNR_STATUS":
        result = get_pnr_status("PNR123")

    elif intent == "TRAIN_TIMING":
        result = get_train_timing("12345")

    elif intent == "BOOK_TICKET":
        return Response(str(VoiceResponse().redirect("/ask-origin")), media_type="application/xml")

    elif intent == "CANCEL_TICKET":
        return Response(str(VoiceResponse().redirect("/ask-cancel-pnr")), media_type="application/xml")

    else:
        result = "Sorry, I did not understand your request."

    response = VoiceResponse()
    response.say(result)

    return Response(str(response), media_type="application/xml")


# -------------------- BOOKING FLOW --------------------

@app.api_route("/ask-origin", methods=["GET", "POST"])
async def ask_origin():
    response = VoiceResponse()

    gather = Gather(input="speech", action="/process-origin", speechTimeout="auto")
    gather.say("From which station are you travelling?")

    response.append(gather)
    return Response(str(response), media_type="application/xml")


@app.api_route("/process-origin", methods=["GET", "POST"])
async def process_origin(request: Request):
    form = await request.form()

    origin = form.get("SpeechResult")
    call_sid = form.get("CallSid")

    sessions.setdefault(call_sid, {})
    sessions[call_sid]["origin"] = origin

    response = VoiceResponse()

    gather = Gather(input="speech", action="/process-destination", speechTimeout="auto")
    gather.say("Where do you want to travel?")

    response.append(gather)
    return Response(str(response), media_type="application/xml")


@app.api_route("/process-destination", methods=["GET", "POST"])
async def process_destination(request: Request):
    form = await request.form()

    destination = form.get("SpeechResult")
    call_sid = form.get("CallSid")

    sessions[call_sid]["destination"] = destination

    response = VoiceResponse()

    gather = Gather(input="speech", action="/process-date", speechTimeout="auto")
    gather.say("What date do you want to travel?")

    response.append(gather)
    return Response(str(response), media_type="application/xml")


@app.api_route("/process-date", methods=["GET", "POST"])
async def process_date(request: Request):
    form = await request.form()

    date = form.get("SpeechResult")
    call_sid = form.get("CallSid")

    sessions[call_sid]["date"] = date

    response = VoiceResponse()

    gather = Gather(input="speech", action="/process-class", speechTimeout="auto")
    gather.say("Which class do you want?")

    response.append(gather)
    return Response(str(response), media_type="application/xml")


@app.api_route("/process-class", methods=["GET", "POST"])
async def process_class(request: Request):
    form = await request.form()

    travel_class = form.get("SpeechResult")
    call_sid = form.get("CallSid")

    sessions[call_sid]["class"] = travel_class

    data = sessions[call_sid]

    response = VoiceResponse()

    gather = Gather(input="speech dtmf", action="/confirm-booking")

    gather.say(
        f"Travel from {data['origin']} to {data['destination']} on {data['date']} "
        f"in {travel_class} class. Say yes to confirm."
    )

    response.append(gather)
    return Response(str(response), media_type="application/xml")


@app.api_route("/confirm-booking", methods=["GET", "POST"])
async def confirm_booking(request: Request):
    form = await request.form()

    speech = (form.get("SpeechResult") or "").lower()
    call_sid = form.get("CallSid")

    response = VoiceResponse()

    if "yes" in speech:
        pnr = str(random.randint(1000000000, 9999999999))

        bookings[pnr] = {**sessions[call_sid], "status": "Booked"}
        save_bookings(bookings)

        response.say(f"Booking successful. Your PNR is {pnr}.")
    else:
        response.say("Booking cancelled.")

    return Response(str(response), media_type="application/xml")


# -------------------- CANCEL --------------------

@app.api_route("/ask-cancel-pnr", methods=["GET", "POST"])
async def ask_cancel():
    response = VoiceResponse()

    gather = Gather(input="speech dtmf", action="/cancel-ticket")
    gather.say("Enter your PNR number")

    response.append(gather)
    return Response(str(response), media_type="application/xml")


@app.api_route("/cancel-ticket", methods=["GET", "POST"])
async def cancel_ticket(request: Request):
    form = await request.form()

    pnr = form.get("Digits")

    response = VoiceResponse()

    if pnr in bookings:
        bookings[pnr]["status"] = "Cancelled"
        save_bookings(bookings)
        response.say("Ticket cancelled successfully.")
    else:
        response.say("Invalid PNR.")

    return Response(str(response), media_type="application/xml")


# -------------------- CALL TRIGGER --------------------

@app.get("/trigger-call")
async def trigger_call():
    call = client.calls.create(
        to="+91xxxxxxxxxx",
        from_=TWILIO_NUMBER,
        url="https://your-ngrok-url/voice"
    )

    return {"call_sid": call.sid}