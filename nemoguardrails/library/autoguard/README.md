# AutoGuard

This package implements the AutoGuard API integration.

AutoGuard comes with a library of built-in guardrails that you can easily use:

1. [Confidential Detection](#confidential-detection)
2. [Gender bias Detection](#gender-bias-detection)
3. [Harm Detection](#harm-detection)
4. [Toxicity detection](#toxicity-detection)
5. [Racial bias Detection](#racial-bias-detection)
6. [Jailbreak Detection](#jailbreak-detection)
7. Factcheck
8. PII

## Usage (AutoGuard)

To use the autoguard's guardrails:

You have to first select the guardrails that you want to activate for input and output respectively. After that add the guardrails' names to the set of configured guardrails for input and output sections of the `autoguard` section in `config.yml` file:

```yaml
rails:
  config:
    autoguard:
      parameters:
        endpoint: "http://35.225.99.81:8888/guardrail"
      input:
        guardrails:
          - racial_bias_detection
          - gender_bias_detection
          - confidential_detection
          - harm_detection
          - text_toxicity_extraction
          - jailbreak_detection
        matching_scores:
          {"racial_bias_detection": {"score": 0.5}, "gender_bias_detection": {"score": 0.5}}
      output:
        guardrails:
          - racial_bias_detection
          - gender_bias_detection
          - confidential_detection
          - harm_detection
          - text_toxicity_extraction
          - jailbreak_detection

```
We also have to add the autoguard's endpoint in parameters.
One of the advanced configs is matching score which determine whether the guardrail will block the input/output or not.

The colang file has to be in the following format:

```colang
define subflow output autoguard
    $result = execute autoguard_api
    if $result[0] == True
        bot refuse to respond autoguard
        stop

define bot refuse to respond autoguard
    "$result[1] has been detected by AutoGuard; Sorry, can't process."
```

### Confidential detection

The goal of the confidential detection rail is to determine if the text has any kind of confidential information. This rail can be applied at both input and output. This guardrail can be added by adding `confidential_detection` in `autoguard` section in `config.yml`

### Gender bias detection

The goal of the gender bias detection rail is to determine if the text has any kind of gender biased content. This rail can be applied at both input and output. This guardrail can be added by adding `gender_bias_detection` in `autoguard` section in `config.yml`

### Harm detection

The goal of the harm detection rail is to determine if the text has any kind of harm to human content. This rail can be applied at both input and output. This guardrail can be added by adding `harm_detection` in `autoguard` section in `config.yml`

### Toxicity extraction

The goal of the toxicity detection rail is to determine if the text has any kind of toxic content. This rail can be applied at both input and output.This guardrail can be added by adding `text_toxicity_extraction` in `autoguard` section in `config.yml`.
This guardrail not just detects the toxicity of the text but also extracts toxic phrases from the text.

### Racial bias detection

The goal of the racial bias detection rail is to determine if the text has any kind of racially biased content. This rail can be applied at both input and output.
This guardrail can be added by adding `racial_bias_detection` in `autoguard` section in `config.yml`

### Jailbreak detection

The goal of the jailbreak detection rail is to determine if the text has any kind of jailbreak attempt.
This rail can be applied at both input and output.This guardrail can be added by adding `jailbreak_detection` in `autoguard` section in `config.yml`

## Usage (AutoGuard PII)

To use AutoGuard's PII (Personal Identifiable Information) module, you have to list the entities that you wish to redact in following format:

```yaml
rails:
  config:
    autoguard:
      parameters:
        endpoint: "http://35.225.99.81:8888/guardrail"
      entities:
        - "[PERSON NAME]"
        - "[LOCATION]"
        - "[DATE OF BIRTH]"
        - "[DATE]"
        - "[PHONE NUMBER]"
        - "[EMAIL ADDRESS]"
        - "[CREDIT CARD NUMBER]"
        - "[BANK ACCOUNT NUMBER]"
        - "[SOCIAL SECURITY NUMBER]"
        - "[MONEY]"
        - "[INSURANCE POLICY NUMBER]"
        - "[PROFESSION]"
        - "[ORGANIZATION]"
        - "[USERNAME]"
        - "[PASSWORD]"
        - "[IP ADDRESS]"
        - "[PASSPORT NUMBER]"
        - "[DRIVER LICENSE NUMBER]"
        - "[API_KEY]"
        - "[TRANSACTION_ID]"
      contextual_rules:
        - ["[PERSON NAME]", "[CREDIT CARD NUMBER]", "[BANK ACCOUNT NUMBER]"]
        - ["[PERSON NAME]", "[EMAIL ADDRESS]", "[DATE OF BIRTH]"]
        - ["[PERSON NAME]", "[EMAIL ADDRESS]", "[LOCATION]", "[SOCIAL SECURITY NUMBER]"]
      matching_rules:
        {"pii_fast": {
          "[PERSON NAME]": 0.5,
          "[LOCATION]": 0.5,
          "[DATE OF BIRTH]": 0.5,
          "[DATE]": 0.5,
          "[PHONE NUMBER]": 0.5,
          "[EMAIL ADDRESS]": 0.5,
          "[CREDIT CARD NUMBER]": 0.5,
          "[BANK ACCOUNT NUMBER]": 0.5,
          "[SOCIAL SECURITY NUMBER]": 0.5,
          "[MONEY]": 0.5,
          "[INSURANCE POLICY NUMBER]": 0.5,
          "[PROFESSION]": 0.5,
          "[ORGANIZATION]": 0.5,
          "[USERNAME]": 0.5,
          "[PASSWORD]": 0.5,
          "[IP ADDRESS]": 0.5,
          "[PASSPORT NUMBER]": 0.5,
          "[DRIVER LICENSE NUMBER]": 0.5,
          "[API_KEY]": 0.5,
          "[TRANSACTION_ID]": 0.5,
          "[RELIGION]": 0.5
        }}
  input:
    flows:
      - call autoguard pii
  output:
    flows:
      - autoguard pii output
```
Add the Autoguard's PII endpoint in the parameters section of autoguard config.

One of the advanced configs is matching score which determine whether the guardrail will mask the entity in text or not.

Another config is contextual rules which determine when PII redaction will be active, PII redaction will take place only when one of the contextual rule will be satisfied.

The colang file has to be in the following format:

```colang
define subflow call autoguard pii
    $pii_result = execute autoguard_pii_api

define subflow autoguard pii output
    if $pii_result[0] == True
      $bot_message = $pii_result[1]
```

## Usage (AutoGuard Factcheck)

To use AutoGuard's factcheck module, you have to modify the `config.yml` in the following format:

```yaml
rails:
  config:
    autoguard:
      parameters:
        fact_check_endpoint: "http://35.225.99.81:8888/factcheck"
      matching_rules:
        { "factcheck": {"score": 0.5}}
  output:
    flows:
      - check facts autoguard
```

Specify the factcheck endpoint the parameters section of autoguard's config.

Following is the format of the colang file:
```colang
define subflow output autoguard factcheck
    $result = execute autoguard_factcheck_api
    if $result < 0.5
        bot refuse to respond autoguard factcheck
        stop

define bot refuse to respond autoguard factcheck
    "Factcheck violation has been detected by AutoGuard."
```
The output of the factcheck endpoint provides you with a factcheck score against which we can add a threshold which determines whether the given output is factually correct or not.
