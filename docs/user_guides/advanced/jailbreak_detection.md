# Jailbreak Detection Deployment

**NOTE**: The recommended way to use Jailbreak Detection with NeMo Guardrails is using the provided [Dockerfile](../../../nemoguardrails/library/jailbreak_detection/Dockerfile). For more details, check out how to [build and use the image](./using-docker.md).

In order to deploy jailbreak detection server, follow these steps:

1. Install the dependencies
```bash
pip install transformers torch uvicorn nemoguardrails
```

2. Start the jailbreak detection server
```bash
python -m nemoguardrails.library.jailbreak_detection.server --port 1337
```

By default, the jailbreak detection server listens on port `1337`. You can change the port using the `--port` option.

## Heuristic Configurations

### `checks.check_jb_lp`
The default threshold value for the `check_jb_lp` heuristic is `89.79`. 
This value represents the mean length/perplexity for a set of jailbreaks derived from a combination of datasets including [AdvBench](https://github.com/llm-attacks/llm-attacks), [ToxicChat](https://huggingface.co/datasets/lmsys/toxic-chat/blob/main/README.md), and [JailbreakChat](https://github.com/verazuo/jailbreak_llms), with non-jailbreaks taken from the same datasets and incorporating 1000 examples from [Dolly-15k](https://huggingface.co/datasets/databricks/databricks-dolly-15k).

The statistics for this metric across jailbreak and non jailbreak datasets are as follows:

|      | Jailbreaks | Non-Jailbreaks |
|------|------------|----------------|
| mean | 89.79      | 27.11          |
| min  | 0.03       | 0.00           |
| 25%  | 12.90      | 0.46           |
| 50%  | 47.32      | 2.40           |
| 75%  | 116.94     | 18.78          |
| max  | 1380.55    | 3418.62        |

Using the mean value of `89.79` yields 31.19% of jailbreaks being detected with a false positive rate of 7.44% on the dataset.
Increasing this threshold will decrease the number of jailbreaks detected but will yield fewer false positives.

**USAGE NOTES**: 
* Manual inspection of false positives uncovered a number of mislabeled examples in the dataset and a substantial number of system-like prompts.
If your application is intended for simple question answering or retrieval-aided generation, this should be a generally safe heuristic.
* This heuristic in its current form is intended only for English language evaluation and will yield significantly more false positives on non-English text, including code.

### `checks.check_jb_ps_ppl`
The `check_jb_ps_ppl` heuristic examines strings of more than 20 "words" (strings separated by whitespace) to detect potential prefix/suffix attacks.
The default threshold value for the `check_jb_ps_ppl` is `1845.65`.
This value is the second-lowest perplexity value across 50 different prompts generated using [GCG](https://github.com/llm-attacks/llm-attacks) prefix/suffix attacks.
Using the default value allows for detection of 49/50 GCG-style attacks with a 0.04% false positive rate on the "non-jailbreak" dataset derived above.

**USAGE NOTES**:
* This heuristic in its current form is intended only for English language evaluation and will yield significantly more false positives on non-English text, including code.
