# Guardrails Library

**NOTE: THIS SECTION IS WORK IN PROGRESS.**

NeMo Guardrails comes with a set of pre-built guardrails that you can activate:

> DISCLAIMER: The built-in rails are only intended to enable you to get started quickly with NeMo Guardrails. For production use cases, further development and testing of the rails are needed.

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

This will trigger the fact-checking output rail every time the bot responds to a question about the report (for a complete example, check out [this example config](../../examples/configs/rag/fact_checking)).


## Active Fence

NeMo Guardrails supports using the [ActiveFence ActiveScore API](https://docs.activefence.com/index.html) as an input rail out-of-the-box (you need to have the `ACTIVE_FENCE_API_KEY` environment variable set).

```yaml
rails:
  input:
    flows:
      # The simplified version
      - active fence moderation

      # The detailed version with individual risk scores
      # - active fence moderation detailed
```

The `active fence moderation` flow uses the maximum risk score with the 0.7 threshold to decide if the input should be allowed or not (i.e., if the risk score is above the threshold, it is considered a violation). The `active fence moderation detailed` has individual scores per category of violations.

To customize the scores, you have to overwrite the [default flows](../../nemoguardrails/library/active_fence/flows.co) in your config. For example, to change the threshold for `active fence moderation` you can add the following flow to your config:

```colang
define subflow active fence moderation
  """Guardrail based on the maximum risk score."""
  $result = execute call active fence api

  if $result.max_risk_score > 0.9
    bot inform cannot answer
    stop
```

## Sensitive Data Detection

NeMo Guardrails supports detecting sensitive data out-of-the-box using [Presidio](https://github.com/Microsoft/presidio), which provides fast identification and anonymization modules for private entities in text such as credit card numbers, names, locations, social security numbers, bitcoin wallets, US phone numbers, financial data and more. You can detect sensitive data on user input, bot output or the relevant chunks retrieved from the knowledge base.

### Setup

To use the built-in sensitive data detection rails, you have to install Presidio and download the `en_core_web_lg` model.

```bash
pip install presidio-analyzer presidio-anonymizer
python -m spacy download en_core_web_lg
```

**TODO**: update with alternative installation using `pip install nemoguardrails[sdd]`.

### Configuration

You can activate sensitive data detection in three different ways: input rail, output rail and retrieval rail.

#### Input Rail

To activate a sensitive data detection input rail, you have to configure the entities that you want to detect:

```yaml
rails:
  config:
    sensitive_data_detection:
      input:
        entities:
          - PERSON
          - EMAIL_ADDRESS
          - ...
```

For the full list of supported entities, please refer to [Presidio - Supported Entities](https://microsoft.github.io/presidio/supported_entities/) page.

Also, you have to add the `detect sensitive data on input` or `mask sensitive data on input` flows to the list of input rails:

```yaml
rails:
  input:
    flows:
      - ...
      - mask sensitive data on input     # or 'detect sensitive data on input'
      - ...
```

When using `detect sensitive data on input`, if sensitive data is detected, the bot will refuse to respond to the user's input. When using `mask sensitive data on input` the bot will mask the sensitive parts in the user's input and continue the processing.

#### Output Rail

The configuration for the output rail is very similar to the input rail:

```yaml
rails:
  config:
    sensitive_data_detection:
      output:
        entities:
          - PERSON
          - EMAIL_ADDRESS
          - ...

  output:
    flows:
      - ...
      - mask sensitive data on output     # or 'detect sensitive data on output'
      - ...
```

#### Retrieval Rail

The configuration for the retrieval rail is very similar to the input/output rail:

```yaml
rails:
  config:
    sensitive_data_detection:
      retrieval:
        entities:
          - PERSON
          - EMAIL_ADDRESS
          - ...

  retrieval:
    flows:
      - ...
      - mask sensitive data on retrieval     # or 'detect sensitive data on retrieval'
      - ...
```

### Custom Recognizers

If have custom entities that you want to detect, you can define custom *recognizers*.
For more detail check out this [tutorial](https://microsoft.github.io/presidio/tutorial/08_no_code/) and this [example](https://github.com/microsoft/presidio/blob/main/presidio-analyzer/conf/example_recognizers.yaml).

Below is an example of how you can configure a `TITLE` entity and detect it inside the input rail.

```yaml
rails:
  config:
    sensitive_data_detection:
      recognizers:
        - name: "Titles recognizer"
          supported_language: "en"
          supported_entity: "TITLE"
          deny_list:
            - Mr.
            - Mrs.
            - Ms.
            - Miss
            - Dr.
            - Prof.
      input:
        entities:
          - PERSON
          - TITLE
```

### Custom Detection

If you want to implement a completely different sensitive data detection mechanism, you can override the default actions [`detect_sensitive_data`](../../nemoguardrails/library/sensitive_data_detection/actions.py) and [`mask_sensitive_data`](../../nemoguardrails/library/sensitive_data_detection/actions.py).


## Hallucination detection

**TODO**: document
