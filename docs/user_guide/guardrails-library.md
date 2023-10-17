# Guardrails Library

**NOTE: THIS SECTION IS WORK IN PROGRESS.**

NeMo Guardrails comes with a set of pre-built guardrails that you can activate:

- Jailbreak detection
- Output moderation
- Fact-checking
- Sensitive Data Detection
- Hallucination detection
- ActiveFence moderation

## Jailbreak Detection

**TODO**

## Output Moderation

**TODO**

## Fact-Checking

The fact-checking output rail enables you to check the truthfulness of the bot response based on the relevant chunks extracted from the knowledge base.

**TODO**: comment on the relationship with the KB.

### Configuration

To activate the output fact-checking rail you must include the default `check facts` in your `config.yml`:

```yaml
rails:
  output:
    flows:
      - check facts
```

The default implementation of the `check facts` flow invokes the `check_facts` action, which should return a score between `0.0` (response is not accurate) and `1.0` (response is accurate):

```colang
define subflow check facts
  if $check_facts == True
    $check_facts = False

    $accuracy = execute check_facts
    if $accuracy < 0.5
      bot inform answer unknown
      stop
```

The fact-checking only happens when the `$check_facts` context variable is set to `True`.

### Providers

NeMo Guardrails supports two fact-checking providers out of the box:

1. `ask_llm`: prompt the main LLM again to check the response against the `relevant_chunks` extracted from the knowledge base.
2. `align_score`: using the [AlignScore](https://aclanthology.org/2023.acl-long.634.pdf) model.

#### AskLLM

**TODO**: comment on how the LLM is prompted.

#### AlignScore

NeMo Guardrails provides out-of-the-box support for the [AlignScore metric (Zha et al.)](https://aclanthology.org/2023.acl-long.634.pdf), which uses a RoBERTa-based model for scoring factual consistency in model responses with respect to the knowledge base.

In our testing, we observed an average latency of ~220ms on hosting AlignScore as an HTTP service, and ~45ms on direct inference with the model loaded in-memory. This makes it much faster than the `ask_llm` method. We also observe substantial improvements in accuracy over the `ask_llm` method, with a balanced performance on both factual and counterfactual statements. However, this method requires an on-prem deployment of the publicly available AlignScore model. Please see the [AlignScore Deployment](./advanced/align_score_deployment.md) guide for more details.

To use the `align_score` fact-checking you have to set the following configuration options in your `config.yml`:

```yaml
rails:
  config:
    fact_checking:
      # Select AlignScore as the provider
      provider: align_score
      parameters:
        # Point to a running instance of the AlignScore server
        endpoint: "http://localhost:5000/alignscore_large"

  output:
    flows:
      # Enable the `check facts` output rail
      - check facts
```

#### Custom Provider

If you want to use a different method for fact-checking, you can register a new `check_facts` action.

**TODO**: provide an example?

### Usage

To trigger the fact-fact checking rail you have to set the `$check_facts` context variable to `True` before a bot message that requires fact checking. For example:

```colang
define flow
  user ask about report
  $check_facts = True
  bot provide report answer
```

This will trigger the fact-checking output rail every time the bot responds to a question about the report (for a complete example, check out [this example config](../../examples/configs/fact_checking)).
