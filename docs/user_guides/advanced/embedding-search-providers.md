# Embedding Search Providers

NeMo Guardrails uses embedding search (a.k.a. vector databases) for implementing the [guardrails process](../../architecture/README.md#the-guardrails-process) and for the [knowledge base](../configuration-guide.md#knowledge-base-documents) functionality.

The default embedding search uses FastEmbed for computing the embeddings (the `all-MiniLM-L6-v2` model) and Annoy for performing the search.

The default configuration is the following:

```yaml
core:
  embedding_search_provider:
    name: default
    parameters:
      embedding_engine: FastEmbed
      embedding_model: all-MiniLM-L6-v2

knowledge_base:
  embedding_search_provider:
    name: default
    parameters:
      embedding_engine: FastEmbed
      embedding_model: all-MiniLM-L6-v2
```

The default embedding search provider can also work with OpenAI embeddings:

```yaml
core:
  embedding_search_provider:
    name: default
    parameters:
      embedding_engine: openai
      embedding_model: text-embedding-ada-002

knowledge_base:
  embedding_search_provider:
    name: default
    parameters:
      embedding_engine: openai
      embedding_model: text-embedding-ada-002
```

## Custom Embedding Search Providers

You can implement your own custom embedding search provider by subclassing `EmbeddingsIndex`. For quick reference, the complete interface is included below:

```python
class EmbeddingsIndex:
    """The embeddings index is responsible for computing and searching a set of embeddings."""

    @property
    def embedding_size(self):
        raise NotImplementedError

    async def add_item(self, item: IndexItem):
        """Adds a new item to the index."""
        raise NotImplementedError()

    async def add_items(self, items: List[IndexItem]):
        """Adds multiple items to the index."""
        raise NotImplementedError()

    async def build(self):
        """Build the index, after the items are added.

        This is optional, might not be needed for all implementations."""
        pass

    async def search(self, text: str, max_results: int) -> List[IndexItem]:
        """Searches the index for the closest matches to the provided text."""
        raise NotImplementedError()

@dataclass
class IndexItem:
    text: str
    meta: Dict = field(default_factory=dict)
```

In order to use your custom embedding search provider, you have to register it in your `config.py`:

```python
def init(app: LLMRails):
    app.register_embedding_search_provider("simple", SimpleEmbeddingSearchProvider)
```

For a complete example, check out [this test configuration](../../../tests/test_configs/with_custom_embedding_search_provider).
