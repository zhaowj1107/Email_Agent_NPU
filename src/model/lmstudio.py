import sys
from openai import OpenAI


class Chatbot:
    """
    Chatbot class to interact with the model server
    """
    def __init__(self):
        self.client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
        self.model = "deepseek-r1-distill-qwen-7b"
        self.message_history = []

    def prompt_llm(self, message_inside, system_prompt):
        """
        Send a chat request to the model server and return the response
        """
        message_inside = f"""
            SYSTEM: You are an expert email analyzer with years of experience in professional communication. 
            {system_prompt}
            
            Email: {message_inside}
            """

        messages = [
            {"role": "user", "content": message_inside}
        ]

        # Get response from AI
        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages,
        )

        # Parse and display the results
        results = response.choices[0].message.content
        if "<think>" in results and "</think>" in results:
            think_start = results.find("<think>")
            think_end = results.find("</think>") + len("</think>")
            results = results[:think_start] + results[think_end:]
        return results.strip()

    def run(self, user_message, system_prompt = None) -> None:
        """
        Run the chat application loop. The user can type messages to chat with the assistant.
        """
        try:
            print("Agent: " + self.prompt_llm(user_message, system_prompt))
            return self.prompt_llm(user_message, system_prompt)
        except Exception as e:
            print("Error! Check the model is correctly loaded. More details in README troubleshooting section.")
            sys.exit(f"Error details: {e}")

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