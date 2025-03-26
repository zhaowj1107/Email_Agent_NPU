"""
File: openrouter_api.py
Description:
    This file contains the function deepseek which calls the deepseek API to get the response.
"""
from openai import OpenAI

def deepseek(user_input, system_prompt):
    """
    function name: deepseek
    input: user_input-->str
    output: return message-->str
    Call deepseek API
    """
    print("Calling openrouter API.")
    client = OpenAI(api_key="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", base_url="https://openrouter.ai/api/v1")
    system_prompt = f"""{system_prompt}"""

    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {"role": "system", "content":system_prompt},
            {"role": "user", "content": user_input},
        ],
        stream=False
    )
    
    infor = response.choices[0].message.content
    return infor
 
if __name__ == '__main__':
    user_input = "What is the logic statement for the weekday calculator?"
    system_prompt = "The logic statement for the weekday calculator is:"
    print(deepseek(user_input, system_prompt))