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
