import requests
import sys
import threading
import time
import yaml


class Chatbot:
    def __init__(self):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.api_key = config["api_key"]
        self.base_url = config["model_server_base_url"]
        self.workspace_slug = config["workspace_slug"]

        self.chat_url = f"{self.base_url}/workspace/{self.workspace_slug}/chat"

        self.message_history = []

    def run(self, user_message, system_prompt = None) -> None:
        """
        Run the chat application loop. The user can type messages to chat with the assistant.
        """
        try:
            print("Agent: " + self.chat(user_message, system_prompt))
        except Exception as e:
            print("Error! Check the model is correctly loaded. More details in README troubleshooting section.")
            sys.exit(f"Error details: {e}")
            

    def chat(self, message_inside: str, system_prompt = None) -> str:
        """
        Send a chat request to the model server and return the response
        
        Inputs:
        - message: The message to send to the chatbot
        """

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key
        }
        message = f"""
            SYSTEM: You are an expert email analyzer with years of experience in professional communication. 
            {system_prompt}
            
            Email: {message_inside}
            """
        
        self.message_history.append({
            "role": "user",
            "content": message
        })

        # create a short term memory bank with system prompt
        short_term_memory = self.message_history[-2:]

        data = {
            "message": message,
            "mode": "chat",
            "sessionId": "example-session-id",
            "attachments": [],
            "history": short_term_memory
        }

        print(data)

        chat_response = requests.post(
            self.chat_url,
            headers=headers,
            json=data
        )

        try:
            text_response = chat_response.json()['textResponse']
            self.message_history.append({
                "role": "assistant",
                "content": text_response
            })
            return text_response
        except ValueError:
            return "Response is not valid JSON"
        except Exception as e:
            return f"Chat request failed. Error: {e}"

if __name__ == '__main__':
    # stop_loading = False
    chatbot = Chatbot()
    system_msg = """
    Your role is to craft clear, effective, and appropriate email responses based on provided analysis.

            As an email response drafter, using this analysis:
            Create a professional email response that:
            1. Addresses all key points
            2. Matches the appropriate tone
            3. Includes clear next steps
    """

    content = """
        Subject: Project Update Request
        Hi team, I hope this email finds you well. Could you please provide an update
        on the current status of the ML project? We need to know the timeline for
        the next deliverable. Thanks!
        """
    
    chatbot.run(content, system_msg)