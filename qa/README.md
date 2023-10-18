# QA Started

This is a QA started guide for using automated tests to test all the examples in `nemoguardrails/examples` folder. This guide will cover:

1. Software installation prerequisites;
2. Download models required by NLTK;
3. Running automated tests;
4. Analyzing logs if there are any failure(s).

## Installation

1. Install NLTK for validating bot response.

 ```bash
 > sudo apt update
 > sudo apt install python3-nltk
 ```

2. Download models required by NLTK.

 ```bash
 > python3
 > import nltk
 > nltk.download('punkt')
 > nltk.download('averaged_perceptron_tagger')
 > nltk.download('wordnet')
 > exit()
 ```

## Running automated tests to test all the examples in `nemoguardrails/examples` folder.

Please refer to the [installation guide](installation-guide.md) for instructions on how to install the NeMo Guardrails toolkit.

1. Make sure that you have the `OPENAI_API_KEY` and `WOLFRAM_ALPHA_APP_ID` environment variables set.

 ```bash
 > export OPENAI_API_KEY=...
 > export WOLFRAM_ALPHA_APP_ID=...
 ```

2. Change the directory to `nemoguardrails/qa` folder, and then run all the automated tests

 ```bash
 > QA=True python -m pytest test_*.py
 ```

NOTE: The QA tests are skipped by default as they are expensive (i.e., they make live call to OpenAI and other services). To enable them, you have to set the `QA` environment variable.

Alternatively, you can also run the tests from the root of the project:

```bash
> QA=True pytest qa
```

3. If there are any failure(s), analyze the corresponding example test log.

 ```bash
 > ls -l *.log
 > moderation_rail.log
 > execution_rails.log
 > grounding_rail.log
 > jailbreak_check.log
 > topical_rail.log
 ```
