# LLM Support

We aim to provide support in NeMo Guardrails for a wide range of LLMs from different providers,
with a focus on open models.
However, due to the complexity of the tasks required for employing dialog rails and most of the predefined
input and output rails (e.g. moderation or  fact-checking), not all LLMs are capable enough to be used.

## Evaluation experiments

This document aims to provide a summary of the evaluation experiments we have employed to assess
the performance of various LLMs for the different type of rails.

For more details about the evaluation of guardrails, including datasets and quantitative results,
please read [this document](../../nemoguardrails/eval/README.md).
The tools used for evaluation are described in the same file, for a summary of topics [read this section](../README.md#evaluation-tools) from the user guide.
Any new LLM available in Guardrails should be evaluated using at least this set of tools.

## LLM Support and Guidance

The following tables summarize the LLM support for each type of rail.

:heavy_check_mark: - Supported

:white_check_mark: - Partial Support


### Dialog rails

| LLM                    | Support            |
|------------------------|--------------------|
| text-davinci-003       | :heavy_check_mark: |
| gpt-3.5-turbo-instruct | :heavy_check_mark: |
| llama-2-13b-chat       | :heavy_check_mark: |
| falcon-7b-instruct  	  | :heavy_check_mark: |
| gpt-3.5-turbo          | :white_check_mark: |
| gpt-4                  | :white_check_mark: |
| dolly-v2-3b            | :white_check_mark: |
| vicuna-7b-v1.3         | :white_check_mark: |
| mpt-7b-instruct        | :white_check_mark: |

### Input and output rails

TO ADD
