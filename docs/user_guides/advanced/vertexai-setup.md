# Vertex AI Setup

This guide outlines how to get set up Vertex AI enabling calling of Vertex AI APIs from code.

In order to use Vertex AI, you need to perform some initial setup with the Google Cloud Platform (GCP).

1. Create a GCP account: The following [page](https://cloud.google.com/docs/get-started) provides more information about the Google Cloud Platform and how to get started. In your account [create a project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) and [set up billing for it](https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_an_existing_project)
2. Install the `gcloud` CLI ([guide](https://cloud.google.com/sdk/docs/install)). Note that although 3.8 - 3.12 are listed as supported, [this error](https://stackoverflow.com/questions/77316716/gcloud-modulenotfounderror-no-module-named-imp) occurs on Python 3.12. This guide was tested using Python 3.10.2.
3. Create a service account following [this guide](https://cloud.google.com/iam/docs/service-accounts-create) and grant it the role of `Vertex AI Service Agent`.
4. Create and download a service account key for the service account ([guide](https://cloud.google.com/iam/docs/keys-create-delete)).
5. Enable the Vertex AI API ([guide](https://cloud.google.com/vertex-ai/docs/start/cloud-environment#:~:text=Enable%20Vertex%20AI%20APIs,-In%20the%20Google&text=Click%20Enable%20All%20Recommended%20APIs,the%20APIs%20are%20being%20enabled.))
6. Install additional python libraries needed to call Vertex AI using `pip install google-cloud-aiplatform>=1.38.0`

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
Gemini: The United States of America, commonly known as the United States or America, is a country primarily located in North America. It is the world's third-most populous country, the third-largest country by land area, and the most populous and largest country in the Americas.

**Geography:**

* **Location:** North America
* **Area:** 9,833,517 sq km (3,800,583 sq mi)
* **Coastline:** 19,924 km (12,382 mi)
* **Highest point:** Mount Denali, Alaska (6,190 m or 20,310 ft)
* **Lowest point:** Death Valley, California (-86 m or -282 ft)

**Demographics:**

* **Population:** 335.4 million (2023 est.)
* **Ethnic groups:** White (76.3%), Hispanic or Latino (18.7%), Black or African American (13.4%), Asian (6%), American Indian and Alaska Native (1.3%)
* **Languages:** English (official), Spanish (widely spoken)

**History:**

* **1492:** European exploration and colonization begins
* **1776:** Declaration of Independence from Great Britain
* **1783:** Treaty of Paris ends the American Revolutionary War
* **1861-1865:** American Civil War
* **1917:** Entry into World War I
* **1941:** Entry into World War II
* **1945:** Atomic bombs dropped on Japan, ending World War II
* **1950-1953:** Korean War
* **1960-1975:** Vietnam War

**Government and Politics:**

* **Type:** Federal republic
* **Capital:** Washington, D.C.
* **President:** Joseph R. Biden Jr.
* **Legislature:** Congress (Senate and House of Representatives)

**Economy:**

* **GDP (nominal):** $26.49 trillion (2023 est.)
* **Currency:** US dollar ($)
* **Major industries:** Manufacturing, technology, healthcare, finance, agriculture

**Culture:**

* **Arts:** Literature, music, film, dance, visual arts
* **Sports:** American football, baseball, basketball, hockey, soccer
* **Cuisine:** Diverse, including American, Mexican, Italian, Chinese, and many others
* **Religion:** Predominantly Christian, with significant minority religions such as Judaism, Islam, and Hinduism

**Important Facts:**

* The United States is a melting pot of cultures, with immigrants from all over the world.
* It is a highly developed country with a strong economy, education system, and healthcare system.
* It is a global leader in science and technology, with major advancements in areas such as space exploration and medicine.
* The United States is also a major military power and plays a significant role in international affairs.
------
User: Where was its 44th president born?
Gemini: The 44th president of the United States, Barack Obama, was born in Honolulu, Hawaii, on August 4, 1961.
------
```
