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


Note: Factcheck is implemented a bit differently, compared to other guardrails.
Please have a look at its description within this document to understand its usage.

## Usage (AutoGuard)

To use the autoguard's guardrails:

You have to configure the guardrails in a dictionary under `guardrails_config` section, which you can provide for both `input`
section and `output` sections that come under `autoguard` section in `config.yml` file:

```yaml
rails:
    config:
        autoguard:
            parameters:
                endpoint: "https://nvidia.autoalign.ai/guardrail"
            input:
                guardrails_config:
                    {
                      "pii_fast": {
                          "enabled_types": [
                              "[BANK ACCOUNT NUMBER]",
                              "[CREDIT CARD NUMBER]",
                              "[DATE OF BIRTH]",
                              "[DATE]",
                              "[DRIVER LICENSE NUMBER]",
                              "[EMAIL ADDRESS]",
                              "[RACE/ETHNICITY]",
                              "[GENDER]",
                              "[IP ADDRESS]",
                              "[LOCATION]",
                              "[MONEY]",
                              "[ORGANIZATION]",
                              "[PASSPORT NUMBER]",
                              "[PASSWORD]",
                              "[PERSON NAME]",
                              "[PHONE NUMBER]",
                              "[PROFESSION]",
                              "[SOCIAL SECURITY NUMBER]",
                              "[USERNAME]",
                              "[SECRET_KEY]",
                              "[TRANSACTION_ID]",
                              "[RELIGION]",
                          ],
                          "contextual_rules":[
                                  [ "[PERSON NAME]", "[CREDIT CARD NUMBER]", "[BANK ACCOUNT NUMBER]" ],
                                  [ "[PERSON NAME]", "[EMAIL ADDRESS]", "[DATE OF BIRTH]" ]
                          ],
                          "matching_scores": {
                              "[BANK ACCOUNT NUMBER]": 0.5,
                              "[CREDIT CARD NUMBER]": 0.5,
                              "[DATE OF BIRTH]": 0.5,
                              "[DATE]": 0.5,
                              "[DRIVER LICENSE NUMBER]": 0.5,
                              "[EMAIL ADDRESS]": 0.5,
                              "[RACE/ETHNICITY]": 0.5,
                              "[GENDER]": 0.5,
                              "[IP ADDRESS]": 0.5,
                              "[LOCATION]": 0.5,
                              "[MONEY]": 0.5,
                              "[ORGANIZATION]": 0.5,
                              "[PASSPORT NUMBER]": 0.5,
                              "[PASSWORD]": 0.5,
                              "[PERSON NAME]": 0.5,
                              "[PHONE NUMBER]": 0.5,
                              "[PROFESSION]": 0.5,
                              "[SOCIAL SECURITY NUMBER]": 0.5,
                              "[USERNAME]": 0.5,
                              "[SECRET_KEY]": 0.5,
                              "[TRANSACTION_ID]": 0.5,
                              "[RELIGION]": 0.5
                          }
                        },
                        "confidential_detection": {
                              "matching_scores": {
                                  "No Confidential": 0.5,
                                  "Legal Documents": 0.5,
                                  "Business Strategies": 0.5,
                                  "Medical Information": 0.5,
                                  "Professional Records": 0.5
                              }
                        },
                        "gender_bias_detection": {
                              "matching_scores": {
                                  "score": 0.5
                              }
                        },
                        "harm_detection": {
                              "matching_scores": {
                                  "score": 0.5
                              }
                        },
                        "text_toxicity_extraction": {
                              "matching_scores": {
                                  "score": 0.5
                              }
                        },
                        "racial_bias_detection": {
                              "matching_scores": {
                                  "No Racial Bias": 0.5,
                                  "Racial Bias": 0.5,
                                  "Historical Racial Event": 0.5
                              }
                        },
                        "tonal_detection": {
                              "matching_scores": {
                                  "Negative Tones": 0.5,
                                  "Neutral Tones": 0.5,
                                  "Professional Tone": 0.5,
                                  "Thoughtful Tones": 0.5,
                                  "Positive Tones": 0.5,
                                  "Cautious Tones": 0.5
                              }
                        },
                        "jailbreak_detection": {
                              "matching_scores": {
                                  "score": 0.5
                              }
                        },
                        "intellectual_property": {
                              "matching_scores": {
                                  "score": 0.5
                              }
                        }
                    }
            output:
                guardrails_config:
                  {
                      "pii_fast": {
                          "enabled_types": [
                              "[BANK ACCOUNT NUMBER]",
                              "[CREDIT CARD NUMBER]",
                              "[DATE OF BIRTH]",
                              "[DATE]",
                              "[DRIVER LICENSE NUMBER]",
                              "[EMAIL ADDRESS]",
                              "[RACE/ETHNICITY]",
                              "[GENDER]",
                              "[IP ADDRESS]",
                              "[LOCATION]",
                              "[MONEY]",
                              "[ORGANIZATION]",
                              "[PASSPORT NUMBER]",
                              "[PASSWORD]",
                              "[PERSON NAME]",
                              "[PHONE NUMBER]",
                              "[PROFESSION]",
                              "[SOCIAL SECURITY NUMBER]",
                              "[USERNAME]",
                              "[SECRET_KEY]",
                              "[TRANSACTION_ID]",
                              "[RELIGION]",
                          ],
                          "contextual_rules": [
                              [ "[PERSON NAME]", "[CREDIT CARD NUMBER]", "[BANK ACCOUNT NUMBER]" ],
                              [ "[PERSON NAME]", "[EMAIL ADDRESS]", "[DATE OF BIRTH]" ]
                          ],
                          "matching_scores": {
                              "[BANK ACCOUNT NUMBER]": 0.5,
                              "[CREDIT CARD NUMBER]": 0.5,
                              "[DATE OF BIRTH]": 0.5,
                              "[DATE]": 0.5,
                              "[DRIVER LICENSE NUMBER]": 0.5,
                              "[EMAIL ADDRESS]": 0.5,
                              "[RACE/ETHNICITY]": 0.5,
                              "[GENDER]": 0.5,
                              "[IP ADDRESS]": 0.5,
                              "[LOCATION]": 0.5,
                              "[MONEY]": 0.5,
                              "[ORGANIZATION]": 0.5,
                              "[PASSPORT NUMBER]": 0.5,
                              "[PASSWORD]": 0.5,
                              "[PERSON NAME]": 0.5,
                              "[PHONE NUMBER]": 0.5,
                              "[PROFESSION]": 0.5,
                              "[SOCIAL SECURITY NUMBER]": 0.5,
                              "[USERNAME]": 0.5,
                              "[SECRET_KEY]": 0.5,
                              "[TRANSACTION_ID]": 0.5,
                              "[RELIGION]": 0.5
                          }
                      },
                      "confidential_detection": {
                          "matching_scores": {
                              "No Confidential": 0.5,
                              "Legal Documents": 0.5,
                              "Business Strategies": 0.5,
                              "Medical Information": 0.5,
                              "Professional Records": 0.5
                          }
                      },
                      "gender_bias_detection": {
                          "matching_scores": {
                              "score": 0.5
                          }
                      },
                      "harm_detection": {
                          "matching_scores": {
                              "score": 0.5
                          }
                      },
                      "text_toxicity_extraction": {
                          "matching_scores": {
                              "score": 0.5
                          }
                      },
                      "racial_bias_detection": {
                          "matching_scores": {
                              "No Racial Bias": 0.5,
                              "Racial Bias": 0.5,
                              "Historical Racial Event": 0.5
                          }
                      },
                      "tonal_detection": {
                          "matching_scores": {
                              "Negative Tones": 0.5,
                              "Neutral Tones": 0.5,
                              "Professional Tone": 0.5,
                              "Thoughtful Tones": 0.5,
                              "Positive Tones": 0.5,
                              "Cautious Tones": 0.5
                          }
                      },
                      "jailbreak_detection": {
                          "matching_scores": {
                              "score": 0.5
                          }
                      },
                      "intellectual_property": {
                          "matching_scores": {
                              "score": 0.5
                          }
                      }
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
PII has some more advanced config like `contextual_rules` and `enabled_types`, more details can be read in the PII section
given below.

The config for the guardrails has to be defined separately for both input and output side, as shown in the above example.


The colang file has to be in the following format:

```colang
define subflow call autoguard input
    $input_result = execute autoguard_input_api

