# daily_report.py
import os
import sys
module_path = os.path.abspath("toolkit")
sys.path.append(module_path)
from whatsapp_sender import whatsapp_sender
import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from ALLM_api import Chatbot


def daily_report():
    # 1. Read the logs file content
    try:
        with open("logs.txt", "r", encoding="utf-8") as f:
            logs_content = f.read()
    except Exception as e:
        print("Failed to read logs.txt. Please check if logs.txt exists and if the encoding is correct.")
        return

    # 2. Get today's date in the format YYYY-MM-DD
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # 3. Filter logs to only include entries for today (matching the [YYYY-MM-DD pattern)
    lines = logs_content.splitlines()
    today_logs = [line for line in lines if f"[{today_date}" in line]

    # If there are no logs for today, output a message and exit
    if not today_logs:
        print("No log records for today.")
        return

    # Combine today's logs into a single string
    filtered_logs = "\n".join(today_logs)

    # 4. Initialize Chatbot (model API call)
    chatbot = Chatbot()

    # 5. Define a system prompt instructing the model to generate an email daily report
    system_prompt = (
        """
        Based on the provided log file, please generate a daily email report\n
        in English with the following format:
 
        Email Daily Report (YYYY-MM-DD)
 
        Email Types:
 
        Total Emails: [number]
        Archieved Emails: [number]
        Draft Emails: [number]
        Reply Emails: [number]
        Calendar Events: [number]
        Email Subject Summary:

        Draft Emails:
        - [Draft Email 1]
        - [Draft Email 2]
        - [Draft Email 3]

        Recommendations:
 
        - [Recommendation 1]
        - [Recommendation 2]
        - [Recommendation 3]
        Additional instructions:
 
        Ensure that all section headers \n
        (like "Email Daily Report", "Email Types", "Email Subject Summary", and "Recommendations") are in bold.
        The recommendations section should be concise and include no more than three bullet points.
        The language used should be clear, professional, and well-organized.
    """
    )

    # 6. Call the model to generate the daily report
    report = chatbot.chat(filtered_logs, system_prompt=system_prompt)
    print("Generated daily report:\n", report)

    # 7. Send the generated report via WhatsApp
    whatsapp_sender(report)
    return report

if __name__ == "__main__":
    daily_report()
