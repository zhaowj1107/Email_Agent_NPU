import email_agent.gmail as gm



def main():
    while True:
        email, email_id = gm.monitor_email(email_id)
    gm.monitor_email()
    if gm.monitor_email = True:
        mail = read_email()
        action = mail_category(mail)
        if action == "A":
            email_archieve(mail)
        elif action == "B":
            email_auto(mail)
            if_calendar(email)
        elif action == "C":
            email_calender(mail)

        elif action == "email":
            send_email(mail)

    daily_report()
