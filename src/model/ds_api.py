"""
File: weekday_calculator.py
Authors: Weijian(David)
Date: 2025-01-25
Description:
Use Deepseek to return the logic statement, and create the truth table
"""
from openai import OpenAI

def deepseek(user_input, system_prompt):
    """
    function name: deepseek
    input: user_input-->str
    output: return message-->str
    Call deepseek API
    """
    print("Calling deepseek API.")
    client = OpenAI(api_key="sk-48b305a73fe14ff2bb9f06f05c78f2ae", base_url="https://api.deepseek.com")
    system_prompt = f"""
            You are an expert email analyzer with years of experience in professional communication. 
            {system_prompt}
            """
    response = client.chat.completions.create(
        model="deepseek-chat",
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