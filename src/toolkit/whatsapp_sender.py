from twilio.rest import Client
 
def whatsapp_sender(message_body):
    account_sid = 'AC668a33783b2bec836426c8006e99ab8d'
    auth_token = 'c6c0e3041dad58dabda400dba1e19f73'
    client = Client(account_sid, auth_token)
 
    message = client.messages.create(
        body=message_body,
        from_='whatsapp:+14155238886',  # Sandbox 中的发送号码
        to='whatsapp:+17787726590'  # 你在 Sandbox 中加入的手机号码
    )
 
    print("Message SID:", message.sid)
 
if __name__ == "__main__":
    message_body = "This is a test message from fiveguys."
    whatsapp_sender(message_body)