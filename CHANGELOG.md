# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## Unreleased

### Added

- Support for [custom tasks and their prompts](./docs/user_guide/advanced/prompt-customization.md#custom-tasks-and-prompts).


## [0.5.0] - 2023-09-04

### Added

- Support for [custom configuration data](./docs/user_guide/configuration-guide.md#custom-data).
- Example for using [custom LLM and multiple KBs](./examples/multi_kb/README.md)
- Support for [`PROMPTS_DIR`](./docs/user_guide/advanced/prompt-customization.md#prompt-configuration).
- [#101](https://github.com/NVIDIA/NeMo-Guardrails/pull/101) Support for [using OpenAI embeddings](./docs/user_guide/configuration-guide.md#the-embeddings-model) models in addition to SentenceTransformers.
- First set of end-to-end QA tests for the example configurations.
- Support for configurable [embedding search providers](./docs/user_guide/advanced/embedding-search-providers.md)

### Changed

- Moved to using `nest_asyncio` for [implementing the blocking API](./docs/user_guide/advanced/nested-async-loop.md). Fixes [#3](https://github.com/NVIDIA/NeMo-Guardrails/issues/3) and [#32](https://github.com/NVIDIA/NeMo-Guardrails/issues/32).
- Improved event property validation in `new_event_dict`.
- Refactored imports to allow installing from source without Annoy/SentenceTransformers (would need a custom embedding search provider to work).

### Fixed

- Fixed when the `init` function from `config.py` is called to allow custom LLM providers to be registered inside.
- [#93](https://github.com/NVIDIA/NeMo-Guardrails/pull/93): Removed redundant `hasattr` check in `nemoguardrails/llm/params.py`.
- [#91](https://github.com/NVIDIA/NeMo-Guardrails/issues/91): Fixed how default context variables are initialized.

## [0.4.0] - 2023-08-03

### Added

- [Event-based API](./docs/user_guide/advanced/event-based-api.md) for guardrails.
- Support for message with type "event" in [`LLMRails.generate_async`](./docs/api/nemoguardrails.rails.llm.llmrails.md#method-llmrailsgenerate_async).
- Support for [bot message instructions](docs/user_guide/advanced/bot-message-instructions.md).
- Support for [using variables inside bot message definitions](./docs/user_guide/colang-language-syntax-guide.md#bot-messages-with-variables).
- Support for `vicuna-7b-v1.3` and `mpt-7b-instruct`.
- Topical evaluation results for `vicuna-7b-v1.3` and `mpt-7b-instruct`.
- Support to use different models for different LLM tasks.
- Support for [red-teaming](docs/user_guide/advanced/red-teaming.md) using challenges.
- Support to disable the Chat UI when running the server using `--disable-chat-ui`.
- Support for accessing the API request headers in server mode.
- Support to [enable CORS settings](docs/user_guide/server-guide.md#cors) for the guardrails server.

### Changed

- Changed the naming of the internal events to align to the upcoming UMIM spec (Unified Multimodal Interaction Management).
- If there are no user message examples, the bot messages examples lookup is disabled as well.

### Fixed

- [#58](https://github.com/NVIDIA/NeMo-Guardrails/issues/58): Fix install on Mac OS 13.
- [#55](https://github.com/NVIDIA/NeMo-Guardrails/issues/55): Fix bug in example causing config.py to crash on computers with no CUDA-enabled GPUs.
- Fixed the model name initialization for LLMs that use the `model` kwarg.
- Fixed the Cohere prompt templates.
- [#55](https://github.com/NVIDIA/NeMo-Guardrails/issues/83): Fix bug related to LangChain callbacks initialization.
- Fixed generation of "..." on value generation.
- Fixed the parameters type conversion when invoking actions from colang (previously everything was string).
- Fixed `model_kwargs` property for the `WrapperLLM`.
- Fixed bug when `stop` was used inside flows.
- Fixed Chat UI bug when an invalid guardrails configuration was used.

## [0.3.0] - 2023-06-30

### Added

- Support for defining [subflows](docs/user_guide/colang-language-syntax-guide.md#subflows).
- Improved support for [customizing LLM prompts](docs/user_guide/advanced/prompt-customization.md)
  - Support for using filters to change how variables are included in a prompt template.
  - Output parsers for prompt templates.
  - The `verbose_v1` formatter and output parser to be used for smaller models that don't understand Colang very well in a few-shot manner.
  - Support for including context variables in prompt templates.
  - Support for chat models i.e. prompting with a sequence of messages.
- Experimental support for allowing the LLM to generate [multi-step flows](docs/user_guide/configuration-guide.md#multi-step-generation).
- Example of using Llama Index from a guardrails configuration (#40).
- [Example](examples/llm/hf_endpoint) for using HuggingFace Endpoint LLMs with a guardrails configuration.
- [Example](examples/llm/hf_pipeline_dolly) for using HuggingFace Pipeline LLMs with a guardrails configuration.
- Support to alter LLM parameters passed as `model_kwargs` in LangChain.
- CLI tool for running evaluations on the different steps (e.g., canonical form generation, next steps, bot message) and on existing rails implementation (e.g., moderation, jailbreak, fact-checking, and hallucination).
- [Initial evaluation](nemoguardrails/eval/README.md) results for `text-davinci-003` and `gpt-3.5-turbo`.
- The `lowest_temperature` can be set through the guardrails config (to be used for deterministic tasks).

### Changed

- The core templates now use Jinja2 as the rendering engines.
- Improved the internal prompting architecture, now using an LLM Task Manager.

### Fixed

- Fixed bug related to invoking a chain with multiple output keys.
- Fixed bug related to tracking the output stats.
- #51: Bug fix - avoid str concat with None when logging user_intent.
- #54: Fix UTF-8 encoding issue and add embedding model configuration.

## [0.2.0] - 2023-05-31

### Added

- Support to [connect any LLM](./docs/user_guide/configuration-guide.md#supported-llm-models) that implements the BaseLanguageModel interface from  LangChain.
- Support for [customizing the prompts](./docs/user_guide/configuration-guide.md#llm-prompts) for specific LLM models.
- Support for [custom initialization](./docs/user_guide/configuration-guide.md#configuration-guide) when loading a configuration through `config.py`.
- Support to extract [user-provided values](./docs/user_guide/advanced/extract-user-provided-values.md) from utterances.

### Changed

- Improved the logging output for Chat CLI (clear events stream, prompts, completion, timing information).
- Updated system actions to use temperature 0 where it makes sense, e.g., canonical form generation, next step generation, fact checking, etc.
- Excluded the default system flows from the "next step generation" prompt.
- Updated langchain to 0.0.167.

### Fixed

- Fixed initialization of LangChain tools.
- Fixed the overriding of general instructions [#7](https://github.com/NVIDIA/NeMo-Guardrails/issues/7).
- Fixed action parameters inspection bug [#2](https://github.com/NVIDIA/NeMo-Guardrails/issues/2).
- Fixed bug related to multi-turn flows [#13](https://github.com/NVIDIA/NeMo-Guardrails/issues/13).
- Fixed Wolfram Alpha error reporting in the sample execution rail.

## [0.1.0] - 2023-04-25

### Added
- First alpha release.
