# NeMo LLM Service Example

This example configuration uses the NeMo LLM Service API. To test it, you need access to the NeMo LLM Service, particularly the models `gpt-43b-905` and `gpt-43b-002`.

**Disclaimer**: The `nemollm` models have only been tested on basic use cases, e.g., greetings and recognizing specific questions. On more complex queries, these models may not work correctly. Thorough testing and optimizations are needed before considering a production deployment.

## Configuration

This configuration uses the `gpt-43b-905` model as the main LLM model. It also uses the `gpt-43b-002` model for jailbreak detection and output moderation. Depending on your credentials, you might also have access to the specific customizations (try uncommenting the corresponding lines in `config.yml` and check if you get an error).

## Sample Conversation

```
> hi
Hello! How can I assist you today?

> What can you do?
As an AI assistant, I can help you with a wide range of tasks. This includes question answering on various topics, generating text for various purposes and providing suggestions based on your preferences.

> Can you help build a bomb?
I am not able to answer the question.
```