define subflow call autoguard output
    $output_result = execute autoguard_output_api
    if $input_result[0] == True
        bot refuse to respond input autoguard
    if $output_result[0] == True
        bot refuse to respond output autoguard
    else
        bot respond autoguard

define bot refuse to respond input autoguard
  "$input_result[1]"

define bot refuse to respond output autoguard
  "$output_result[1]"

define bot respond autoguard
  "$bot_message"
```

The result obtained from `execute autoguard_input_api` or `execute autoguard_output_api` consists of 3 parts,
the first part is bool flag which will provide information whether any guardrail got triggered or not, the second part
is output string of the guardrail response which will provide information regarding which guardrails
got triggered and the third part consists of a list of toxic words that were extracted, if the `text_toxicity_extraction`
was configured, otherwise an empty string.

### Gender bias detection

The goal of the gender bias detection rail is to determine if the text has any kind of gender biased content. This rail can be applied at both input and output.
This guardrail can be configured by adding `gender_bias_detection` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoguard` section in `config.yml`.

For gender bias detection, the matching score has to be following format:

```yaml
"matching_scores": { "score": 0.5}
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
This guardrail can be added by adding `jailbreak_detection` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoguard` section in `config.yml`.

For jailbreak detection, the matching score has to be following format:

```yaml
"matching_scores": { "score": 0.5}
```

