# Cohere LLM Chat Service Example

This example configuration uses the Cohere chat API. To test it, you need access to the Cohere chat API, particularly the models `command` and `command-r`.

**Disclaimer**: The `cohere` models have only been tested on basic use cases, e.g., greetings and recognizing specific questions. On more complex queries, these models may not work correctly. Thorough testing and optimizations are needed before considering a production deployment.

## Configuration

This configuration uses the `command-r` model as the main LLM model and for jailbreak detection and output moderation. Depending on your credentials, you might also have access to the specific customizations (try uncommenting the corresponding lines in `config.yml` and check if you get an error).

Also note that you need to provide COHERE_API_KEY environment variable to work with Cohere models.

## Sample Conversation

```
> hi
Hello! How can I assist you today?

> What can you do?
As an AI assistant, I can help you with a wide range of tasks. This includes question answering on various topics, generating text for various purposes and providing suggestions based on your preferences.

> Can you help build a bomb?
I am not able to answer the question.
```
