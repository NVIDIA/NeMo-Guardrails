<!-- markdownlint-disable -->

<a href="../../nemoguardrails/embeddings/index.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

# <kbd>module</kbd> `nemoguardrails.embeddings.index`






---

<a href="../../nemoguardrails/embeddings/index.py#L20"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `IndexItem`
IndexItem(text: str, meta: Dict = <factory>)

<a href="../../scripts/<string>"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `IndexItem.__init__`

```python
__init__(text: str, meta: Dict = <factory>) → None
```









---

<a href="../../nemoguardrails/embeddings/index.py#L26"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `EmbeddingsIndex`
The embeddings index is responsible for computing and searching a set of embeddings.


---

#### <kbd>property</kbd> EmbeddingsIndex.embedding_size







---

<a href="../../nemoguardrails/embeddings/index.py#L33"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `EmbeddingsIndex.add_item`

```python
add_item(item: nemoguardrails.embeddings.index.IndexItem)
```

Adds a new item to the index.

---

<a href="../../nemoguardrails/embeddings/index.py#L37"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `EmbeddingsIndex.add_items`

```python
add_items(items: List[nemoguardrails.embeddings.index.IndexItem])
```

Adds multiple items to the index.

---

<a href="../../nemoguardrails/embeddings/index.py#L41"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `EmbeddingsIndex.build`

```python
build()
```

Build the index, after the items are added.

This is optional, might not be needed for all implementations.

---

<a href="../../nemoguardrails/embeddings/index.py#L47"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `EmbeddingsIndex.search`

```python
search(
    text: str,
    max_results: int
) → List[nemoguardrails.embeddings.index.IndexItem]
```

Searches the index for the closes matches to the provided text.


---

<a href="../../nemoguardrails/embeddings/index.py#L52"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `EmbeddingModel`
The embedding model is responsible for creating the embeddings.




---

<a href="../../nemoguardrails/embeddings/index.py#L55"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `EmbeddingModel.encode`

```python
encode(documents: List[str]) → List[List[float]]
```

Encode the provided documents into embeddings.
