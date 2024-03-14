# Using LLMs hosted on Vertex AI

This guide shows an example that queries LLMs hosted on Vertex AI. This guide includes an example GuardRails configuration that is a variation of the ABC bot defined in the the [Getting Started Guide](../../../getting_started/README.md). The only change is that this changes the model being used `gemini-1.0-pro` using the `vertexai` engine.

This guide assumes you have configured and tested direct programmatic querying of Vertex AI models. If not, refer to [this guide](../../advanced/vertexai-setup.md).

The following additional python libraries are needed to use Vertex AI with GuardRails.

```bash
pip install google-cloud-aiplatform>=1.38.0
pip install langchain-google-vertexai==0.1.0
```

Copy the ABC bot into a subdirectory called `config`

```bash
cp -r ../../../../examples/bots/abc config
```

Open `config/config.yml` and edit the `models` portion as follows:

```yaml
models:
  - type: main
    engine: vertexai
    model: gemini-1.0-pro
```

Test the model with ABC rails in place.

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

Note that the bot follows the provided rails and responds as the ABC bot.
