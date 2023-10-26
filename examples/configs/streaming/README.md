# Streaming

This is an example configuration that uses streaming. To activate streaming support, you have to set the following key in your `config.yml`:

```yaml
streaming: True
```

**NOTE**: This configuration uses OpenAI GPT-4. If you don't have access to GPT-4, feel free to use `gpt-3.5-turbo-instruct` or `text-davinci-003` as well.

## Testing

To test this config, in streaming mode, using the chat CLI, run the following command from the root of the project:

```bash
nemoguardrails chat --config=examples/configs/streaming --streaming
```
