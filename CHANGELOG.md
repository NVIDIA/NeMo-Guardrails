# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

NOTE:
The changes related to the Colang language and runtime have moved to [CHANGELOG-Colang](./CHANGELOG-Colang.md) file.

## [0.9.1.1] - 2024-07-26

### Fixed

* [#650](https://github.com/NVIDIA/NeMo-Guardrails/pull/650) Fix gpt-3.5-turbo-instruct prompts #651.


## [0.9.1] - 2024-07-25

### Added

* Colang version [2.0-beta.2](./CHANGELOG-Colang.md#20-beta2---unreleased)
* [#370](https://github.com/NVIDIA/NeMo-Guardrails/pull/370) Add Got It AI's Truthchecking service for RAG applications by @mlmonk.
* [#543](https://github.com/NVIDIA/NeMo-Guardrails/pull/543) Integrating AutoAlign's guardrail library with NeMo Guardrails by @abhijitpal1247.
* [#566](https://github.com/NVIDIA/NeMo-Guardrails/pull/566) Autoalign factcheck examples by @abhijitpal1247.
* [#518](https://github.com/NVIDIA/NeMo-Guardrails/pull/518) Docs: add example config for using models with ollama by @vedantnaik19.
* [#538](https://github.com/NVIDIA/NeMo-Guardrails/pull/538) Support for `--default-config-id` in the server.
* [#539](https://github.com/NVIDIA/NeMo-Guardrails/pull/539) Support for `LLMCallException`.
* [#548](https://github.com/NVIDIA/NeMo-Guardrails/pull/548) Support for custom embedding models.
* [#617](https://github.com/NVIDIA/NeMo-Guardrails/pull/617) NVIDIA AI Endpoints embeddings.
* [#462](https://github.com/NVIDIA/NeMo-Guardrails/pull/462) Support for calling embedding models from langchain-nvidia-ai-endpoints.
* [#622](https://github.com/NVIDIA/NeMo-Guardrails/pull/622) Patronus Lynx Integration.

### Changed

* [#597](https://github.com/NVIDIA/NeMo-Guardrails/pull/597) Make UUID generation predictable in debug-mode.
* [#603](https://github.com/NVIDIA/NeMo-Guardrails/pull/603) Improve chat cli logging.
* [#551](https://github.com/NVIDIA/NeMo-Guardrails/pull/551) Upgrade to Langchain 0.2.x by @nicoloboschi.
* [#611](https://github.com/NVIDIA/NeMo-Guardrails/pull/611) Change default templates.
* [#545](https://github.com/NVIDIA/NeMo-Guardrails/pull/545) NVIDIA API Catalog and NIM documentation update.
* [#463](https://github.com/NVIDIA/NeMo-Guardrails/pull/463) Do not store pip cache during docker build by @don-attilio.
* [#629](https://github.com/NVIDIA/NeMo-Guardrails/pull/629) Move community docs to separate folder.
* [#647](https://github.com/NVIDIA/NeMo-Guardrails/pull/647) Documentation updates.
* [#648](https://github.com/NVIDIA/NeMo-Guardrails/pull/648) Prompt improvements for Llama-3 models.

### Fixed

* [#482](https://github.com/NVIDIA/NeMo-Guardrails/pull/482) Update README.md by @curefatih.
* [#530](https://github.com/NVIDIA/NeMo-Guardrails/pull/530) Improve the test serialization test to make it more robust.
* [#570](https://github.com/NVIDIA/NeMo-Guardrails/pull/570) Add support for FacialGestureBotAction by @elisam0.
* [#550](https://github.com/NVIDIA/NeMo-Guardrails/pull/550) Fix issue #335 - make import errors visible.
* [#547](https://github.com/NVIDIA/NeMo-Guardrails/pull/547) Fix LLMParams bug and add unit tests (fixes #158).
* [#537](https://github.com/NVIDIA/NeMo-Guardrails/pull/537) Fix directory traversal bug.
* [#536](https://github.com/NVIDIA/NeMo-Guardrails/pull/536) Fix issue #304 NeMo Guardrails packaging.
* [#539](https://github.com/NVIDIA/NeMo-Guardrails/pull/539) Fix bug related to the flow abort logic in Colang 1.0 runtime.
* [#612](https://github.com/NVIDIA/NeMo-Guardrails/pull/612) Follow-up fixes for the default prompt change.
* [#585](https://github.com/NVIDIA/NeMo-Guardrails/pull/585) Fix Colang 2.0 state serialization issue.
* [#486](https://github.com/NVIDIA/NeMo-Guardrails/pull/486) Fix select model type and custom prompts task.py by @cyun9601.
* [#487](https://github.com/NVIDIA/NeMo-Guardrails/pull/487) Fix custom prompts configuration manual.md.
* [#479](https://github.com/NVIDIA/NeMo-Guardrails/pull/479) Fix static method and classmethod action decorators by @piotrm0.
* [#544](https://github.com/NVIDIA/NeMo-Guardrails/pull/544) Fix issue #216 bot utterance.
* [#616](https://github.com/NVIDIA/NeMo-Guardrails/pull/616) Various fixes.
* [#623](https://github.com/NVIDIA/NeMo-Guardrails/pull/623) Fix path traversal check.


## [0.9.0] - 2024-05-08

### Added

* [Colang 2.0 Documentation](https://docs.nvidia.com/nemo/guardrails/colang_2/overview.html).
* Revamped [NeMo Guardrails Documentation](https://docs.nvidia.com/nemo-guardrails).

### Fixed

* [#461](https://github.com/NVIDIA/NeMo-Guardrails/pull/461) Feature/ccl cleanup.
* [#483](https://github.com/NVIDIA/NeMo-Guardrails/pull/483) Fix dictionary expression evaluation bug.
* [#467](https://github.com/NVIDIA/NeMo-Guardrails/pull/467) Feature/colang doc related cleanups.
* [#484](https://github.com/NVIDIA/NeMo-Guardrails/pull/484) Enable parsing of `..."<NLD>"` expressions.
* [#478](https://github.com/NVIDIA/NeMo-Guardrails/pull/478) Fix #420 - evaluate not working with chat models.


## [0.8.3] - 2024-04-18

### Changed

* [#453](https://github.com/NVIDIA/NeMo-Guardrails/pull/453) Update documentation for NVIDIA API Catalog example.

### Fixed

* [#382](https://github.com/NVIDIA/NeMo-Guardrails/pull/382) Fix issue with `lowest_temperature` in self-check and hallucination rails.
* [#454](https://github.com/NVIDIA/NeMo-Guardrails/pull/454) Redo fix for #385.
* [#442](https://github.com/NVIDIA/NeMo-Guardrails/pull/442) Fix README type by @dileepbapat.


## [0.8.2] - 2024-04-01

### Added

* [#402](https://github.com/NVIDIA/NeMo-Guardrails/pull/402) Integrate Vertex AI Models into Guardrails by @aishwaryap.
* [#403](https://github.com/NVIDIA/NeMo-Guardrails/pull/403) Add support for NVIDIA AI Endpoints by @patriciapampanelli
* [#396](https://github.com/NVIDIA/NeMo-Guardrails/pull/396) Docs/examples nv ai foundation models.
* [#438](https://github.com/NVIDIA/NeMo-Guardrails/pull/438) Add research roadmap documentation.

### Changed

* [#389](https://github.com/NVIDIA/NeMo-Guardrails/pull/389) Expose the `verbose` parameter through `RunnableRails` by @d-mariano.
* [#415](https://github.com/NVIDIA/NeMo-Guardrails/pull/415) Enable `print(...)` and `log(...)`.
* [#389](https://github.com/NVIDIA/NeMo-Guardrails/pull/389) Expose verbose arg in RunnableRails by @d-mariano.
* [#414](https://github.com/NVIDIA/NeMo-Guardrails/pull/414) Feature/colang march release.
* [#416](https://github.com/NVIDIA/NeMo-Guardrails/pull/416) Refactor and improve the verbose/debug mode.
* [#418](https://github.com/NVIDIA/NeMo-Guardrails/pull/418) Feature/colang flow context sharing.
* [#425](https://github.com/NVIDIA/NeMo-Guardrails/pull/425) Feature/colang meta decorator.
* [#427](https://github.com/NVIDIA/NeMo-Guardrails/pull/427) Feature/colang single flow activation.
* [#426](https://github.com/NVIDIA/NeMo-Guardrails/pull/426) Feature/colang 2.0 tutorial.
* [#428](https://github.com/NVIDIA/NeMo-Guardrails/pull/428) Feature/Standard library and examples.
* [#431](https://github.com/NVIDIA/NeMo-Guardrails/pull/431) Feature/colang various improvements.
* [#433](https://github.com/NVIDIA/NeMo-Guardrails/pull/433) Feature/Colang 2.0 improvements: generate_async support, stateful API.

### Fixed

* [#412](https://github.com/NVIDIA/NeMo-Guardrails/pull/412) Fix #411 - explain rails not working for chat models.
* [#413](https://github.com/NVIDIA/NeMo-Guardrails/pull/413) Typo fix: Comment in llm_flows.co by @habanoz.
* [#420](https://github.com/NVIDIA/NeMo-Guardrails/pull/430) Fix typo for hallucination message.

## [0.8.1] - 2024-03-15

### Added

- [#377](https://github.com/NVIDIA/NeMo-Guardrails/pull/377) Add example for streaming from custom action.

### Changed

- [#380](https://github.com/NVIDIA/NeMo-Guardrails/pull/380) Update installation guide for OpenAI usage.
- [#401](https://github.com/NVIDIA/NeMo-Guardrails/pull/401) Replace YAML import with new import statement in multi-modal example.

### Fixed

- [#398](https://github.com/NVIDIA/NeMo-Guardrails/pull/398) Colang parser fixes and improvements.
- [#394](https://github.com/NVIDIA/NeMo-Guardrails/pull/394) Fixes and improvements for Colang 2.0 runtime.
- [#381](https://github.com/NVIDIA/NeMo-Guardrails/pull/381) Fix typo by @serhatgktp.
- [#379](https://github.com/NVIDIA/NeMo-Guardrails/pull/379) Fix missing prompt in verbose mode for chat models.
- [#400](https://github.com/NVIDIA/NeMo-Guardrails/pull/400) Fix Authorization header showing up in logs for NeMo LLM.

## [0.8.0] - 2024-02-28

### Added

- [#292](https://github.com/NVIDIA/NeMo-Guardrails/pull/292) [Jailbreak heuristics](./docs/user_guides/guardrails-library.md#jailbreak-detection-heuristics) by @erickgalinkin.
- [#256](https://github.com/NVIDIA/NeMo-Guardrails/pull/256) Support [generation options](./docs/user_guides/advanced/generation-options.md).
- [#307](https://github.com/NVIDIA/NeMo-Guardrails/pull/307) Added support for multi-config api calls by @makeshn.
- [#293](https://github.com/NVIDIA/NeMo-Guardrails/pull/293) Adds configurable stop tokens by @zmackie.
- [#334](https://github.com/NVIDIA/NeMo-Guardrails/pull/334) Colang 2.0 - Preview by @schuellc.
- [#208](https://github.com/NVIDIA/NeMo-Guardrails/pull/208) Implement cache embeddings (resolves #200) by @Pouyanpi.
- [#331](https://github.com/NVIDIA/NeMo-Guardrails/pull/331) Huggingface pipeline streaming by @trebedea.

Documentation:
- [#311](https://github.com/NVIDIA/NeMo-Guardrails/pull/311) Update documentation to demonstrate the use of output rails when using a custom RAG by @niels-garve.
- [#347](https://github.com/NVIDIA/NeMo-Guardrails/pull/347) Add [detailed logging docs](./docs/user_guides/detailed_logging) by @erickgalinkin.
- [#354](https://github.com/NVIDIA/NeMo-Guardrails/pull/354) [Input and output rails only guide](./docs/user_guides/input_output_rails_only) by @trebedea.
- [#359](https://github.com/NVIDIA/NeMo-Guardrails/pull/359) Added [user guide for jailbreak detection heuristics](./docs/user_guides/jailbreak_detection_heuristics) by @makeshn.
- [#363](https://github.com/NVIDIA/NeMo-Guardrails/pull/363) Add [multi-config API call user guide](./docs/user_guides/multi_config_api).
- [#297](https://github.com/NVIDIA/NeMo-Guardrails/pull/297) Example configurations for using only the guardrails, without LLM generation.

### Changed

- [#309](https://github.com/NVIDIA/NeMo-Guardrails/pull/309) Change the paper citation from ArXiV to EMNLP 2023 by @manuelciosici
- [#319](https://github.com/NVIDIA/NeMo-Guardrails/pull/319) Enable embeddings model caching.
- [#267](https://github.com/NVIDIA/NeMo-Guardrails/pull/267) Make embeddings computing async and add support for batching.
- [#281](https://github.com/NVIDIA/NeMo-Guardrails/pull/281) Follow symlinks when building knowledge base by @piotrm0.
- [#280](https://github.com/NVIDIA/NeMo-Guardrails/pull/280) Add more information to results of `retrieve_relevant_chunks` by @piotrm0.
- [#332](https://github.com/NVIDIA/NeMo-Guardrails/pull/332) Update docs for batch embedding computations.
- [#244](https://github.com/NVIDIA/NeMo-Guardrails/pull/244) Docs/edit getting started by @DougAtNvidia.
- [#333](https://github.com/NVIDIA/NeMo-Guardrails/pull/333) Follow-up to PR 244.
- [#341](https://github.com/NVIDIA/NeMo-Guardrails/pull/341) Updated 'fastembed' version to 0.2.2 by @NirantK.

### Fixed

- [#286](https://github.com/NVIDIA/NeMo-Guardrails/pull/286) Fixed #285 - using the same evaluation set given a random seed for topical rails by @trebedea.
- [#336](https://github.com/NVIDIA/NeMo-Guardrails/pull/336) Fix #320. Reuse the asyncio loop between sync calls.
- [#337](https://github.com/NVIDIA/NeMo-Guardrails/pull/337) Fix stats gathering in a parallel async setup.
- [#342](https://github.com/NVIDIA/NeMo-Guardrails/pull/342) Fixes OpenAI embeddings support.
- [#346](https://github.com/NVIDIA/NeMo-Guardrails/pull/346) Fix issues with KB embeddings cache, bot intent detection and config ids validator logic.
- [#349](https://github.com/NVIDIA/NeMo-Guardrails/pull/349) Fix multi-config bug, asyncio loop issue and cache folder for embeddings.
- [#350](https://github.com/NVIDIA/NeMo-Guardrails/pull/350) Fix the incorrect logging of an extra dialog rail.
- [#358](https://github.com/NVIDIA/NeMo-Guardrails/pull/358) Fix Openai embeddings async support.
- [#362](https://github.com/NVIDIA/NeMo-Guardrails/pull/362) Fix the issue with the server being pointed to a folder with a single config.
- [#352](https://github.com/NVIDIA/NeMo-Guardrails/pull/352) Fix a few issues related to jailbreak detection heuristics.
- [#356](https://github.com/NVIDIA/NeMo-Guardrails/pull/356) Redo followlinks PR in new code by @piotrm0.

## [0.7.1] - 2024-02-01

### Changed

- [#288](https://github.com/NVIDIA/NeMo-Guardrails/pull/288) Replace SentenceTransformers with FastEmbed.


## [0.7.0] - 2024-01-31

### Added

- [#254](https://github.com/NVIDIA/NeMo-Guardrails/pull/254) Support for [Llama Guard input and output content moderation](./docs/user_guides/guardrails-library.md#llama-guard-based-content-moderation).
- [#253](https://github.com/NVIDIA/NeMo-Guardrails/pull/253) Support for [server-side threads](./docs/user_guides/server-guide.md#threads).
- [#235](https://github.com/NVIDIA/NeMo-Guardrails/pull/235) Improved [LangChain integration](docs/user_guides/langchain/langchain-integration.md) through `RunnableRails`.
- [#190](https://github.com/NVIDIA/NeMo-Guardrails/pull/190) Add [example](./examples/notebooks/generate_events_and_streaming.ipynb) for using `generate_events_async` with streaming.
- Support for Python 3.11.

### Changed

- [#240](https://github.com/NVIDIA/NeMo-Guardrails/pull/240) Switch to pyproject.
- [#276](https://github.com/NVIDIA/NeMo-Guardrails/pull/276) Upgraded Typer to 0.9.

### Fixed

- [#286](https://github.com/NVIDIA/NeMo-Guardrails/pull/286) Fixed not having the same evaluation set given a random seed for topical rails.
- [#239](https://github.com/NVIDIA/NeMo-Guardrails/pull/239) Fixed logging issue where `verbose=true` flag did not trigger expected log output.
- [#228](https://github.com/NVIDIA/NeMo-Guardrails/pull/228) Fix docstrings for various functions.
- [#242](https://github.com/NVIDIA/NeMo-Guardrails/pull/242) Fix Azure LLM support.
- [#225](https://github.com/NVIDIA/NeMo-Guardrails/pull/225) Fix annoy import, to allow using without.
- [#209](https://github.com/NVIDIA/NeMo-Guardrails/pull/209) Fix user messages missing from prompt.
- [#261](https://github.com/NVIDIA/NeMo-Guardrails/pull/261) Fix small bug in `print_llm_calls_summary`.
- [#252](https://github.com/NVIDIA/NeMo-Guardrails/pull/252) Fixed duplicate loading for the default config.
- Fixed the dependencies pinning, allowing a wider range of dependencies versions.
- Fixed sever security issues related to uncontrolled data used in path expression and information exposure through an exception.


## [0.6.1] - 2023-12-20

### Added

- Support for `--version` flag in the CLI.

### Changed

- Upgraded `langchain` to `0.0.352`.
- Upgraded `httpx` to `0.24.1`.
- Replaced deprecated `text-davinci-003` model with `gpt-3.5-turbo-instruct`.

### Fixed

- [#191](https://github.com/NVIDIA/NeMo-Guardrails/pull/191): Fix chat generation chunk issue.

## [0.6.0] - 2023-12-13

### Added

- Support for [explicit definition](./docs/user_guides/configuration-guide.md#guardrails-definitions) of input/output/retrieval rails.
- Support for [custom tasks and their prompts](docs/user_guides/advanced/prompt-customization.md#custom-tasks-and-prompts).
- Support for fact-checking [using AlignScore](./docs/user_guides/guardrails-library.md#alignscore-based-fact-checking).
- Support for [NeMo LLM Service](./docs/user_guides/configuration-guide.md#nemo-llm-service) as an LLM provider.
- Support for making a single LLM call for both the guardrails process and generating the response (by setting `rails.dialog.single_call.enabled` to `True`).
- Support for [sensitive data detection](./docs/user_guides/guardrails-library.md#presidio-based-sensitive-data-detection) guardrails using Presidio.
- [Example](./examples/configs/llm/hf_pipeline_llama2) using NeMo Guardrails with the LLaMa2-13B model.
- [Dockerfile](./Dockerfile) for building a Docker image.
- Support for [prompting modes](./docs/user_guides/advanced/prompt-customization.md) using `prompting_mode`.
- Support for [TRT-LLM](./docs/user_guides/configuration-guide.md#trt-llm) as an LLM provider.
- Support for [streaming](./docs/user_guides/advanced/streaming.md) the LLM responses when no output rails are used.
- [Integration](./docs/user_guides/guardrails-library.md#active-fence) of ActiveFence ActiveScore API as an input rail.
- Support for `--prefix` and `--auto-reload` in the [guardrails server](./docs/user_guides/server-guide.md).
- Example [authentication dialog flow](./examples/configs/auth).
- Example [RAG using Pinecone](./examples/configs/rag/pinecone).
- Support for loading a configuration from dictionary, i.e. `RailsConfig.from_content(config=...)`.
- Guidance on [LLM support](./docs/user_guides/llm-support.md).
- Support for `LLMRails.explain()` (see the [Getting Started](./docs/getting_started) guide for sample usage).

### Changed

- Allow context data directly in the `/v1/chat/completion` using messages with the type `"role"`.
- Allow calling a subflow whose name is in a variable, e.g. `do $some_name`.
- Allow using actions which are not `async` functions.
- Disabled pretty exceptions in CLI.
- Upgraded dependencies.
- Updated the [Getting Started Guide](./docs/getting_started).
- Main [README](./README.md) now provides more details.
- Merged original examples into a single [ABC Bot](./examples/bots/abc) and removed the original ones.
- Documentation improvements.

### Fixed

- Fix going over the maximum prompt length using the `max_length` attribute in [Prompt Templates](./docs/user_guides/advanced/prompt-customization.md#prompt-templates).
- Fixed problem with `nest_asyncio` initialization.
- [#144](https://github.com/NVIDIA/NeMo-Guardrails/pull/144) Fixed TypeError in logging call.
- [#121](https://github.com/NVIDIA/NeMo-Guardrails/pull/109) Detect chat model using openai engine.
- [#109](https://github.com/NVIDIA/NeMo-Guardrails/pull/109) Fixed minor logging issue.
- Parallel flow support.
- Fix `HuggingFacePipeline` bug related to LangChain version upgrade.


## [0.5.0] - 2023-09-04

### Added

- Support for [custom configuration data](docs/user_guides/configuration-guide.md#custom-data).
- Example for using [custom LLM and multiple KBs](examples/configs/rag/multi_kb/README.md)
- Support for [`PROMPTS_DIR`](docs/user_guides/advanced/prompt-customization.md#prompt-configuration).
- [#101](https://github.com/NVIDIA/NeMo-Guardrails/pull/101) Support for [using OpenAI embeddings](docs/user_guides/configuration-guide.md#the-embeddings-model) models in addition to SentenceTransformers.
- First set of end-to-end QA tests for the example configurations.
- Support for configurable [embedding search providers](docs/user_guides/advanced/embedding-search-providers.md)

### Changed

- Moved to using `nest_asyncio` for [implementing the blocking API](docs/user_guides/advanced/nested-async-loop.md). Fixes [#3](https://github.com/NVIDIA/NeMo-Guardrails/issues/3) and [#32](https://github.com/NVIDIA/NeMo-Guardrails/issues/32).
- Improved event property validation in `new_event_dict`.
- Refactored imports to allow installing from source without Annoy/SentenceTransformers (would need a custom embedding search provider to work).

### Fixed

- Fixed when the `init` function from `config.py` is called to allow custom LLM providers to be registered inside.
- [#93](https://github.com/NVIDIA/NeMo-Guardrails/pull/93): Removed redundant `hasattr` check in `nemoguardrails/llm/params.py`.
- [#91](https://github.com/NVIDIA/NeMo-Guardrails/issues/91): Fixed how default context variables are initialized.

## [0.4.0] - 2023-08-03

### Added

- [Event-based API](docs/user_guides/advanced/event-based-api.md) for guardrails.
- Support for message with type "event" in [`LLMRails.generate_async`](./docs/api/nemoguardrails.rails.llm.llmrails.md#method-llmrailsgenerate_async).
- Support for [bot message instructions](docs/user_guides/advanced/bot-message-instructions.md).
- Support for [using variables inside bot message definitions](docs/user_guides/colang-language-syntax-guide.md#bot-messages-with-variables).
- Support for `vicuna-7b-v1.3` and `mpt-7b-instruct`.
- Topical evaluation results for `vicuna-7b-v1.3` and `mpt-7b-instruct`.
- Support to use different models for different LLM tasks.
- Support for [red-teaming](docs/user_guides/advanced/red-teaming.md) using challenges.
- Support to disable the Chat UI when running the server using `--disable-chat-ui`.
- Support for accessing the API request headers in server mode.
- Support to [enable CORS settings](docs/user_guides/server-guide.md#cors) for the guardrails server.

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

- Support for defining [subflows](docs/user_guides/colang-language-syntax-guide.md#subflows).
- Improved support for [customizing LLM prompts](docs/user_guides/advanced/prompt-customization.md)
  - Support for using filters to change how variables are included in a prompt template.
  - Output parsers for prompt templates.
  - The `verbose_v1` formatter and output parser to be used for smaller models that don't understand Colang very well in a few-shot manner.
  - Support for including context variables in prompt templates.
  - Support for chat models i.e. prompting with a sequence of messages.
- Experimental support for allowing the LLM to generate [multi-step flows](docs/user_guides/configuration-guide.md#multi-step-generation).
- Example of using Llama Index from a guardrails configuration (#40).
- [Example](examples/configs/llm/hf_endpoint) for using HuggingFace Endpoint LLMs with a guardrails configuration.
- [Example](examples/configs/llm/hf_pipeline_dolly) for using HuggingFace Pipeline LLMs with a guardrails configuration.
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

- Support to [connect any LLM](docs/user_guides/configuration-guide.md#supported-llm-models) that implements the BaseLanguageModel interface from  LangChain.
- Support for [customizing the prompts](docs/user_guides/configuration-guide.md#llm-prompts) for specific LLM models.
- Support for [custom initialization](docs/user_guides/configuration-guide.md#configuration-guide) when loading a configuration through `config.py`.
- Support to extract [user-provided values](docs/user_guides/advanced/extract-user-provided-values.md) from utterances.

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
