# Guardrail Evaluation

The Guardrail Evaluation UI enables you to review your evaluation results.


- Go to <a href="/Review" target="_self">Review</a> to review your evaluation results.
- Go to <a href="/Summary" target="_self">Summary</a> to view your evaluation results.

## Usage

Below is a getting started guide for the `nemoguardrails eval` CLI.

## Run Evaluations

To run a new evaluation with a guardrail configuration:
```bash
nemoguardrails eval run --guardrail-config-path=... --output-path=...
```

## Check Compliance

To check the compliance with the policies, you can use the LLM-as-a-judge method.

```bash
nemoguardrails eval check-compliance --llm-judge=gpt-4 --ouput-path=...
```

You can use any LLM supported by NeMo Guardrails.

```yaml
models:
  - type: llm-judge
    engine: openai
    model: gpt-4

  - type: llm-judge
    engine: nvidia_ai_endpoints
    model: meta/llama3-8b-instruct
```



## Review and Analyze

To review and analyze the results, launch the NeMo Guardrails Eval UI:

```bash
nemoguardrails eval ui
```
