# Retrieval-Augmented Generation

This guide will teach you how to apply a guardrails configuration in a RAG scenario. This guide builds on the [previous guide](../6_topical_rails), developing further the demo ABC Bot.

## Prerequisites

Set up an OpenAI API key, if not already set.

```bash
export OPENAI_API_KEY=$OPENAI_API_KEY    # Replace with your own key
```

If you're running this inside a notebook, you also need to patch the AsyncIO loop.

```python
import nest_asyncio

nest_asyncio.apply()
```

## Usage

There are two modes in which you can use a guardrails configuration in conjunction with RAG:

1. **Relevant Chunks**: perform the retrieval yourself and pass the **relevant chunks** directly to the `generate` method.
2. **Knowledge Base**: configure a **knowledge base** directly into the guardrails configuration and let NeMo Guardrails manage the retrieval part.

### Relevant Chunks

In the previous guide, we've seen that asking "How many free vacation days do I have per year" yields a general response:

```python
from nemoguardrails import RailsConfig, LLMRails

config = RailsConfig.from_path("./config")
rails = LLMRails(config)

response = rails.generate(messages=[{
    "role": "user",
    "content": "How many vacation days do I have per year?"
}])
print(response["content"])
```

```
Full-time employees are eligible for up to two weeks of paid vacation time per year. Part-time employees receive a prorated amount based on their hours worked. Please refer to the employee handbook for more information.
```

Let's assume that at the ABC company, the following is included in the Employee Handbook:

```markdown
Employees are eligible for the following time off:

* Vacation: 20 days per year, accrued monthly.
* Sick leave: 15 days per year, accrued monthly.
* Personal days: 5 days per year, accrued monthly.
* Paid holidays: New Year's Day, Memorial Day, Independence Day, Thanksgiving Day, Christmas Day.
* Bereavement leave: 3 days paid leave for immediate family members, 1 day for non-immediate family members.
```

We can pass this information directly when making the `generate` call:

```python
response = rails.generate(messages=[{
    "role": "context",
    "content": {
        "relevant_chunks": """
            Employees are eligible for the following time off:
              * Vacation: 20 days per year, accrued monthly.
              * Sick leave: 15 days per year, accrued monthly.
              * Personal days: 5 days per year, accrued monthly.
              * Paid holidays: New Year's Day, Memorial Day, Independence Day, Thanksgiving Day, Christmas Day.
              * Bereavement leave: 3 days paid leave for immediate family members, 1 day for non-immediate family members. """
    }
},{
    "role": "user",
    "content": "How many vacation days do I have per year?"
}])
print(response["content"])
```

```
Eligible employees receive 20 days of paid vacation time per year, which accrues monthly. You can find more information about this in the employee handbook.
```

As expected, we now receive the correct answer.

### Knowledge Base

There are three ways you can configure a knowledge base directly into a guardrails configuration:

1. Using the `kb` folder.
2. Using a custom `retrieve_relevant_chunks` action.
3. Using a custom `EmbeddingSearchProvider`.

For option 1, you can add a knowledge base directly into your guardrails configuration by creating a `kb` folder inside the `config` folder and adding documents there. Currently, only the Markdown format is supported. For a quick example, check out the complete implementation of the [ABC Bot](../../../examples/bots/abc).

Options 2 and 3 represent advanced use cases and will soon detailed in separate guides.

## Wrapping Up

This guide introduced briefly how a guardrails configuration can be used in the context of a RAG setup.

## Next

To continue learning about NeMo Guardrails, check out:
1. [Guardrails Library](../../user_guides/guardrails-library.md).
2. [Configuration Guide](../../user_guides/configuration-guide.md).
