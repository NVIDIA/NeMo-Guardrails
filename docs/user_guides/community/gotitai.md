# Got It AI Integration

NeMo Guardrails integrates with [Got It AI's Hallucination Manager](https://www.app.got-it.ai/hallucination-manager) for hallucination detection in RAG systems. The Hallucination Manager's TruthChecker API is designed to detect and manage hallucinations in AI models, specifically for real-world RAG applications.

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
