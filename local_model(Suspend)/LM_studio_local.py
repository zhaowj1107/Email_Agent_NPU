"""
This script is used to test the local model on the local machine.
The local model is used to generate responses for the chatbot."""

import json
import requests
import shutil
import sys
import threading
import time
import urllib.parse
import urllib.request
import itertools
import warnings # suppress warnings
warnings.filterwarnings("ignore")

from openai import OpenAI


# Initialize LM Studio client
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
MODEL = "deepseek-r1-distill-qwen-7b"

def prompt_llm(prompt):
    # Define the conversation with the AI
    messages = [
        {"role": "user", "content": prompt}
    ]

    # Get response from AI
    response = client.chat.completions.create(
        model = "your-model",
        messages = messages,
    )

    # Parse and display the results
    results = response.choices[0].message.content
    if "<think>" in results and "</think>" in results:
        think_start = results.find("<think>")
        think_end = results.find("</think>") + len("</think>")
        results = results[:think_start] + results[think_end:]
    return results.strip()


if __name__ == "__main__":
    # Define the prompt for the AI
    # prompt = "who are u?"
    prompt = "draft me a email about application for Qualcomm AI Hackathon"

    # Get the response from the AI
    response = prompt_llm(prompt)

    # Display the response
    print(response)