# Integration with LangChain

There are multiple ways of using the NeMo Guardrails toolkit together with LangChain in your project:

1. Use existing chains in your guardrails: [Jump to section](#use-chains-in-your-custom-actions)
2. Add guardrails to existing chains: [Jump to section](#add-guardrails-to-existing-chains)
3. Use chains in your custom actions: [Jump to section](#use-chains-in-your-custom-actions)
4. Use LangChain tools as actions in your guardrails: [Jump to section](#use-langchain-tools-as-actions-in-your-guardrails)
5. Use `RailsChain` - **coming soon**
6. Use `RailsAgent` - **coming soon**

## Use existing chains in your guardrails

Existing LangChain chains can be used as actions when defining guardrails in Colang. For example, to set up a guardrail that uses the `ConstitutionalChain`([link](https://python.langchain.com/en/latest/modules/chains/examples/constitutional_chain.html)), the following is required.

- First, initialize and register the chain as an action:

  ```python
  app = LLMRails(config)

  constitutional_chain = ConstitutionalChain.from_llm(
      llm=app.llm,
      chain=ContextVarChain(var_name="last_bot_message"),
      constitutional_principles=[
          ConstitutionalPrinciple(
              critique_request="Tell if this answer is good.",
              revision_request="Give a better answer.",
          )
      ],
  )

  app.register_action(constitutional_chain, name="check_if_constitutional")
  ```

- Then, use it in a flow:
  ```
  define flow
    user ...
    bot respond
    $updated_msg = execute check_if_constitutional
    if $updated_msg != $last_bot_message
      bot remove last message
      bot $updated_msg
  ```
Checkout [this sample script](../../examples/scripts/demo_chain_as_action.py) for the complete example.

## Add guardrails to existing chains

If a chain performs a specific task, e.g., question answering, guardrails can be added to it by including it in a guardrails configuration. In the example below, we add a simple guardrail against insults for a `RetrievalQA` chain.

**Python code:**

```python
config = RailsConfig.from_content(...)
app = LLMRails(config)

qa_chain = get_qa_chain(app.llm)
app.register_action(qa_chain, name="qa_chain")
```
**Colang flows:**
```colang
define user express insult
  "You are stupid"

# Basic guardrail against insults.
define flow
  user express insult
  bot express calmly willingness to help

define flow
  user ...
  $answer = execute qa_chain(query=$last_user_message)
  bot $answer
```

Checkout [this sample script](../../examples/scripts/demo_chain_with_guardrails.py) for a complete example.

## Use chains in your custom actions

In a custom action, you can define the keyword argument `llm` and it will automatically be filled with the `BaseLLM` instance. You can then use it to create any chain you want as part of the action.

Example:

```python
async def check_facts(
    llm: BaseLLM,
):
    """Checks the facts for the bot response."""
    ...

    prompt = PromptTemplate(
        template=fact_check_template, input_variables=["evidence", "response"]
    )

    fact_check_chain = LLMChain(prompt=prompt, llm=llm)
    entails = await fact_check_chain.apredict(
        evidence=evidence, response=bot_response
    )

    ...
```

## Use LangChain tools as actions in your guardrails

The NeMo Guardrails toolkit comes with pre-built wrappers for some of the most common tools, and you can use them directly as actions. The initial list includes: `apify`, `bing_search`,  `google_search`, `searx_search`, `google_serper`, `openweather_query`, `serp_api_query`,  `wikipedia_query`, `wolfram_alpha_query` and `zapier_nla_query`.

Below is a quick example for sharing something on slack when the user requests that.

```colang
define flow
  user request share on slack
  execute zapier_nla_query(query=$last_user_message)
```
