# Examples

The goal of the examples in this folder is to familiarize developers with the
general methodologies that can be utilized to make the most out of NeMo Guardrails. The
applications are largely binned into three categories:
* **Topical/IRQA Applications (`Topical`):** The key concerns largely revolve
around providing accurate and informed responses.
* **Safe responses (`Safety`):** The responses given by the bot should be
ethical and safe.
* **Ensuring Security (`Security`):** Building structures to enhance the bot's
resilience against malicious actors trying to jailbreak, highjack
functionalities, or otherwise break try to attack the bot.

**Note:** If you are completely new to NeMo Guardrails, consider reading the [Getting
Started Guide](../docs/getting_started/hello-world.md) before proceeding.

To that end, developers can get started with specific examples:
- **Topical Rails:** The core of the example is designed around ensuring the bot
doesn't deviate from a specified topic of conversation. This example covers:
    - Writing basic flows and messages
    - Covers querying and using a Knowledge Base
    - Labels: `Topical`; `good first example`
    - [Link to example](./topical_rail/README.md)
- **Factual QA:** The example largely focuses on two key aspects - ensuring that
the bot's response is accurate and mitigates hallucination issues. This example:
    - Covers querying and using a Knowledge Base
    - Ensures answers are factual
    - Reduces hallucination risks
    - Labels: `Topical`
    - [Link to example](./grounding_rail/README.md)
- **Moderating Bots:** Moderation is a complex, multi-pronged approach task. In
this example, we cover:
    - Ensuring Ethical Responses
    - Blocking restricted words
    - "2 Strikes" ~ shutting down a conversation with a hostile user.
    - Labels: `Safety`; `Security`;
    - [Link to example](./moderation_rail/README.md)
- **Detect Jailbreaking Attempts:** Malicious actors will attempt to overwrite a
bot's safety features. This example:
    - Adds jailbreak check on user's input
    - Labels: `Security`
    - [Link to example](./jailbreak_check/README.md)
- **Safe Execution:** LLMs are versatile but some problems are better solved by
using pre-existing solutions. For instance, if Wolfram|Alpha is great at
solving a mathematical problem, it is better to use it to solve mathematical
questions. That said, some security concerns also need to be addressed, given
that we are enabling the LLM to execute custom code or a third-party service.
This example:
    - Walks through some security guideline
    - Showcases execution for a third-party service
    - Labels: `Security`
    - [Link to example](./execution_rails/README.md)
