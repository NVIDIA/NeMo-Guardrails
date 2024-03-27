# AutoAlign

This package implements the AutoAlign's guardrails API integration - a comprehensive guardrail library by [AutoAlign](https://autoalign.ai/).

AutoAlign comes with a library of built-in guardrails that you can easily use:

1. [Gender bias Detection](#gender-bias-detection)
2. [Harm Detection](#harm-detection)
3. [Jailbreak Detection](#jailbreak-detection)
4. [Confidential Detection](#confidential-detection)
5. [Intellectual property detection](#intellectual-property-detection)
6. [Racial bias Detection](#racial-bias-detection)
7. [Tonal Detection](#tonal-detection)
8. [Toxicity detection](#toxicity-extraction)
9. [PII](#pii)
10. [Factcheck](#factcheck-or-groundness-check)


Note: Factcheck is implemented a bit differently, compared to other guardrails.
Please have a look at its description within this document to understand its usage.


## AutoAlign API KEY

In order to use AutoAlign's guardrails you need to set `AUTOALIGN_API_KEY` as an environment variable in your system,
with the API key as its value.

Please contact [hello@autoalign.ai](mailto:hello@autoalign.ai) for your own API key. Please mention NeMo and AutoAlign in the subject line in order to receive quick responses from the AutoAlign team.


## Usage

To use the AutoAlign's guardrails:

You have to configure the guardrails using the `guardrails_config` section, which you can provide for both `input`
section and `output` sections that come under `autoalign` section in `config.yml` file:

```yaml
rails:
    config:
        autoalign:
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
            - autoalign check input
    output:
        flows:
            - autoalign check output
```
We also have to add the AutoAlign's guardrail endpoint in parameters.

One of the advanced configs is matching score (ranging from 0 to 1) which is a threshold that determines whether the guardrail will block the input/output or not.
If the matching score is higher (i.e. close to 1) then the guardrail will be more strict.
Some guardrails have very different format of `matching_scores` config,
in each guardrail's description we have added an example to show how `matching_scores`
has been implemented for that guardrail.
PII has some more advanced config like `contextual_rules` and `enabled_types`, more details can be read in the PII section
given below.

**Please note that** all the additional configs such as `matching_scores`, `contextual_rules`, and `enabled_types` are optional; if they are not specified then the default values will be applied.

The config for the guardrails has to be defined separately for both input and output side, as shown in the above example.


The colang file has been implemented in the following format in the library:

```colang
define flow autoalign check input
  $input_result = execute autoalign_input_api(show_autoalign_message=True)

  if $input_result["guardrails_triggered"]
    $autoalign_input_response = $input_result['combined_response']
    bot refuse to respond
    stop

define flow autoalign check output
  $output_result = execute autoalign_output_api(show_autoalign_message=True)

  if $output_result["guardrails_triggered"]
    bot refuse to respond
    stop
  else
    $pii_message_output = $output_result["pii_fast"]["response"]
    if $output_result["pii_fast"]["guarded"]
      bot respond pii output
      stop

define bot respond pii output
  "$pii_message_output"


define bot refuse to respond
  "I'm sorry I can't respond."

```

The actions `autoalign_input_api` and `autoalign_output_api` takes in two arguments `show_autoalign_message` and
`show_toxic_phrases`. Both the arguments expect boolean value being passed to them. The default value of
`show_autoalign_message` is `True` and for `show_toxic_phrases` is False. The `show_autoalign_message` controls whether
we will any output from autoalign or not. The response from AutoAlign would be presented as a subtext, when
`show_autoalign_message` is kept `True`. Details regarding the second argument can be found in `text_toxicity_extraction`
section.


The result obtained from `execute autoalign_input_api` or `execute autoalign_output_api` is a dictionary,
where the keys are the guardrail names (there are some additional keys which we will describe later) and
values are again a dictionary with `guarded` and `response` keys. The value of `guarded` key is a bool which
tells us whether the guardrail got triggered or not and value of `response` contains the AutoAlign response.

Now coming to the additional keys, one of the key `guardrails_triggered` whose value is a bool which tells
us whether any guardrail apart from PII got triggered or not. Another key is `combined_response` whose value
provides a combined guardrail message for all the guardrails that got triggered.

Users can create their own flows and make use of AutoAlign's guardrails by using the actions
`execute autoalign_input_api` and `execute autoalign_output_api` in their flow.

### Gender bias detection

The goal of the gender bias detection rail is to determine if the text has any kind of gender biased content. This rail can be applied at both input and output.
This guardrail can be configured by adding `gender_bias_detection` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoalign` section in `config.yml`.

For gender bias detection, the matching score has to be following format:

```yaml
"matching_scores": { "score": 0.5}
```

### Harm detection

The goal of the harm detection rail is to determine if the text has any kind of harm to human content. This rail can be applied at both input and output.
This guardrail can be added by adding `harm_detection` in `input` or `output` section under list of configured `guardrails` which should be in `autoalign` section in `config.yml`.

For harm detection, the matching score has to be following format:

```yaml
"harm_detection": { "score": 0.5}
```

### Jailbreak detection

The goal of the jailbreak detection rail is to determine if the text has any kind of jailbreak attempt.
This guardrail can be added by adding `jailbreak_detection` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoalign` section in `config.yml`.

For jailbreak detection, the matching score has to be following format:

```yaml
"matching_scores": { "score": 0.5}
```

### Intellectual property Detection

The goal of the intellectual property detection rail is to determine if the text has any mention of any intellectual property.
This guardrail can be added by adding `intellectual_property` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoalign` section in `config.yml`.

For intellectual property detection, the matching score has to be following format:

```yaml
"matching_scores": { "score": 0.5}
```

### Confidential detection

The goal of the confidential detection rail is to determine if the text has any kind of confidential information. This rail can be applied at both input and output.
This guardrail can be added by adding `confidential_detection` key in the dictionary under `guardrails_config` section
which is under `input` or `output` section which should be in `autoalign` section in `config.yml`.

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
which is under `input` or `output` section which should be in `autoalign` section in `config.yml`.

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
which is under `input` or `output` section which should be in `autoalign` section in `config.yml`.

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
which is under `input` or `output` section which should be in `autoalign` section in `config.yml`.

For text toxicity detection, the matching score has to be following format:

```yaml
"matching_scores": { "score": 0.5}
```

Can extract toxic phrases by changing the colang file a bit:

```colang
define flow call autoalign input
  $input_result = execute autoalign_input_api(show_autoalign_message=True, show_toxic_phrases=True)

  if $input_result["guardrails_triggered"]
    $autoalign_input_response = $input_result['combined_response']
    bot refuse to respond
    stop

define flow call autoalign output
  $output_result = execute autoalign_output_api(show_autoalign_message=True, show_toxic_phrases=True)

  if $output_result["guardrails_triggered"]
    bot refuse to respond
    stop
  else
    $pii_message_output = $output_result["pii_fast"]["response"]
    if $output_result["pii_fast"]["guarded"]
      bot respond pii output
      stop


define bot respond pii output
  "$pii_message_output"


define bot refuse to respond
  "I'm sorry I can't respond."
```


### PII

To use AutoAlign's PII (Personal Identifiable Information) module, you have to list the entities that you wish to redact
in `enabled_types` in the dictionary of `guardrails_config` under the key of `pii_fast`; if not listed then all PII types will be redacted.

The above sample shows all PII entities that is currently being supported by AutoAlign.

One of the advanced configs is matching score which is a threshold that determines whether the guardrail will mask the entity in text or not.
This is optional, and not specified then the default matching score (0.5) will be applied.

Another config is contextual rules which determines when PII types must be present in text in order for the redaction to take place.
PII redaction will take place only when one of the contextual rule will be satisfied.

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

### Factcheck or Groundness Check
The factcheck needs an input statement (represented as ‘prompt’) as a list of evidence documents.
To use AutoAlign's factcheck module, you have to modify the `config.yml` in the following format:

```yaml
rails:
  config:
    autoalign:
      parameters:
        fact_check_endpoint: "https://nvidia.autoalign.ai/factcheck"
  output:
    flows:
      - autoalign factcheck output
```

Specify the factcheck endpoint the parameters section of autoalign's config.
Then, you have to call the corresponding subflows for factcheck guardrails.

Following is the format of the colang file, which is present in the library:
```colang
define flow autoalign factcheck input
  execute autoalign_retrieve_relevant_chunks_input
  $input_result = execute autoalign_factcheck_input_api

define flow autoalign factcheck output
  execute retrieve_relevant_chunks
  $output_result = execute autoalign_factcheck_output_api
  if $input_result < 0.5
    bot inform autoalign factcheck input violation
  if $output_result < 0.5
    bot inform autoalign factcheck output violation
    stop

define bot inform autoalign factcheck input violation
  "Factcheck input violation has been detected by AutoAlign."

define bot inform autoalign factcheck output violation
  "$bot_message Factcheck output violation has been detected by AutoAlign."
```

The output of the factcheck endpoint provides you with a factcheck score against which we can add a threshold which determines whether the given output is factually correct or not.

The supporting documents or the evidence has to be placed within a `kb` folder within `config` folder.
