import logging
from typing import Any, List
import os
import cohere
from tenacity import retry, stop_after_attempt, wait_fixed, before_sleep_log

from . import EmbeddingModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CohereEmbeddingModel(EmbeddingModel):
    """Embedding model using Cohere API.

    Args:
        embedding_model (str): The name of the embedding model.

    Attributes:
        model (str): The name of the embedding model.
        embedding_size (int): The size of the embeddings.

    Methods:
        encode: Encode a list of documents into embeddings.
    """

    def __init__(
            self,
            embedding_model: str,
    ):
        self.model = embedding_model
        self.truncate = "NONE"

        self.co_api_key = os.environ.get("COHERE_API_KEY")
        if not self.co_api_key:
            raise Exception("`COHERE_API_KEY` not provided")

        self.client = None # shared client causes event loop closed error
        self.async_client = None # shared client causes event loop closed error

        self.embedding_size_dict = {
            "embed-english-v3.0": 1024,
            "embed-english-light-v3.0": 384,
            "embed-multilingual-v3.0": 1024,
            "embed-multilingual-light-v3.0": 384
        }

        if self.model in self.embedding_size_dict:
            self.embedding_size = self.embedding_size_dict[self.model]
        else:
            # Perform a first encoding to get the embedding size
            self.embedding_size = len(self.encode(["test"])[0])

    def encode(self, documents: List[str]) -> List[List[float]]:
        """Encode a list of documents into embeddings.

        Args:
            documents (List[str]): The list of documents to be encoded.

        Returns:
            List[List[float]]: The encoded embeddings.

        """
        embeddings = self.embed_with_retry(
            model=self.model,
            texts=documents,
            truncate=self.truncate,
            # https://docs.cohere.com/docs/embed-api#the-input_type-parameter
            input_type="search_document"
        ).embeddings
        return [list(map(float, e)) for e in embeddings]

    async def encode_async(self, documents: List[str]) -> List[List[float]]:
        """Encode a list of documents into embeddings.

        Args:
            documents (List[str]): The list of documents to be encoded.

        Returns:
            List[List[float]]: The encoded embeddings.

        """
        embeddings = (
            await self.aembed_with_retry(
                model=self.model,
                texts=documents,
                truncate=self.truncate,
                # https://docs.cohere.com/docs/embed-api#the-input_type-parameter
                input_type="search_document"
            )
        ).embeddings
        return [list(map(float, e)) for e in embeddings]

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), before_sleep=before_sleep_log(logger, logging.WARNING))
    def embed_with_retry(self, **kwargs:Any) -> Any:
        self.client = cohere.Client(self.co_api_key)
        return self.client.embed(**kwargs)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), before_sleep=before_sleep_log(logger, logging.WARNING))
    async def aembed_with_retry(self, **kwargs: Any) -> Any:
        self.async_client = cohere.AsyncClient(self.co_api_key)
        return await self.async_client.embed(**kwargs)


