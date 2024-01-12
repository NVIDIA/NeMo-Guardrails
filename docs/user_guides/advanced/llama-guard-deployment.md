## Self-hosting Llama Guard using vLLM

Detailed below are steps to self-host Llama Guard using vLLM and HuggingFace. Alternatively, you can do this using your own custom inference code with the downloaded model weights, too.

1. Get access to the Llama Guard model from Meta on HuggingFace. See [this page](https://huggingface.co/meta-llama/LlamaGuard-7b) for more details.

2. Log in to Hugging Face with your account token
```
huggingface-cli login
```

3. Here, we use vLLM to host a Llama Guard inference endpoint in the OpenAI-compatible mode.
```
pip install vllm
python -m vllm.entrypoints.openai.api_server --host 0.0.0.0 --port 5123 --model meta-llama/LlamaGuard-7b
```

Once the server is successfully started, see [these example YAML configuration files](../../../examples/configs/llama_guard) for the bot configuration. The host and port need to match the values used above in step 3 to host the inference endpoint.
