from nemoguardrails import LLMRails, RailsConfig
from langchain.llms.base import BaseLLM

from typing import Callable, Any, Coroutine

COLANG_CONFIG = """
define user express greeting
  "hi"

define user express ill intent
  "I hate you"
  "I want to destroy the world"

define bot express cannot respond
  "I'm sorry I cannot help you with that."

define user express question
   "What is the current unemployment rate?"

# Basic guardrail example
define flow
  user express ill intent
  bot express cannot respond

# Question answering flow
define flow
  user ...
  $answer = execute llama_index_query(query=$last_user_message)
  bot $answer

"""

YAML_CONFIG = """
models:
  - type: main
    engine: openai
    model: text-davinci-003
"""


def demo():
    try:
        import llama_index
        from llama_index.indices.query.base import BaseQueryEngine
        from llama_index.response.schema import StreamingResponse

    except ImportError:
        raise ImportError(
            "Could not import llama_index, please install it with "
            "`pip install llama_index`."
        )

    config = RailsConfig.from_content(COLANG_CONFIG, YAML_CONFIG)
    app = LLMRails(config)

    def _get_llama_index_query_engine(llm: BaseLLM):
        docs = llama_index.SimpleDirectoryReader(
            input_files=["../examples/grounding_rail/kb/report.md"]
        ).load_data()
        llm_predictor = llama_index.LLMPredictor(llm=llm)
        index = llama_index.GPTVectorStoreIndex.from_documents(
            docs, llm_predictor=llm_predictor
        )
        default_query_engine = index.as_query_engine()
        return default_query_engine

    def _get_callable_query_engine(
        query_engine: BaseQueryEngine,
    ) -> Callable[[str], Coroutine[Any, Any, str]]:
        async def get_query_response(query: str) -> str:
            response = query_engine.query(query)
            if isinstance(response, StreamingResponse):
                typed_response = response.get_response()
            else:
                typed_response = response
            response_str = typed_response.response
            if response_str is None:
                return ""
            return response_str

        return get_query_response

    query_engine = _get_llama_index_query_engine(app.llm)
    app.register_action(
        _get_callable_query_engine(query_engine), name="llama_index_query"
    )

    history = [{"role": "user", "content": "What is the current unemployment rate?"}]
    result = app.generate(messages=history)
    print(result)


if __name__ == "__main__":
    demo()