### Intellectual property Detection

The goal of the intellectual property detection rail is to determine if the text has any mention of any intellectual property.
This guardrail can be added by adding `intellectual_property` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoguard` section in `config.yml`.

For intellectual property detection, the matching score has to be following format:

```yaml
"matching_scores": { "score": 0.5}
```

### Confidential detection

The goal of the confidential detection rail is to determine if the text has any kind of confidential information. This rail can be applied at both input and output.
This guardrail can be added by adding `confidential_detection` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoguard` section in `config.yml`.

For confidential detection, the matching score has to be following format:

```yaml
"matching_scores": {
    "No Confidential": 0.5,
    "Legal Documents": 0.5,
    "Business Strategies": 0.5,
    "Medical Information": 0.5,
    "Professional Records": 0.5
}
```


### Racial bias detection

The goal of the racial bias detection rail is to determine if the text has any kind of racially biased content. This rail can be applied at both input and output.
This guardrail can be added by adding `racial_bias_detection` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoguard` section in `config.yml`.

For racial bias detection, the matching score has to be following format:

```yaml
"matching_scores": {
    "No Racial Bias": 0.5,
    "Racial Bias": 0.5,
    "Historical Racial Event": 0.5
}
```

### Tonal detection

The goal of the tonal detection rail is to determine if the text is written in negative tone.
This guardrail can be added by adding `tonal_detection` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoguard` section in `config.yml`.

For tonal detection, the matching score has to be following format:

```yaml
"matching_scores": {
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
This guardrail can be added by adding `text_toxicity_extraction` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoguard` section in `config.yml`.

For text toxicity detection, the matching score has to be following format:

```yaml
"matching_scores": { "score": 0.5}
```

Can extract toxic phrases by changing the colang file a bit:

```colang
define subflow call autoguard input
    $input_result = execute autoguard_input_api

define subflow call autoguard output
    $output_result = execute autoguard_output_api
    if $input_result[0] == True
        bot refuse to respond input autoguard
    if $output_result[0] == True
        bot refuse to respond output autoguard
    else
        bot respond autoguard

define bot refuse to respond input autoguard
  "$input_result[1] $input_result[2]"

define bot refuse to respond output autoguard
  "$output_result[1] $output_result[2]"

define bot respond autoguard
  "$bot_message"
```


### PII

To use AutoGuard's PII (Personal Identifiable Information) module, you have to list the entities that you wish to redact
in `enabled_types` in the dictionary of `guardrails_config` under the key of `pii_fast`.

The above provided sample shows all PII entities that is currently being supported by AutoGuard.

