import os
import argparse

from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import *
from call_function import call_function
from call_function import available_functions


load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

# check if the API key exists
if api_key is None:
    raise RuntimeError("GEMINI_API_KEY environment variable not found. Please set it in your .env file.")

client = genai.Client(api_key=api_key)

def main():

    parser = argparse.ArgumentParser(description="Chatbot")
    parser.add_argument("user_prompt", type=str, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")


    args = parser.parse_args()

    messages = [
        types.Content(role="user", parts=[types.Part(text=args.user_prompt)])
    ]

    for _ in range(20):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[available_functions],
                system_instruction=system_prompt
            ),
        )

        # ✅ 1. adicionar candidatos ao histórico
        if response.candidates:
            for candidate in response.candidates:
                messages.append(candidate.content)

        function_responses = []

        # ✅ 2. verificar chamadas de função
        if response.function_calls:
            for function_call in response.function_calls:
                function_call_result = call_function(function_call, args.verbose)

                if not function_call_result.parts:
                    raise Exception("No parts returned from function call")

                part = function_call_result.parts[0]

                if part.function_response is None:
                    raise Exception("No function_response in part")

                if part.function_response.response is None:
                    raise Exception("No response in function_response")

                function_responses.append(part)

                if args.verbose:
                    print(f"-> {part.function_response.response}")

            # ✅ 3. adicionar resultado das funções ao histórico
            messages.append(
                types.Content(role="user", parts=function_responses)
            )

        else:
            # ✅ 4. resposta final
            print("Final response:")
            print(response.text)
            break

    else:
        print("Error: Maximum iterations reached without a final response")
        
if __name__ == "__main__":
    main()
