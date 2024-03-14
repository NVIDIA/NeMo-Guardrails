# Using LLMs hosted on Vertex AI

This guide shows an example that queries LLMs hosted on Vertex AI. This guide includes an example GuardRails configuration that is a variation of the ABC bot defined in the the [Getting Started Guide](../../getting_started). The only change is that this changes the model being used `gemini-1.0-pro` using the `vertexai` engine.

In order to use Vertex AI, you need to perform some initial setup with the Google Cloud Platform (GCP).
1. Create a GCP account: The following [page](https://cloud.google.com/docs/get-started) provides more information about the Google Cloud Platform and how to get started. In your account [create a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) and [set up billing for it](https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_an_existing_project)
2. Install the `gcloud` CLI ([guide](https://cloud.google.com/sdk/docs/install)). Note that although 3.8 - 3.12 are listed as supported, [this error](https://stackoverflow.com/questions/77316716/gcloud-modulenotfounderror-no-module-named-imp) occurs on Python 3.12. This guide was tested using Python 3.10.2.
3. Create a service account following [this guide](https://cloud.google.com/iam/docs/service-accounts-create) and grant it the role of `Vertex AI Service Agent`.
4. Create and download a service account key for the service account ([guide](https://cloud.google.com/iam/docs/keys-create-delete)).
5. Enable the Vertex AI API ([guide](https://cloud.google.com/vertex-ai/docs/start/cloud-environment#:~:text=Enable%20Vertex%20AI%20APIs,-In%20the%20Google&text=Click%20Enable%20All%20Recommended%20APIs,the%20APIs%20are%20being%20enabled.))
6. Install additional python libraries needed to call Vertex AI using `pip install google-cloud-aiplatform>=1.38.0`

The following additional python libraries are needed to use Vertex AI

```bash
pip install google-cloud-aiplatform>=1.38.0
pip install langchain-google-vertexai==0.1.0
```

Test that you are successfully able to call VertexAI APIs using the following snippet:

```python
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "<path>/<to>/<your>/<service>/<account>/<key>.json"

from vertexai.preview.generative_models import GenerativeModel, ChatSession

model = GenerativeModel("gemini-1.0-pro")
chat = model.start_chat()

def get_chat_response(chat: ChatSession, prompt: str):
    response = chat.send_message(prompt)
    return response.text

prompts = [
    "Hi, who are you?",
    "What can you tell me about the United States?",
    "Where was its 44th president born?",
]

for prompt in prompts:
    print("User:", prompt)
    print("Gemini:", get_chat_response(chat, prompt))
    print("------")
```

```
User: Hi, who are you?
Gemini: I am Gemini, a multimodal AI model, developed by Google.
------
User: What can you tell me about the United States?
Gemini: The United States of America, often referred to as the US or America, is a country primarily located in North America. It consists of 50 states, a federal district, five major unincorporated territories, 326 Indian reservations, and nine minor outlying islands. At 3.8 million square miles, the United States is the world's third or fourth-largest country by total area and is slightly smaller than the entire continent of Europe's 3.9 million square miles. With a population of over 332 million, it is the third most populous country in the world. The capital is Washington, D.C., and the most populous city is New York City.

The United States is a federal republic and a representative democracy, in which the government is chosen by the people. The country is divided into three branches of government: the legislative branch, the executive branch, and the judicial branch. The legislative branch is composed of the Senate and the House of Representatives, which together form the United States Congress. The executive branch is led by the President, who is also the commander-in-chief of the armed forces. The judicial branch is composed of the Supreme Court and lower federal courts.

The United States has a diverse economy, with a gross domestic product (GDP) of over $20 trillion. The country is a major exporter of agricultural products, machinery, and technology. The United States is also a major importer of oil and other natural resources.

The United States is a member of the United Nations, NATO, the G7, the G20, and the Organisation for Economic Co-operation and Development (OECD). The country is a permanent member of the United Nations Security Council.

The United States has a long and complex history. The first European settlers arrived in the early 17th century. The United States gained independence from Great Britain in 1776. The country has been involved in a number of wars, including the American Civil War, the Spanish-American War, and World War II.

The United States is a diverse country, with people from all over the world. The country has a rich culture, with a wide variety of music, art, and literature. The United States is also a major center of technology and innovation.
------
User: Where was its 44th president born?
Gemini: The 44th President of the United States, Barack Obama, was born in Honolulu, Hawaii on August 4, 1961.
------
```

Now we can test Vertex AI models with GuardRails. The `config` directory includes a variation of the ABC Bot but calling the Gemini 1.0 Pro model from Vertex AI. The main difference is in the `config.yml` file. The relevant section is
```yaml
models:
  - type: main
    engine: vertexai
    model: gemini-1.0-pro
```
This makes use of the [integration of Vertex AI into LangChain](https://python.langchain.com/docs/integrations/llms/google_vertex_ai_palm) to call Vertex AI models.

```python
import nest_asyncio
nest_asyncio.apply()

from nemoguardrails import RailsConfig
from nemoguardrails import LLMRails

config_path = "config"
config = RailsConfig.from_path(config_path)

rails = LLMRails(config)
user_utt = "Hi, who are you?"
response = rails.generate(messages=[{"role": "user", "content": user_utt}])
print("User:", user_utt)
print("Bot: ", response)
```

```
    Fetching 7 files:   0%|          | 0/7 [00:00<?, ?it/s]

    User: Hi, who are you?
    Bot:  {'role': 'assistant', 'content': "I'm the ABC Bot, a virtual assistant designed to answer your questions about the ABC Company. I'm here to help you with any inquiries you may have about our policies, benefits, and more. How can I assist you today?"}
```

Now the bot follows the provided rails and responds as the ABC bot.
