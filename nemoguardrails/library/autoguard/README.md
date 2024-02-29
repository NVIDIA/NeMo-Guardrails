# AutoGuard

This package implements the AutoGuard API integration.

AutoGuard comes with a library of built-in guardrails that you can easily use:

1. [Gender bias Detection](#gender-bias-detection)
2. [Harm Detection](#harm-detection)
3. [Jailbreak Detection](#jailbreak-detection)
4. [Confidential Detection](#confidential-detection)
5. [Intellectual property detection](#intellectual-property-detection)
5. [Racial bias Detection](#racial-bias-detection)
6. [Tonal Detection](#tonal-detection)
7. [Toxicity detection](#toxicity-extraction)
8. [PII](#pii)
9. [Factcheck](#factcheck)


Note: Factcheck and PII are implemented a bit differently, compared to other guardrails.
Please have a look at their description within this document to understand their usage.

## Usage (AutoGuard)

To use the autoguard's guardrails:

You have to first select the guardrails that you want to activate for input and output respectively.
After that add the guardrails' names to the set of configured guardrails for input and output sections
of the `autoguard` section in `config.yml` file:

```yaml
rails:
  config:
    autoguard:
      parameters:
        endpoint: "https://nvidia.autoalign.ai/guardrail"
      input:
        guardrails:
          - racial_bias_detection
          - gender_bias_detection
          - confidential_detection
          - tonal_detection
          - harm_detection
          - text_toxicity_extraction
          - jailbreak_detection
          - intellectual_property
        matching_scores:
          {"gender_bias_detection": {"score": 0.5}, "harm_detection": {"score": 0.5},
          "jailbreak_detection": {"score": 0.5},"intellectual_property": {"score": 0.5}, "confidential_detection": {"No Confidential": 0.5,
                                                                             "Legal Documents": 0.5,
                                                                             "Business Strategies": 0.5,
                                                                             "Medical Information": 0.5,
                                                                             "Professional Records": 0.5},
           "racial_bias_detection": { "No Racial Bias": 0.5,
                                      "Racial Bias": 0.5,
                                      "Historical Racial Event": 0.5}, "tonal_detection": {"Negative Tones": 0.8,
                                                                                           "Neutral Tones": 0.5,
                                                                                           "Professional Tone": 0.5,
                                                                                           "Thoughtful Tones": 0.5,
                                                                                           "Positive Tones": 0.5,
                                                                                           "Cautious Tones": 0.5}
           }
      output:
        guardrails:
          - racial_bias_detection
          - gender_bias_detection
          - confidential_detection
          - tonal_detection
          - harm_detection
          - text_toxicity_extraction
          - jailbreak_detection
          - intellectual_property
        matching_scores:
          { "gender_bias_detection": { "score": 0.5 }, "harm_detection": { "score": 0.5 },
            "jailbreak_detection": { "score": 0.5 }, "intellectual_property": {"score": 0.5}, "confidential_detection": { "No Confidential": 0.5,
                                                                                 "Legal Documents": 0.5,
                                                                                 "Business Strategies": 0.5,
                                                                                 "Medical Information": 0.5,
                                                                                 "Professional Records": 0.5 },
            "racial_bias_detection": { "No Racial Bias": 0.5,
                                       "Racial Bias": 0.5,
                                       "Historical Racial Event": 0.5 }, "tonal_detection": { "Negative Tones": 0.8,
                                                                                              "Neutral Tones": 0.5,
                                                                                              "Professional Tone": 0.5,
                                                                                              "Thoughtful Tones": 0.5,
                                                                                              "Positive Tones": 0.5,
                                                                                              "Cautious Tones": 0.5 }
          }
  input:
    flows:
      - call autoguard input
  output:
    flows:
      - call autoguard output
```
We also have to add the autoguard's endpoint in parameters.

One of the advanced configs is matching score which is a threshold that determines whether the guardrail will block the input/output or not.
Some guardrails have very different format of `matching_scores` config,
in each guardrail's description we have added an example to show how `matching_scores`
has been implemented for that guardrail.

The config for the guardrails has to be defined separately for both input and output side, as shown in the above example.


The colang file has to be in the following format:

```colang
define subflow call autoguard input
    $result = execute autoguard_input_api
    if $result[0] == True
        bot refuse to respond autoguard
        stop

define subflow call autoguard output
    $result = execute autoguard_output_api
    if $result[0] == True
        bot refuse to respond autoguard
        stop

define bot refuse to respond autoguard
  "$result[1]"
```


### Gender bias detection

The goal of the gender bias detection rail is to determine if the text has any kind of gender biased content. This rail can be applied at both input and output.
This guardrail can be added by adding `gender_bias_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

For gender bias detection, the matching score has to be following format:

```yaml
"gender_bias_detection": { "score": 0.5}
```

### Harm detection

The goal of the harm detection rail is to determine if the text has any kind of harm to human content. This rail can be applied at both input and output.
This guardrail can be added by adding `harm_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

For harm detection, the matching score has to be following format:

```yaml
"harm_detection": { "score": 0.5}
```

### Jailbreak detection

The goal of the jailbreak detection rail is to determine if the text has any kind of jailbreak attempt.
This guardrail can be added by adding `jailbreak_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

For jailbreak detection, the matching score has to be following format:

```yaml
"jailbreak_detection": { "score": 0.5}
```

### Intellectual property Detection

The goal of the intellectual property detection rail is to determine if the text has any mention of any intellectual property.
This guardrail can be added by adding `intellectual_propertyy` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

For intellectual property detection, the matching score has to be following format:

```yaml
"intellectual_property": { "score": 0.5}
```

### Confidential detection

The goal of the confidential detection rail is to determine if the text has any kind of confidential information. This rail can be applied at both input and output.
This guardrail can be added by adding `confidential_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

For confidential detection, the matching score has to be following format:
```yaml
"confidential_detection": {
    "No Confidential": 0.5,
    "Legal Documents": 0.5,
    "Business Strategies": 0.5,
    "Medical Information": 0.5,
    "Professional Records": 0.5
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

The goal of the toxicity detection rail is to determine if the text has any kind of toxic content. This rail can be applied at both input and output. This guardrail not just detects the toxicity of the text but also extracts toxic phrases from the text.
This guardrail can be added by adding `text_toxicity_extraction` in `input` or `output` section under list of configured `guardrails` which should be in `autoguard` section in `config.yml`.

For text toxicity detection, the matching score has to be following format:

```yaml
"text_toxicity_extraction": { "score": 0.5}
```

### PII

To use AutoGuard's PII (Personal Identifiable Information) module, you have to list the entities that you wish to redact in following format:

```yaml
rails:
  config:
    autoguard:
      parameters:
        endpoint: "https://nvidia.autoalign.ai/guardrail"
      output:
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

The above provided sample shows all PII entities that is currently being supported by AutoGuard.

One of the advanced configs is matching score which is a threshold that determines whether the guardrail will mask the entity in text or not.

Another config is contextual rules which determine when PII redaction will be active, PII redaction will take place only when one of the contextual rule will be satisfied.

You have to define the config for output and input side separately based on where the guardrail is applied upon.
In the above example the guardrail is configured on the output side so all the `config` is under the `output` section.

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

### Factcheck

To use AutoGuard's factcheck module, you have to modify the `config.yml` in the following format:

```yaml
rails:
  config:
    autoguard:
      parameters:
        fact_check_endpoint: "https://nvidia.autoalign.ai/factcheck"
  output:
    flows:
      - output autoguard factcheck
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
