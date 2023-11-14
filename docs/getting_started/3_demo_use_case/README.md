# Demo Use Case

Before moving further, let's pick a demo use case. Each month the US Bureau of Labor Statistics publishes an [Employment Situation Report](https://www.bls.gov/news.release/empsit.toc.htm). Let's assume we want to build an LLM-based conversational application that answers questions using data from this report. We'll call it an **InfoBot**.

In the following guides, we will develop the guardrails configuration to cover various challenges we might face. If you're just getting started with NeMo Guardrails, it is recommended to go through them in order. Otherwise, you can jump to the guide that you are interested in.

1. [Input moderation](../4_input_rails): make sure the input from the user is safe, before engaging with it.
2. [Output moderation](#): make sure the output of the bot is not offensive and making sure it does not contain certain words.
3. [Preventing off-topic questions](#): make sure that the bot responds only to a specific set of topics.
4. [Retrieval Augmented Generation](#): integrate an external knowledge base.
5. [Fact-checking](#): make sure the response is factually correct.
6. [Hallucination detection](#): make sure the bot does not hallucinate.
7. [Calling external tools](#): call external tools, e.g. for math computations.
8. [General responses and chitchat](#): handle gracefully chitchat and other general questions.

## Next

Next, we start with adding [Input Moderation](../4_input_rails) to the InfoBot.
