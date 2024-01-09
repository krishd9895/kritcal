import requests
import phonenumbers
import telebot
import os
from webserver import keep_alive
import time
import datetime

telegram_token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(telegram_token)

# Initialize the bot
bot = telebot.TeleBot(telegram_token)

# API keys
api_keys = [
    os.environ["API_KEY1"],
    os.environ["API_KEY2"],
    os.environ["API_KEY3"],
    os.environ["API_KEY4"],
    os.environ["API_KEY5"]
]

url = "https://truecaller4.p.rapidapi.com/api/v1/getDetails"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Please enter a phone number to get details.")

@bot.message_handler(func=lambda message: True)
def get_phone_details(message):
    if not message.text.startswith("+"):
        bot.reply_to(message, "Please enter a valid phone number starting with a '+' sign.")
        return

    phone_number = message.text.strip()

    try:
        parsed_number = phonenumbers.parse(phone_number, None)
    except phonenumbers.phonenumberutil.NumberParseException:
        bot.reply_to(message, "Please enter a valid phone number.")
        return

    ack_message = bot.send_message(message.chat.id, "Retrieving details...")

    querystring = {"phone": phone_number, "countryCode": phonenumbers.region_code_for_number(parsed_number)}

    response = None
    api_key_used = None

    for api_key in api_keys:
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "truecaller4.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            response.raise_for_status()  # Raise an exception for non-2xx status codes
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            print(f"API request failed: {e}")
            continue  # Move to the next API key

        data = response.json()

        if "data" in data:
            api_key_used = api_key
            break  # Successful response received, exit the loop

    if response is None:
        bot.reply_to(message, "All API keys failed. Unable to retrieve details.")
    else:
        if "data" in data:
            if len(data["data"]) > 0:
                name = data["data"][0].get("name")
                if name:
                    response_message = f"Name: {name}"

                    if "image" in data["data"][0]:
                        image_url = data["data"][0]["image"]
                        response_message += f"\nImage URL: {image_url}"

                    if "businessProfile" in data["data"][0]:
                        business_profile = data["data"][0]["businessProfile"]
                        if "businessMessages" in business_profile:
                            business_messages = business_profile["businessMessages"]
                            if business_messages:
                                text = business_messages[0]["text"]
                                response_message += f"\nText: {text}"
                            else:
                                response_message += "\nBusiness profile text not available"

                    bot.edit_message_text(chat_id=ack_message.chat.id, message_id=ack_message.message_id, text=response_message)
                else:
                    bot.edit_message_text(chat_id=ack_message.chat.id, message_id=ack_message.message_id, text="No details found for the provided phone number.")
            else:
                bot.edit_message_text(chat_id=ack_message.chat.id, message_id=ack_message.message_id, text="No details found for the provided phone number.")
        else:
            bot.edit_message_text(chat_id=ack_message.chat.id, message_id=ack_message.message_id, text="Unable to retrieve details. Please try again later.")


# Start the bot
keep_alive()

while True:
    try:
        bot.polling(none_stop=True, timeout=30)
    except Exception as e:
        print(f"Bot polling error occurred: {e}")
        time.sleep(10)  # Wait for 10 seconds before restarting the bot polling
          
