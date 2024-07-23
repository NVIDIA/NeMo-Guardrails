# Got It AI Integration

NeMo Guardrails integrates with [Got It AI's Hallucination Manager](https://www.app.got-it.ai/hallucination-manager) for hallucination detection in RAG systems. The Hallucination Manager's TruthChecker API is designed to detect and manage hallucinations in AI models, specifically for real-world RAG applications.

Existing fact-checking methods are not sufficient to detect hallucinations in AI models for real-world RAG applications. The TruthChecker API performs a dual task to determine whether a response is a `hallucination` or not:
1. Check for the faithfulness of the generated response to the retrieved knowledge chunks.
2. Check for the relevance of the response to the user query and the conversation history.

The TruthChecker API can be configured to work for open-domain use-case or for a specific domain or knowledge base. By default, the TruthChecker API is configured to work for open-domain and we expect it to deliver strong performance on specific domains. However, for an enhanced experience for a specific domain or knowledge base, you can fine-tuning the model on the knowledge base and unlock benefits like secure on-premise model deployments.

Please [contact the Got It AI team](https://www.app.got-it.ai/) for more information on how to fine-tune the TruthChecker API for your specific domain or knowledge base.

To integrate the TruthChecker API with NeMo Guardrails, the `GOTITAI_API_KEY` environment variable needs to be set.

```yaml
rails:
  output:
    flows:
      - gotitai rag truthcheck
```

To trigger the fact-checking rail, you have to set the `$check_facts` context variable to `True` before a bot message that requires fact-checking, e.g.:

```colang
define flow
  user ask about report
  $check_facts = True
  bot provide report answer
```
