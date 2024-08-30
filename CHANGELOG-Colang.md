# Changelog

All notable changes to the Colang language and runtime will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0-beta.3] - Unreleased

### Added

* [#673](https://github.com/NVIDIA/NeMo-Guardrails/pull/673) Add support for new Colang 2 keyword `deactivate`.
* [#703](https://github.com/NVIDIA/NeMo-Guardrails/pull/703) Add bot configuration as variable `$system.config`.
* [#709](https://github.com/NVIDIA/NeMo-Guardrails/pull/709) Add basic support for most OpenAI and LLame 3 models.
* [#712](https://github.com/NVIDIA/NeMo-Guardrails/pull/712) Add interaction loop priority levels for flows.
* [#717](https://github.com/NVIDIA/NeMo-Guardrails/pull/717) Add CLI chat debugging commands.

### Changed

* [#669](https://github.com/NVIDIA/NeMo-Guardrails/pull/669) Merged (and removed) utils library file with core library.

### Fixed

* [#672](https://github.com/NVIDIA/NeMo-Guardrails/pull/672) Fixes a event group match bug (e.g. `match $flow_ref.Finished() or $flow_ref.Failed()`)
* [#699](https://github.com/NVIDIA/NeMo-Guardrails/pull/699) Fix issues with ActionUpdated events and user utterance action extraction.

## [2.0-beta.2] - 2024-07-25

This second beta version of Colang brings a set of improvements and fixes.

### Added

Language and runtime:

* [#504](https://github.com/NVIDIA/NeMo-Guardrails/pull/504) Add colang 2.0 syntax error details by @rgstephens.
* [#533](https://github.com/NVIDIA/NeMo-Guardrails/pull/533) Expose global variables in prompting templates.
* [#534](https://github.com/NVIDIA/NeMo-Guardrails/pull/534) Add `continuation on unhandled user utterance` flow to the standard library (`llm.co`).
* [#554](https://github.com/NVIDIA/NeMo-Guardrails/pull/554) Support for NLD intents.
* [#559](https://github.com/NVIDIA/NeMo-Guardrails/pull/559) Support for the `@active` decorator which activates flows automatically.

Other:

* [#591](https://github.com/NVIDIA/NeMo-Guardrails/pull/591) Unit tests for runtime exception handling in flows.

### Changed

* [#576](https://github.com/NVIDIA/NeMo-Guardrails/pull/576) Make `if` / `while` / `when` statements compatible with python syntax, i.e., allow `:` at the end of line.
* [#596](https://github.com/NVIDIA/NeMo-Guardrails/pull/596) Allow `not`, `in`, `is` in generated flow names.
* [#578](https://github.com/NVIDIA/NeMo-Guardrails/pull/578) Improve bot action generation.
* [#594](https://github.com/NVIDIA/NeMo-Guardrails/pull/594) Add more information to Colang syntax errors.
* [#599](https://github.com/NVIDIA/NeMo-Guardrails/pull/599) Runtime processing loop also consumes generated events before completion.
* [#540](https://github.com/NVIDIA/NeMo-Guardrails/pull/540) LLM prompting improvements targeting `gpt-4o`.

### Fixed

* [#525](https://github.com/NVIDIA/NeMo-Guardrails/pull/525) Fix string expression double braces.
* [#531](https://github.com/NVIDIA/NeMo-Guardrails/pull/531) Fix Colang 2 flow activation.
* [#577](https://github.com/NVIDIA/NeMo-Guardrails/pull/577) Remove unnecessary print statements in runtime.
* [#593](https://github.com/NVIDIA/NeMo-Guardrails/pull/593) Fix `match` statement issue.
* [#579](https://github.com/NVIDIA/NeMo-Guardrails/pull/579) Fix multiline string expressions issue.
* [#604](https://github.com/NVIDIA/NeMo-Guardrails/pull/604) Fix tracking user talking state issue.
* [#598](https://github.com/NVIDIA/NeMo-Guardrails/pull/598) Fix issue related to a race condition.

## [2.0-beta] - 2024-05-08

### Added

* [Standard library of flows](https://docs.nvidia.com/nemo/guardrails/colang_2/language_reference/the-standard-library.html): `core.co`, `llm.co`, `guardrails.co`, `avatars.co`, `timing.co`, `utils.co`.

### Changed

* Syntax changes:
  * Meta comments have been replaced by the `@meta` and `@loop` decorators:
    * `# meta: user intent` -> `@meta(user_intent=True)` (also user_action, bot_intent, bot_action)
    * `# meta: exclude from llm` -> `@meta(exclude_from_llm=True)`
    * `# meta: loop_id=<loop_id>`  -> `@loop("<loop_id>")`
  * `orwhen` -> `or when`
  * NLD instructions `"""<NLD>"""` -> `..."<NLD>"`
  * Support for `import` statement
  * Regular expressions syntax change `r"<regex>"` -> `regex("<regex>")`
  * String expressions change: `"{{<expression>}}"` -> `"{<expression>}"`

* Chat CLI runtime flags `--verbose` logging format improvements
* Internal event parameter renaming: `flow_start_uid` -> `flow_instance_uid`
* Colang function name changes: `findall` -> `find_all` ,

* Changes to flow names that were previously part of `ccl_*.co` files (which are now part of the standard library):
  * `catch colang errors` -> `notification of colang errors` (core.co)
  * `catch undefined flows` -> `notification of undefined flow start` (core.co)
  * `catch unexpected user utterance` -> `notification of unexpected user utterance` (core.co)
  * `poll llm request response` -> `polling llm request response` (llm.co)
  * `trigger user intent for unhandled user utterance` -> `generating user intent for unhandled user utterance` (llm.co)
  * `generate then continue interaction` -> `llm continue interaction` (llm.co)
  * `track bot talking state` -> `tracking bot talking state` (core.co)
  * `track user talking state` -> `tracking user talking state` (core.co)
  * `track unhandled user intent state` -> `tracking unhandled user intent state` (llm.co)
  * `track visual choice selection state` -> `track visual choice selection state` (avatars.co)
  * `track user utterance state` -> `tracking user talking state` (core.co)
  * `track bot utterance state` -> No replacement yet (copy to your bot script)
  * `interruption handling bot talking` -> `handling bot talking interruption` (avatars.co)
  * `generate then continue interaction` -> `llm continue interaction` (llm.co)

## [2.0-alpha] - 2024-02-28

[Colang 2.0](https://docs.nvidia.com/nemo/guardrails/colang_2/overview.html) represents a complete overhaul of both the language and runtime. Key enhancements include:

### Added

* A more powerful flows engine supporting multiple parallel flows and advanced pattern matching over the stream of events.
* A standard library to simplify bot development.
* Smaller set of core abstractions: flows, events, and actions.
* Explicit entry point through the main flow and explicit activation of flows.
* Asynchronous actions execution.
* Adoption of terminology and syntax akin to Python to reduce the learning curve for new developers.
