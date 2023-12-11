import os

import openai

current_directory = os.path.dirname(os.path.abspath(__file__))

# Set your OpenAI API key
api_key = os.environ.get("OPENAI_API_KEY")

# Read prompts from a file
with open(f"{current_directory}/prompts/test.md", "r") as file:
    lines = file.readlines()

prompt = "".join(lines)

# Initialize the OpenAI API client
openai.api_key = api_key

# Send prompts to ChatGPT and print the responses
response = openai.Completion.create(
    engine="gpt-3.5-turbo-instruct",
    prompt=prompt,
    temperature=0.0,
    max_tokens=256,  # Adjust as needed
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    n=1,  # Number of responses to generate
    request_timeout=None,
)

print("\n" + "=" * 50)
print(response.choices[0].text)
print("=" * 50 + "\n")
