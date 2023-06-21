# GuardRails Evaluation

We propose a set of tools that can be used to evaluate the different types of rails implemented in NeMo Guardrails.
In the current version, these tools are designed to test the performance of each type of rail individually.

The evaluation tools can be easily used from the CLI. Examples will be provided for each type of rail.

At the same time, we provide preliminary results on the performance of the rails on a set of public datasets, relevant for each task at hand.


## Topical Rails

**Aim and Usage**

Topical rails evaluation focuses on the core mechanism used by NeMo Guardrails to guide conversations using canonical forms and dialogue flows.
More details about this core functionality is explained [here](./../../docs/architecture/README.md).

Thus, when using topical rails evaluation, we are actually assessing the performance for:
1. User canonical form generation
2. Next step generation - in the current approach, we only assess the performance of bot canonical forms as next step in a flow
3. Bot message generation

To use the topical rails evaluation tool, the CLI command is:

`nemoguardrails evaluate topical --config=<rails_app_path> --verbose`

A topical rails evaluation has the following CLI parameters:

- `config`: The Guardrails app to be evaluated.
- `verbose`: If the Guardrails app should be run in verbose mode
- `test_percentage`: Percentage of the samples for an intent to be used as test set
- `max_tests_intent`: Maximum number of test samples per intent to be used when testing
(useful to have balanced test data for unbalanced datasets). If the value is 0,
this parameter is not used.
- `max_samples_intent`: Maximum number of samples per intent to be used in the
vector database. If the value is 0, all samples not in test set are used.
- `results_frequency`: If we want to print intermediate results about the
current evaluation, this is the step.

**Evaluation Results**

For the initial evaluation experiments for topical rails, we have used two datasets used for conversational NLU:
- [_chit-chat_](https://github.com/RasaHQ/rasa-demo/blob/main/data/nlu/chitchat.yml) dataset
- [_banking_](https://github.com/PolyAI-LDN/task-specific-datasets/tree/master/banking_data) dataset

The datasets were transformed into a NeMo Guardrails app, by defining canonical forms for each intent, specific dialogue flows, and even bot messages (for the _chit-chat_ dataset alone).
The two datasets have a large number of user intents, thus topical rails. One of them is very generic and with higher-grained intents (_chit-chat_), while the _banking_ dataset is domain-specific and more fine-grained.

Preliminary evaluation results follow next.

| Dataset   | # intents | # test samples |
|-----------|-----------|----------------|
| chit-chat | 76        | 226            |
| banking   | 77        | 231            |


## Execution Rails

## Fact-checking Rails

Details about fact-checking evaluation.

## Moderation Rails

Details about moderation evaluation.

## Hallucination Rails

Details about hallucination evaluation.
