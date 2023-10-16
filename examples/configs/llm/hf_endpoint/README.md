# HuggingFace Endpoint

This configuration uses the HuggingFace [Inference Endpoints](https://huggingface.co/docs/inference-endpoints/index).

First, create an endpoint following the instructions [here](https://huggingface.co/docs/inference-endpoints/guides/create_endpoint). Then, update the `endpoint_url` key in the `config.yml` file.

**Disclaimer**: The `dolly-v2-3b` LLM model has only been tested on basic use cases, e.g., greetings and recognizing specific questions. On more complex queries, this model may not work correctly. Thorough testing and optimizations are needed before considering a production deployment.
