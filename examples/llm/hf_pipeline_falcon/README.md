# HuggingFace Pipeline with Falcon models

This configuration uses the HuggingFace Pipeline LLM with the [Falcon-7b-instruct](https://huggingface.co/tiiuae/falcon-7b-instruct) model but also has support for other variants (Falcon-40B-instruct, Falcon-40B and Falcon-7B)

The `Falcon-40b-instruct` LLM model has been tested on the topical rails evaluation sets, results are available [here](../../../nemoguardrails/eval/README.md).

In this folder, the guardrails application is very basic, but anyone can change it with any other more complex configuration.

**Disclaimer**: The current results of using `Falcon-40b-instruct` LLM are promising, but still incipient.
On more complex guardrails apps, this model may not work correctly. Thorough testing and optimizations, including for the prompts, are needed before considering a production deployment.