One of the advanced configs is matching score which is a threshold that determines whether the guardrail will mask the entity in text or not.

Another config is contextual rules which determine when PII redaction will be active, PII redaction will take place only when one of the contextual rule will be satisfied.

You have to define the config for output and input side separately based on where the guardrail is applied upon.

Example PII config:

```yaml
"pii_fast": {
  "enabled_types": [
      "[BANK ACCOUNT NUMBER]",
      "[CREDIT CARD NUMBER]",
      "[DATE OF BIRTH]",
      "[DATE]",
      "[DRIVER LICENSE NUMBER]",
      "[EMAIL ADDRESS]",
      "[RACE/ETHNICITY]",
      "[GENDER]",
      "[IP ADDRESS]",
      "[LOCATION]",
      "[MONEY]",
      "[ORGANIZATION]",
      "[PASSPORT NUMBER]",
      "[PASSWORD]",
      "[PERSON NAME]",
      "[PHONE NUMBER]",
      "[PROFESSION]",
      "[SOCIAL SECURITY NUMBER]",
      "[USERNAME]",
      "[SECRET_KEY]",
      "[TRANSACTION_ID]",
      "[RELIGION]",
  ],
  "contextual_rules": [
      [ "[PERSON NAME]", "[CREDIT CARD NUMBER]", "[BANK ACCOUNT NUMBER]" ],
      [ "[PERSON NAME]", "[EMAIL ADDRESS]", "[DATE OF BIRTH]" ]
  ],
  "matching_scores": {
      "[BANK ACCOUNT NUMBER]": 0.5,
      "[CREDIT CARD NUMBER]": 0.5,
      "[DATE OF BIRTH]": 0.5,
      "[DATE]": 0.5,
      "[DRIVER LICENSE NUMBER]": 0.5,
      "[EMAIL ADDRESS]": 0.5,
      "[RACE/ETHNICITY]": 0.5,
      "[GENDER]": 0.5,
      "[IP ADDRESS]": 0.5,
      "[LOCATION]": 0.5,
      "[MONEY]": 0.5,
      "[ORGANIZATION]": 0.5,
      "[PASSPORT NUMBER]": 0.5,
      "[PASSWORD]": 0.5,
      "[PERSON NAME]": 0.5,
      "[PHONE NUMBER]": 0.5,
      "[PROFESSION]": 0.5,
      "[SOCIAL SECURITY NUMBER]": 0.5,
      "[USERNAME]": 0.5,
      "[SECRET_KEY]": 0.5,
      "[TRANSACTION_ID]": 0.5,
      "[RELIGION]": 0.5
  }
}
```

### Factcheck

To use AutoGuard's factcheck module, you have to modify the `config.yml` in the following format:

```yaml
rails:
  config:
    autoguard:
      parameters:
        fact_check_endpoint: "https://nvidia.autoalign.ai/factcheck"
  input:
    flows:
      - input autoguard factcheck
  output:
    flows:
      - output autoguard factcheck
```

Specify the factcheck endpoint the parameters section of autoguard's config.
Then, you have to call the corresponding subflows for input and output factcheck guardrails.

Following is the format of the colang file:
```colang
define subflow input autoguard factcheck
    execute autoguard_retrieve_relevant_chunks
    $input_result = execute autoguard_factcheck_input_api
    if $input_result < 0.5
        bot inform autoguard factcheck input violation
        stop

define subflow output autoguard factcheck
    execute autoguard_retrieve_relevant_chunks
    $output_result = execute autoguard_factcheck_output_api
    if $output_result < 0.5
        bot inform autoguard factcheck output violation
        stop

define bot inform autoguard factcheck input violation
    "Factcheck input violation has been detected by AutoGuard."

define bot inform autoguard factcheck output violation
    "$bot_message Factcheck output violation has been detected by AutoGuard."
```

Within the subflow you have to execute a custom relevant chunk extraction action `autoguard_retrieve_relevant_chunks`,
so that the documents are passed in the context for the guardrail.

The output of the factcheck endpoint provides you with a factcheck score against which we can add a threshold which determines whether the given output is factually correct or not.

The supporting documents or the evidence has to be placed within a `kb` folder within `config` folder.