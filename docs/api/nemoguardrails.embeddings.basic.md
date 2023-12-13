<!-- markdownlint-disable -->

<a href="../../nemoguardrails/embeddings/basic.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

# <kbd>module</kbd> `nemoguardrails.embeddings.basic`





---

<a href="../../nemoguardrails/embeddings/basic.py#L145"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>function</kbd> `init_embedding_model`

```python
init_embedding_model(
    embedding_model: str,
    embedding_engine: str
) → EmbeddingModel
```

Initialize the embedding model.


---

<a href="../../nemoguardrails/embeddings/basic.py#L24"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `BasicEmbeddingsIndex`
Basic implementation of an embeddings index.

It uses `sentence-transformers/all-MiniLM-L6-v2` to compute the embeddings. It uses Annoy to perform the search.

<a href="../../nemoguardrails/embeddings/basic.py#L31"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `BasicEmbeddingsIndex.__init__`

```python
__init__(embedding_model=None, embedding_engine=None, index=None)
```






---

#### <kbd>property</kbd> BasicEmbeddingsIndex.embedding_size





---

#### <kbd>property</kbd> BasicEmbeddingsIndex.embeddings





---

#### <kbd>property</kbd> BasicEmbeddingsIndex.embeddings_index







---

<a href="../../nemoguardrails/embeddings/basic.py#L73"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `BasicEmbeddingsIndex.add_item`

```python
add_item(item: nemoguardrails.embeddings.index.IndexItem)
```

Add a single item to the index.

---

<a href="../../nemoguardrails/embeddings/basic.py#L84"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `BasicEmbeddingsIndex.add_items`

```python
add_items(items: List[nemoguardrails.embeddings.index.IndexItem])
```

Add multiple items to the index at once.

---

<a href="../../nemoguardrails/embeddings/basic.py#L95"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `BasicEmbeddingsIndex.build`

```python
build()
```

Builds the Annoy index.

---

<a href="../../nemoguardrails/embeddings/basic.py#L102"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `BasicEmbeddingsIndex.search`

```python
search(
    text: str,
    max_results: int = 20
) → List[nemoguardrails.embeddings.index.IndexItem]
```

Search the closest `max_results` items.


---

<a href="../../nemoguardrails/embeddings/basic.py#L113"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `SentenceTransformerEmbeddingModel`
Embedding model using sentence-transformers.

<a href="../../nemoguardrails/embeddings/basic.py#L116"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `SentenceTransformerEmbeddingModel.__init__`

```python
__init__(embedding_model: str)
```








---

<a href="../../nemoguardrails/embeddings/basic.py#L124"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `SentenceTransformerEmbeddingModel.encode`

```python
encode(documents: List[str]) → List[List[float]]
```






---

<a href="../../nemoguardrails/embeddings/basic.py#L128"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `OpenAIEmbeddingModel`
Embedding model using OpenAI API.

<a href="../../nemoguardrails/embeddings/basic.py#L131"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `OpenAIEmbeddingModel.__init__`

```python
__init__(embedding_model: str)
```








---

<a href="../../nemoguardrails/embeddings/basic.py#L135"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `OpenAIEmbeddingModel.encode`

```python
encode(documents: List[str]) → List[List[float]]
```

Encode a list of documents into embeddings.
