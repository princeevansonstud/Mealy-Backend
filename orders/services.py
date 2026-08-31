import base64
import requests
from datetime import datetime
from django.conf import settings


def get_mpesa_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(
        url,
        auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
        timeout=10,
    )
    print(f"MPESA OAuth status: {response.status_code}")
    print(f"MPESA OAuth response: {response.text}")
    response.raise_for_status()
    return response.json().get("access_token")


def initiate_stk_push(phone_number: str, amount: float, order_id: str):
    access_token = get_mpesa_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    formatted_phone = str(phone_number).strip().replace("+", "")
    if formatted_phone.startswith("0"):
        formatted_phone = f"254{formatted_phone[1:]}"

    data_to_encode = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(data_to_encode.encode()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": formatted_phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": formatted_phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"Order-{order_id}",
        "TransactionDesc": f"Payment for Order #{order_id}",
    }

    print(f"MPESA STK push payload: {payload}")

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers, timeout=15)

    print(f"MPESA STK push status: {response.status_code}")
    print(f"MPESA STK push response: {response.text}")

    return response.json()
