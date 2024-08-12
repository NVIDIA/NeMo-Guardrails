# Evaluation Tooling

NeMo Guardrails provides a set of tools for evaluating the performance of a guardrail configuration.

## Introduction

A guardrail evaluation has three main components:
1. Compliance Rate
2. Resource Usage
3. Latency

## CLI

You can run evaluations and inspect the results using the CLI `nemoguardrails eval`.

Usage:
```bash
nemoguardrails eval [OPTIONS] COMMAND [ARGS]...
```

### Commands

- `run`: Run a set of interactions through a guardrail configuration.
- `check`: Check compliance against the policies.
- `review`: Review the interactions included in the evaluation.
- `summary`: Show a summary of the evaluation.
- `rail`: Run a rail evaluation task.**

### Description

The `nemoguardrails eval` command is used to evaluate specific rails or the overall system. It supports several subcommands each tailored to a specific part of the evaluation process.

### Overall Evaluation

To run an overall evaluation, use the following command:

```bash
nemoguardrails eval run \
  --eval-config-path=<PATH_TO_EVAL_CONFIG> \
  --guardrail-config-path=<PATH_TO_GUARDRAIL_CONFIG> \
  --output-path=<PATH_FOR_OUTPUT_FILES>
```

This executes an evaluation based on the specified configurations. You can set the paths for evaluation and guardrail configuration files, and define where the output should be stored.

#### Options

- `--eval-config-path TEXT`: Path to a directory containing evaluation configuration files. This option has a default value which points to the `config` folder in the current directory.
  - Default: `config`

- `--guardrail-config-path TEXT`: **Required**. Path to a directory containing guardrail configuration files. This is a mandatory field and does not have a default value.
  - Default: None

- `--output-path TEXT`: Output directory for the evaluation results. If not specified, the results are saved in a folder within the current directory that matches the name of the guardrail configuration.
  - Default: Depends on the guardrail configuration name.
