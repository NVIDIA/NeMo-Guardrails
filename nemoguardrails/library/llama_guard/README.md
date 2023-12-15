To use Meta's Llama Guard, host the model on-prem and expose it as an API.

Detailed below are steps to do this using vLLM and Hugging Face. Alternatively, you can do this using your own custom inference code with the downloaded model weights too.

1. Get access to the Llama Guard model from Meta on Hugging Face. See [this page](https://huggingface.co/meta-llama/LlamaGuard-7b) for more details.

2. Log in to Hugging Face with your account token
```
huggingface-cli login
```

3. Here, we use `vLLM` to host a Llama Guard inference endpoint.
```
pip install vllm
python -m vllm.entrypoints.api_server --host 0.0.0.0 --port 5123 --model meta-llama/LlamaGuard-7b
```

Note that NeMo Guardrails usually invokes the `register_llm_provider` function to use custom LLMs, including Llama 2.

However, Llama Guard, even though an LLM under the hood, has been finetuned to perform safe/unsafe classifications given structured prompts only. As such, it is not a general-purpose LLM and often doesn't produce reasonable outputs to general prompts.

Hence, we use the format for registering custom actions instead.
