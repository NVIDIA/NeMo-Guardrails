# AutoGuard

This package implements the AutoGuard API integration.

AutoGuard comes with a library of built-in guardrails that you can easily use:

1. [Confidential Detection](#confidential-detection)
2. [Tonal Detection](#tonal-detection)
2. [Gender bias Detection](#gender-bias-detection)
3. [Harm Detection](#harm-detection)
4. [Racial bias Detection](#racial-bias-detection)
5. [Jailbreak Detection](#jailbreak-detection)
6. [Toxicity detection](#toxicity-extraction)
7. [Factcheck](#usage-autoguard-factcheck)
8. [PII](#usage-autoguard-pii)


Note: Toxicity, factcheck and PII are implemented a bit differently, compared to other guardrails.

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
          {"gender_bias_detection": {"score": 0.5}}
        flows:
          - input autoguard
      output:
        guardrails:
          - racial_bias_detection
          - gender_bias_detection
          - confidential_detection
          - harm_detection
          - text_toxicity_extraction
          - jailbreak_detection
        matching_scores:
          {"gender_bias_detection": {"score": 0.5}}
        flows:
          - output autoguard
```
We also have to add the autoguard's endpoint in parameters.

One of the advanced configs is matching score which is a threshold that determines whether the guardrail will block the input/output or not.

The colang file has to be in the following format:

```colang
define subflow input autoguard
    $result = execute autoguard_api
    if $result[0] == True
        bot refuse to respond autoguard
        stop

define subflow output autoguard
    $result = execute autoguard_api
    if $result[0] == True
        bot refuse to respond autoguard
        stop

define bot refuse to respond autoguard
    "$result[1] has been detected by AutoGuard; Sorry, can't process."
```


### Gender bias detection

The goal of the gender bias detection rail is to determine if the text has any kind of gender biased content. This rail can be applied at both input and output.
This guardrail can be added by adding `gender_bias_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.
### Harm detection

The goal of the harm detection rail is to determine if the text has any kind of harm to human content. This rail can be applied at both input and output.
This guardrail can be added by adding `harm_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

### Jailbreak detection

The goal of the jailbreak detection rail is to determine if the text has any kind of jailbreak attempt.
This guardrail can be added by adding `jailbreak_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.


### Confidential detection

The goal of the confidential detection rail is to determine if the text has any kind of confidential information. This rail can be applied at both input and output.
This guardrail can be added by adding `confidential_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

For confidential detection, the matching score has to be following format:
```yaml
"confidential_detection": {
    "No Confidential": 1,
    "Legal Documents": 1,
    "Business Strategies": 1,
    "Medical Information": 1,
    "Professional Records": 1
}
```


### Racial bias detection

The goal of the racial bias detection rail is to determine if the text has any kind of racially biased content. This rail can be applied at both input and output.
This guardrail can be added by adding `racial_bias_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

For racial bias detection, the matching score has to be following format:
```yaml
"racial_bias_detection": {
    "No Racial Bias": 0.5,
    "Racial Bias": 0.5,
    "Historical Racial Event": 0.5
}
```

### Tonal detection

The goal of the tonal detection rail is to determine if the text is written in negative tone.
This guardrail can be added by adding `tonal_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

For tonal detection, the matching score has to be following format:

```yaml
"tonal_detection": {
    "Negative Tones": 0.5,
    "Neutral Tones": 0.5,
    "Professional Tone": 0.5,
    "Thoughtful Tones": 0.5,
    "Positive Tones": 0.5,
    "Cautious Tones": 0.5
}
```

### Toxicity extraction

The goal of the toxicity detection rail is to determine if the text has any kind of toxic content. This rail can be applied at both input and output.This guardrail can be added by adding `text_toxicity_extraction` in `autoguard` section in `config.yml`.
This guardrail not just detects the toxicity of the text but also extracts toxic phrases from the text.

There are two different interfaces for input and output flows, one is `autoguard_toxicity_output_api` for output flow and another one is `autoguard_toxicity_input_api` for input flow.

```yaml
rails:
  config:
    autoguard:
      parameters:
        endpoint: "http://35.225.99.81:8888/guardrail"
      input:
        guardrails:
          - text_toxicity_extraction
        matching_scores:
          {"text_toxicity_extraction": {"score": 0.5}}
        flows:
          - call autoguard toxicity input
```

```colang
define subflow call autoguard toxicity input
    $result = execute autoguard_toxicity_input_api
    if $result[0] == True
        bot refuse to respond autoguard toxicity
        stop

define bot refuse to respond autoguard toxicity
    "$result[1] has been detected by AutoGuard; Sorry, can't process. Toxic phrases: $result[2]"
```

## Usage (AutoGuard PII)

To use AutoGuard's PII (Personal Identifiable Information) module, you have to list the entities that you wish to redact in following format:

```yaml
rails:
  config:
    autoguard:
      parameters:
        endpoint: "http://35.225.99.81:8888/guardrail"
      entities:
        - '[BANK ACCOUNT NUMBER]'
        - '[CREDIT CARD NUMBER]'
        - '[DATE OF BIRTH]'
        - '[DATE]'
        - '[DRIVER LICENSE NUMBER]'
        - '[EMAIL ADDRESS]'
        - '[RACE/ETHNICITY]'
        - '[GENDER]'
        - '[IP ADDRESS]'
        - '[LOCATION]'
        - '[MONEY]'
        - '[ORGANIZATION]'
        - '[PASSPORT NUMBER]'
        - '[PASSWORD]'
        - '[PERSON NAME]'
        - '[PHONE NUMBER]'
        - '[PROFESSION]'
        - '[SOCIAL SECURITY NUMBER]'
        - '[USERNAME]'
        - '[SECRET_KEY]'
        - '[TRANSACTION_ID]'
        - '[RELIGION]'
      contextual_rules:
        - ["[PERSON NAME]"]
        - ["[PERSON NAME]", "[CREDIT CARD NUMBER]", "[BANK ACCOUNT NUMBER]"]
        - ["[PERSON NAME]", "[EMAIL ADDRESS]", "[DATE OF BIRTH]"]
        - ["[PERSON NAME]", "[EMAIL ADDRESS]", "[LOCATION]", "[SOCIAL SECURITY NUMBER]"]
      matching_scores:
        {"pii_fast": {
          '[BANK ACCOUNT NUMBER]': 0.5,
            '[CREDIT CARD NUMBER]': 0.5,
            '[DATE OF BIRTH]': 0.5,
            '[DATE]': 0.5,
            '[DRIVER LICENSE NUMBER]': 0.5,
            '[EMAIL ADDRESS]': 0.5,
            '[RACE/ETHNICITY]': 0.5,
            '[GENDER]': 0.5,
            '[IP ADDRESS]': 0.5,
            '[LOCATION]': 0.5,
            '[MONEY]': 0.5,
            '[ORGANIZATION]': 0.5,
            '[PASSPORT NUMBER]': 0.5,
            '[PASSWORD]': 0.5,
            '[PERSON NAME]': 0.5,
            '[PHONE NUMBER]': 0.5,
            '[PROFESSION]': 0.5,
            '[SOCIAL SECURITY NUMBER]': 0.5,
            '[USERNAME]': 0.5,
            '[SECRET_KEY]': 0.5,
            '[TRANSACTION_ID]': 0.5,
            '[RELIGION]': 0.5
        }}
  output:
    flows:
      - call autoguard pii
```
Add the Autoguard's PII endpoint in the parameters section of autoguard config.

The above provided sample shows all PII entities that is currently being supported by AutoGuard.

One of the advanced configs is matching score which is a threshold that determines whether the guardrail will mask the entity in text or not.

Another config is contextual rules which determine when PII redaction will be active, PII redaction will take place only when one of the contextual rule will be satisfied.

The colang file has to be in the following format:

```colang
define subflow call autoguard pii
    $pii_result = execute autoguard_pii_output_api
    if $pii_result[0] == True
      bot autoguard pii response
      stop

define bot autoguard pii response
    "$pii_result[1]"
```

There are two different interfaces for input and output flows, one is `autoguard_pii_output_api` for output flow and another one is `autoguard_pii_input_api` for input flow.

## Usage (AutoGuard Factcheck)

To use AutoGuard's factcheck module, you have to modify the `config.yml` in the following format:

```yaml
rails:
  config:
    autoguard:
      parameters:
        fact_check_endpoint: "http://35.225.99.81:8888/factcheck"
      matching_scores:
        { "factcheck": {"score": 0.5}}
  output:
    flows:
      - check facts autoguard
```

Specify the factcheck endpoint the parameters section of autoguard's config.

One of the advanced configs is matching score which is a threshold that determines whether the guardrail will block the text or not.

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
