from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
import json
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@app.get("/")
async def root():
    return {"message": "Server Running"}


# IVR Entry Point
@app.api_route("/voice", methods=["GET", "POST"])
async def voice(request: Request):

    response = VoiceResponse()

    gather = response.gather(
        input="speech dtmf",
        action="/process",
        method="POST",
        speechTimeout="auto",
        numDigits=1
    )

    gather.say(
        "Welcome to Smart IVR. You can ask about PNR status or train timing."
    )

    return Response(content=str(response), media_type="application/xml")


<<<<<<< HEAD

=======
# Read PNR status
>>>>>>> d4ff8e21 (Milestone 3: Conversational AI IVR with Gemini integration)
def get_pnr_status(pnr):

    with open("irctc.json") as f:
        data = json.load(f)

    if pnr in data:
        ticket = data[pnr]

        return f"Your ticket is {ticket['status']} in coach {ticket['coach']} seat {ticket['seat']}."

    return "PNR not found."


# Read Train timing
def get_train_timing(train_no):

    with open("irctc.json") as f:
        data = json.load(f)

    if train_no in data:
        train = data[train_no]

        return f"Train departs at {train['departure']} and arrives at {train['arrival']}."

    return "Train not found."


# Gemini AI Intent Detection
def detect_intent(user_text):

    prompt = f"""
    You are an assistant for a railway IVR system.

    Identify the user intent.

    Possible intents:
    PNR_STATUS
    TRAIN_TIMING
    UNKNOWN

    User message: {user_text}

    Respond with only the intent name.
    """

    ai_response = model.generate_content(prompt)

    return ai_response.text.strip()


# Process user request
@app.post("/process")
async def process(
    SpeechResult: str = Form(None),
    Digits: str = Form(None)
):

    user_text = ""

    if SpeechResult:
        user_text = SpeechResult.lower()

    elif Digits:
        user_text = "pnr status"

    intent = detect_intent(user_text)

    if intent == "PNR_STATUS":
        result = get_pnr_status("PNR123")

    elif intent == "TRAIN_TIMING":
        result = get_train_timing("12345")

    else:
        result = "Sorry, I did not understand your request."

    response = VoiceResponse()
    response.say(result)

    return Response(content=str(response), media_type="application/xml")


<<<<<<< HEAD
# @app.get("/trigger-call")
# async def trigger_call():
#     call = client.calls.create(
#         to="+91xxxxxxxxxx",  
#         from_=TWILIO_NUMBER,
#         url="https://tonie-superficial-formally.ngrok-free.dev/voice"
#     )

#     return {"call_sid": call.sid, "status": call.status}

=======
# Trigger phone call
>>>>>>> d4ff8e21 (Milestone 3: Conversational AI IVR with Gemini integration)
@app.get("/trigger-call")
async def trigger_call():

    call = client.calls.create(
<<<<<<< HEAD
        to="+91xxxxxxxxxx",   
        from_=TWILIO_NUMBER,
        url="https://tonie-superficial-formally.ngrok-free.dev/voice"
    )
    return {"call_sid": call.sid, "status": call.status}
=======
        to="+918501071866",
        from_=TWILIO_NUMBER,
        url="https://tonie-superficial-formally.ngrok-free.dev/voice"
    )

    return {"call_sid": call.sid, "status": call.status}
>>>>>>> d4ff8e21 (Milestone 3: Conversational AI IVR with Gemini integration)
