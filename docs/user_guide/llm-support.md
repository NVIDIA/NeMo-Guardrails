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

The following tables summarize the LLM support for the main features of NeMo Guardrails, focusing on the different rails available out of the box.


| Feature                                          | text-davinci-003   | gpt-3.5-turbo-instruct | nemollm-43b-chat   | llama-2-13b-chat   | falcon-7b-instruct | gpt-3.5-turbo | gpt-4 | vicuna-7b-v1.3 | mpt-7b-instruct | dolly-v2-3b |
|--------------------------------------------------|--------------------|------------------------|--------------------|--------------------|--------------------|---------------|-------|----------------|-----------------|-------------|
| Dialog Rails                                     | :heavy_check_mark: | :heavy_check_mark:     | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: ||||
| - Single LLM call                                | :heavy_check_mark: | :heavy_check_mark:     | :heavy_check_mark: | :x:                | :x:                | :x:           | :x:   | :x:            |
| - Multi-step flow generation                     | EXPERIMENTAL       | :x:                    | :x:                | :x:                | :x:                | :x:           | :x:   | :x:            | :x:             | :x:         |
| Streaming  	                                     | :heavy_check_mark: | :heavy_check_mark:     | :x:                ||||||
| Hallucination detection (SelfCheckGPT with LLM ) | :heavy_check_mark: | :x:                    | :x:                | :x:                | :x:                | :x:           | :x:   | :x:            | :x:             | :x:         |
| AskLLM                                           | :heavy_check_mark: ||||||||
| - Jailbreak detection                            | :heavy_check_mark: | :x:                    | :heavy_check_mark: | :x:                | :x:                | :x:           | :x:   | :x:            | :x:             | :x:         |
| - Output moderation                              | :heavy_check_mark: | :x:                    | :heavy_check_mark: | :x:                | :x:                | :x:           | :x:   | :x:            | :x:             | :x:         |
| - Fact-checking                                  | :heavy_check_mark: | :x:                    | :heavy_check_mark: | :heavy_check_mark: | :x:                | :x:           | :x:   | :x:            | :x:             | :x:         |
 | AlignScore fact-checking (LLM independent)       | :heavy_check_mark: ||||||||
| ActiveFence moderation (LLM independent)         | :heavy_check_mark: ||||||||

Table legend:
- :heavy_check_mark: - Supported
- :x: - Not Supported
