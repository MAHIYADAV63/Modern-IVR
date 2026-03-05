from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
import json

app = FastAPI()
load_dotenv()

# 🔐 Use Environment Variables (SAFE METHOD)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@app.get("/")
async def root():
    return {"message": "Server Running"}


@app.api_route("/voice", methods=["GET", "POST"])
async def voice(request: Request):
    response = VoiceResponse()
    response.say("Welcome to Smart IVR. Please say your request after the beep.")

    response.record(
        action="/process",
        method="POST",
        maxLength=5,
        playBeep=True
    )

    return Response(content=str(response), media_type="application/xml")



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


@app.post("/process")
async def process(simulated_text: str = Form(None)):
    user_text = simulated_text.lower() if simulated_text else ""

    if "pnr" in user_text:
        result = get_pnr_status("PNR123")
    elif "train" in user_text:
        result = get_train_timing("12345")
    else:
        result = "Sorry, I did not understand your request."

    response = VoiceResponse()
    response.say(result)
    response.hangup()

    return Response(content=str(response), media_type="application/xml")


# @app.get("/trigger-call")
# async def trigger_call():
#     call = client.calls.create(
#         to="+91xxxxxxxxxx",  
#         from_=TWILIO_NUMBER,
#         url="https://tonie-superficial-formally.ngrok-free.dev/voice"
#     )

#     return {"call_sid": call.sid, "status": call.status}

@app.get("/trigger-call")
async def trigger_call():
    call = client.calls.create(
        to="+91xxxxxxxxxx",   
        from_=TWILIO_NUMBER,
        url="https://tonie-superficial-formally.ngrok-free.dev/voice"
    )
    return {"call_sid": call.sid, "status": call.status}
