<!-- markdownlint-disable -->

# API Overview

## Modules

- [`nemoguardrails.context`](./nemoguardrails.context.md#module-nemoguardrailscontext)
- [`nemoguardrails.embeddings.basic`](./nemoguardrails.embeddings.basic.md#module-nemoguardrailsembeddingsbasic)
- [`nemoguardrails.embeddings.index`](./nemoguardrails.embeddings.index.md#module-nemoguardrailsembeddingsindex)
- [`nemoguardrails.rails.llm.config`](./nemoguardrails.rails.llm.config.md#module-nemoguardrailsrailsllmconfig): Module for the configuration of rails.
- [`nemoguardrails.rails.llm.llmrails`](./nemoguardrails.rails.llm.llmrails.md#module-nemoguardrailsrailsllmllmrails): LLM Rails entry point.
- [`nemoguardrails.streaming`](./nemoguardrails.streaming.md#module-nemoguardrailsstreaming)

## Classes

- [`basic.BasicEmbeddingsIndex`](./nemoguardrails.embeddings.basic.md#class-basicembeddingsindex): Basic implementation of an embeddings index.
- [`basic.OpenAIEmbeddingModel`](./nemoguardrails.embeddings.basic.md#class-openaiembeddingmodel): Embedding model using OpenAI API.
- [`basic.SentenceTransformerEmbeddingModel`](./nemoguardrails.embeddings.basic.md#class-sentencetransformerembeddingmodel): Embedding model using sentence-transformers.
- [`index.EmbeddingModel`](./nemoguardrails.embeddings.index.md#class-embeddingmodel): The embedding model is responsible for creating the embeddings.
- [`index.EmbeddingsIndex`](./nemoguardrails.embeddings.index.md#class-embeddingsindex): The embeddings index is responsible for computing and searching a set of embeddings.
- [`index.IndexItem`](./nemoguardrails.embeddings.index.md#class-indexitem): IndexItem(text: str, meta: Dict = <factory>)
- [`config.CoreConfig`](./nemoguardrails.rails.llm.config.md#class-coreconfig): Settings for core internal mechanics.
- [`config.DialogRails`](./nemoguardrails.rails.llm.config.md#class-dialograils): Configuration of topical rails.
- [`config.Document`](./nemoguardrails.rails.llm.config.md#class-document): Configuration for documents that should be used for question answering.
- [`config.EmbeddingSearchProvider`](./nemoguardrails.rails.llm.config.md#class-embeddingsearchprovider): Configuration of a embedding search provider.
- [`config.FactCheckingRailConfig`](./nemoguardrails.rails.llm.config.md#class-factcheckingrailconfig): Configuration data for the fact-checking rail.
- [`config.InputRails`](./nemoguardrails.rails.llm.config.md#class-inputrails): Configuration of input rails.
- [`config.Instruction`](./nemoguardrails.rails.llm.config.md#class-instruction): Configuration for instructions in natural language that should be passed to the LLM.
- [`config.KnowledgeBaseConfig`](./nemoguardrails.rails.llm.config.md#class-knowledgebaseconfig)
- [`config.MessageTemplate`](./nemoguardrails.rails.llm.config.md#class-messagetemplate): Template for a message structure.
- [`config.Model`](./nemoguardrails.rails.llm.config.md#class-model): Configuration of a model used by the rails engine.
- [`config.OutputRails`](./nemoguardrails.rails.llm.config.md#class-outputrails): Configuration of output rails.
- [`config.Rails`](./nemoguardrails.rails.llm.config.md#class-rails): Configuration of specific rails.
- [`config.RailsConfig`](./nemoguardrails.rails.llm.config.md#class-railsconfig): Configuration object for the models and the rails.
- [`config.RailsConfigData`](./nemoguardrails.rails.llm.config.md#class-railsconfigdata): Configuration data for specific rails that are supported out-of-the-box.
- [`config.RetrievalRails`](./nemoguardrails.rails.llm.config.md#class-retrievalrails): Configuration of retrieval rails.
- [`config.SensitiveDataDetection`](./nemoguardrails.rails.llm.config.md#class-sensitivedatadetection): Configuration of what sensitive data should be detected.
- [`config.SensitiveDataDetectionOptions`](./nemoguardrails.rails.llm.config.md#class-sensitivedatadetectionoptions)
- [`config.SingleCallConfig`](./nemoguardrails.rails.llm.config.md#class-singlecallconfig): Configuration for the single LLM call option for topical rails.
- [`config.TaskPrompt`](./nemoguardrails.rails.llm.config.md#class-taskprompt): Configuration for prompts that will be used for a specific task.
- [`config.UserMessagesConfig`](./nemoguardrails.rails.llm.config.md#class-usermessagesconfig): Configuration for how the user messages are interpreted.
- [`llmrails.LLMRails`](./nemoguardrails.rails.llm.llmrails.md#class-llmrails): Rails based on a given configuration.
- [`streaming.StreamingHandler`](./nemoguardrails.streaming.md#class-streaminghandler): Streaming async handler.

## Functions

- [`basic.init_embedding_model`](./nemoguardrails.embeddings.basic.md#function-init_embedding_model): Initialize the embedding model.
