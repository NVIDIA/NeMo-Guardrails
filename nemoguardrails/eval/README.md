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
1. User canonical form (intent) generation
2. Next step generation - in the current approach, we only assess the performance of bot canonical forms as next step in a flow
3. Bot message generation

To use the topical rails evaluation tool, the CLI command is:

`nemoguardrails evaluate topical --config=<rails_app_path> --verbose`

A topical rails evaluation has the following CLI parameters:

- `config`: The Guardrails app to be evaluated.
- `verbose`: If the Guardrails app should be run in verbose mode
- `test-percentage`: Percentage of the samples for an intent to be used as test set
- `max-tests-intent`: Maximum number of test samples per intent to be used when testing
(useful to have balanced test data for unbalanced datasets). If the value is 0,
this parameter is not used.
- `max-samples-intent`: Maximum number of samples per intent to be used in the
vector database. If the value is 0, all samples not in test set are used.
- `results-frequency`: If we want to print intermediate results about the
current evaluation, this is the step.
- `sim-threshold`: If larger than 0, for intents that do not have an exact match
pick the most similar intent above this threshold.
- `random-seed`: Random seed used by the evaluation.
- `output-dir`: Output directory for predictions.


**Evaluation Results**

For the initial evaluation experiments for topical rails, we have used two datasets used for conversational NLU:
- [_chit-chat_](https://github.com/rahul051296/small-talk-rasa-stack) dataset
- [_banking_](https://github.com/PolyAI-LDN/task-specific-datasets/tree/master/banking_data) dataset

The datasets were transformed into a NeMo Guardrails app, by defining canonical forms for each intent, specific dialogue flows, and even bot messages (for the _chit-chat_ dataset alone).
The two datasets have a large number of user intents, thus topical rails. One of them is very generic and with higher-grained intents (_chit-chat_), while the _banking_ dataset is domain-specific and more fine-grained.
More details about running the topical rails evaluation experiments and the evaluation datasets is available [here](./data/topical/README.md).

Preliminary evaluation results follow next. In all experiments, we have chosen to have a balanced test set with at most 3 samples per intent.
For both datasets, we have assessed the performance for various LLMs and also for the number of samples (`k = all, 3, 1`) per intent that are indexed in the vector database.

Take into account that the performance of an LLM is heavily dependent on the prompt, especially due to the more complex [prompt used by Guardrails](./../../docs/architecture/README.md#example-prompt).
Therefore, at the current moment we only release the results for OpenAI models, but more results will follow in next releases. All results are preliminary as better prompting can improve them.

Important lessons to be learned from the evaluation results:
- Each step in the three-step approach (user intent, next step / bot intent, bot message) used by Guardrails offers an improvement in performance.
- It is important to have at least k=3 samples in the vector database for each user intent (canonical form) for achieving good performance.
- Some models (e.g., gpt-3.5-turbo) produce a wider variety of canonical forms, even with the few-shot prompting used by Guardrails. In these cases, it is useful to add a similarity match instead of exact match for user intents. In this case, the similarity threshold becomes an important inference parameter.
- Initial results show that even small models, e.g. [dolly-v2-3b](https://huggingface.co/databricks/dolly-v2-3b), [vicuna-7b-v1.3](https://huggingface.co/lmsys/vicuna-7b-v1.3), [mpt-7b-instruct](https://huggingface.co/mosaicml/mpt-7b-instruct), [falcon-7b-instruct](https://huggingface.co/tiiuae/falcon-7b-instruct), have good performance for topical rails. Out of these, Falcon 7B Instruct seems to be the best performing model.

Evaluation Date - June 21, 2023. Updated July 24, 2023 for Dolly, Vicuna and Mosaic MPT models.

| Dataset   | # intents | # test samples |
|-----------|-----------|----------------|
| chit-chat | 76        | 226            |
| banking   | 77        | 231            |

Results on _chit-chat_ dataset, metric used is accuracy.


| Model                       | User intent, `w.o sim` | User intent, `sim=0.6` | Bot intent, `w.o sim` | Bot intent, `sim=0.6` | Bot message, `w.o sim` | Bot message, `sim=0.6` |
|-----------------------------|------------------------|------------------------|-----------------------|-----------------------|------------------------|------------------------|
| `text-davinci-003, k=all`   | 0.89                   | 0.89                   | 0.90                  | 0.90                  | 0.91                   | 0.91                   |
| `text-davinci-003, k=3`     | 0.82                   | N/A                    | 0.85                  | N/A                   | N/A                    | N/A                    |
| `text-davinci-003, k=1`     | 0.65                   | N/A                    | 0.73                  | N/A                   | N/A                    | N/A                    |
| `gpt-3.5-turbo, k=all`      | 0.44                   | 0.56                   | 0.50                  | 0.61                  | 0.54                   | 0.65                   |
| `dolly-v2-3b, k=all`        | 0.80                   | 0.82                   | 0.81                  | 0.83                  | 0.81                   | 0.83                   |
| `vicuna-7b-v1.3, k=all`     | 0.62                   | 0.75                   | 0.69                  | 0.77                  | 0.71                   | 0.79                   |
| `mpt-7b-instruct, k=all`    | 0.73                   | 0.81                   | 0.78                  | 0.82                  | 0.80                   | 0.82                   |
| `falcon-7b-instruct, k=all` | 0.81                   | 0.81                   | 0.81                  | 0.82                  | 0.82                   | 0.82                   |


Results on _banking_ dataset, metric used is accuracy.


| Model                       | User intent, `w.o sim` | User intent, `sim=0.6` | Bot intent, `w.o sim` | Bot intent, `sim=0.6` | Bot message, `w.o sim` | Bot message, `sim=0.6` |
|-----------------------------|------------------------|------------------------|-----------------------|-----------------------|------------------------|------------------------|
| `text-davinci-003, k=all`   | 0.77                   | 0.82                   | 0.83                  | 0.84                  | N/A                    | N/A                    |
| `text-davinci-003, k=3`     | 0.65                   | N/A                    | 0.73                  | N/A                   | N/A                    | N/A                    |
| `text-davinci-003, k=1`     | 0.50                   | N/A                    | 0.63                  | N/A                   | N/A                    | N/A                    |
| `gpt-3.5-turbo, k=all`      | 0.38                   | 0.73                   | 0.45                  | 0.73                  | N/A                    | N/A                    |
| `dolly-v2-3b, k=all`        | 0.32                   | 0.62                   | 0.40                  | 0.64                  | N/A                    | N/A                    |
| `vicuna-7b-v1.3, k=all`     | 0.39                   | 0.62                   | 0.54                  | 0.65                  | N/A                    | N/A                    |
| `mpt-7b-instruct, k=all`    | 0.45                   | 0.58                   | 0.50                  | 0.60                  | N/A                    | N/A                    |
| `falcon-7b-instruct, k=all` | 0.70                   | 0.75                   | 0.76                  | 0.78                  | N/A                    | N/A                    |


## Execution Rails

### Fact-checking Rails

The default fact checking rail is implemented as an entailment prediction problem. Given an evidence and the predicted answer, we make an LLM call to predict whether the answer is grounded in the evidence or not.

To run the fact checking rail, you can use the following CLI command:

```nemoguardrails evaluate fact-checking```

Here is a list of arguments that you can use to configure the fact checking rail:

- `dataset-path`: Path to the dataset. It should be a json file with the following format:

    ```
    [
        {
            "question": "question text",
            "answer": "answer text",
            "evidence": "evidence text",
        },
    }
    ```
    ,
- `llm`: The LLM provider to use. Default is openai.
- `model-name`: The name of the model to use. Default is text-davinci-003.
- `num-samples`: Number of samples to run the eval on. Default is 50.
- `create-negatives`: Whether to generate synthetic negative examples or not. Default is True.
- `output-dir`: The directory to save the output to. Default is eval_outputs/factchecking.
- `write-outputs`: Whether to write the outputs to a file or not. Default is True.

More details on how to set up the data in the right format and run the evaluation on your own dataset can be found [here](./data/factchecking/README.md).

#### Evaluation Results

We evaluate the performance of the fact checking rail on the [MSMARCO](https://huggingface.co/datasets/ms_marco) dataset. We randomly sample 100 (question, answer, evidence) triples and run the evaluation using OpenAI `text-davinci-003` and `gpt-3.5-turbo` models.

Evaluation Date - June 02, 2023.

We breakdown the performance into positive entailment accuracy and negative entailment accuracy. Positive entailment accuracy is the accuracy of the model in correctly identifying answers that are grounded in the evidence passage. Negative entailment accuracy is the accuracy of the model on correctly identifying answers that are **not** grounded in the evidence. Details on how to create synthetic negative examples can be found [here](./data/factchecking/README.md)

| Model | Positive Entailment Accuracy  | Negative Entailment Accuracy | Overall Accuracy |
|-------|----------| ---------------------------- | ----------------------------- |
| text-davinci-003 | 0.83 | 0.87 | 0.85 |
| gpt-3.5-turbo | 0.87 | 0.80 | 0.83 |


### Moderation Rails

The moderation rails involve two components - the jailbreak detection rail and the output moderation rail.
* The jailbreak detection rail attempts to flag user inputs that could potentially cause the model to output unsafe content.
* The output moderation rail attempts to filter the language model output to avoid unsafe content from being displayed to the user.

The jailbreak and output moderation rails can be evaluated using the following CLI command:

```nemoguardrails evaluate moderation```

The various arguments that can be passed to evaluate the moderation rails are

- `model_name`: Name of the model to use. Default is 'text-davinci-003'.
- `llm`: Name of the LLM provide. Default is 'openai'.
- `dataset-path`: Path to the dataset to evaluate the rails on. The dataset should contain one prompt per line.
- `split`: The split of the dataset. This can be either 'helpful' or 'harmful'. This is used to determine the appropriate label for the predictions.
- `num-samples`: Number of samples to evaluate. Default is 50.
- `check-jailbreak`: Whether to evaluate the jailbreak rail. Default is True.
- `check-output_moderation`: Whether to evaluate the output moderation rail. Default is True.
- `output-path`: Folder to write the results to. Default is 'eval_outputs/moderation'.

It is also possible to evaluate each of the rails individually. To evaluate the jailbreak rail only, use the following command:

```nemoguardrails evaluate moderation --check-output-moderation False```

and to evaluate the output moderation rail only, use the following command:

```nemoguardrails evaluate moderation --check-jailbreak False```

More details on how to set up the data in the right format and run the evaluation on your own dataset can be found [here](./data/moderation/README.md).

#### Evaluation Results

We evaluate the moderation rails on the Anthropic [Red Team Attempts dataset](https://huggingface.co/datasets/Anthropic/hh-rlhf/tree/main/red-team-attempts) and the Anthropic [Helpful Base dataset](https://huggingface.co/datasets/Anthropic/hh-rlhf/tree/main/helpful-base). This dataset contains prompts that are labeled by humans as either helpful or harmful. We randomly sample 100 prompts from each of the splits and run the evaluation using OpenAI `text-davinci-003` and `gpt-3.5-turbo` models.

Evaluation Date - June 02, 2023.

We breakdown the performance of the models on the two rails into the following metrics:

* % of the prompts that are **blocked** on the Red Team Attempts dataset
* % of the prompts that are **allowed** on the Helpful Base dataset

We want the models to block as many harmful prompts as possible and allow as many helpful prompts as possible.

#### Moderation Rails Performance

| Model | % of harmful prompts blocked | % of helpful prompts allowed |
|-------|----------| ---------------------------- |
| text-davinci-003 | 80 | 97 |
| gpt-3.5-turbo | 70 | 100 |

### Hallucination Rails

For general questions that the model uses parametric knowledge to answer, we can define a hallucination rail to detect when the model is potentially making up facts. The default implementation of the hallucination rails is based on [SelfCheckGPT](https://arxiv.org/abs/2303.08896).

* Given a question, we sample multiple answers from the model, often at a high temperature (temp=1.0).
* We then check if the answers are consistent with each other. This agreement check is implemented using an LLM call similar to the fact checking rail.
* If the answers are inconsistent, it indicates that the model might be hallucinating.

To run the hallucination rail, use the following CLI command:

```nemoguardrails evaluate hallucination```

Here is a list of arguments that you can use to configure the hallucination rail:

- `dataset-path`: Path to the dataset. It should be a text file with one question per line.
- `llm`: The LLM provider to use. Default is openai.
- `model-name`: The name of the model to use. Default is text-davinci-003.
- `num-samples`: Number of samples to run the eval on. Default is 50.
- `output-dir`: The directory to save the output to. Default is eval_outputs/hallucination.
- `write-outputs`: Whether to write the outputs to a file or not. Default is True.

To evaluate the hallucination rail on your own dataset, you can follow the create a text file with the list of questions and run the evaluation using the following command

```nemoguardrails evaluate hallucination --dataset-path <path-to-your-text-file>```

#### Evaluation Results

To evaluate the hallucination rail, we manually curate a set of [questions](./data/hallucination/sample.txt) which mainly consists of questions with a false premise, i.e., questions that cannot have a correct answer.

For example, the question "What is the capital of the moon?" has a false premise since the moon does not have a capital. Since the question is stated in a way that implies that the moon has a capital, the model might be tempted to make up a fact and answer the question.

We then run the hallucination rail on these questions and check if the model is able to detect the hallucination. We run the evaluation using OpenAI `text-davinci-003` and `gpt-3.5-turbo` models.

Evaluation Date - June 12, 2023.

We breakdown the performance into the following metrics:

* % of questions that are intercepted by the model, i.e., % of questions where the model detects are not answerable
* % of questions that are intercepted by model + hallucination rail, i.e., % of questions where the either the model detects are not answerable or the hallucination rail detects that the model is making up facts

| Model | % intercepted - model |% intercepted - model + hallucination rail|
|-------|----------| ---------------------------- |
| text-davinci-003 | 0 | 70 |
| gpt-3.5-turbo |65 | 90 |

We find that gpt-3.5-turbo is able to intercept 65% of the questions and identify them as not answerable on its own. Adding the hallucination rail helps intercepts 25% more questions and prevents the model from making up facts.
