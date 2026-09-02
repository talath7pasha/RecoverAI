from twilio.rest import Client

TWILIO_ACCOUNT_SID = "AC7536103a4a718fcc073032baca04fb23"
TWILIO_AUTH_TOKEN = "cf96c545ad10d8b4d0755a5d42ce7625"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Twilio WhatsApp Sandbox pre-approved appointment/order notification format
message = client.messages.create(
    from_="whatsapp:+17372212163",
    to="whatsapp:+917483955271",
    body=(
        "Your RecoverAI payment reminder is ready. Tap to view and negotiate: "
        "https://rzp.io/l/recoverai_test"
    ),
)

print(f"Delivered successfully! SID: {message.sid}")