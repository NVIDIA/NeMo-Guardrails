import os

import pytest

from nemoguardrails import LLMRails, RailsConfig

try:
    from nemoguardrails.embeddings.embedding_providers.cohere import (
        CohereEmbeddingModel,
    )
except ImportError:
    # Ignore this if running in test environment when cohere not installed.
    CohereEmbeddingModel = None

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), ".", "test_configs")

LIVE_TEST_MODE = os.environ.get("LIVE_TEST")

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set level to DEBUG to see all messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Set level to DEBUG to see all messages
logger.addHandler(console_handler)


@pytest.fixture
def app():
    """Load the configuration where we replace FastEmbed with Cohere."""
    config = RailsConfig.from_path(
        os.path.join(CONFIGS_FOLDER, "with_cohere_embeddings")
    )

    return LLMRails(config, verbose=True)


@pytest.mark.skipif(not LIVE_TEST_MODE, reason="Not in live mode.")
def test_custom_llm_registration(app):
    assert isinstance(
        app.llm_generation_actions.flows_index._model, CohereEmbeddingModel
    )


@pytest.mark.skipif(not LIVE_TEST_MODE, reason="Not in live mode.")
@pytest.mark.asyncio
async def test_live_query_async():
    config = RailsConfig.from_path(
        os.path.join(CONFIGS_FOLDER, "with_cohere_embeddings")
    )
    app = LLMRails(config, verbose=True)

    result = await app.generate_async(
        messages=[{"role": "user", "content": "tell me what you can do"}]
    )

    assert result == {
        "role": "assistant",
        "content": "I am an AI assistant that helps answer questions.",
    }


@pytest.mark.skipif(not LIVE_TEST_MODE, reason="Not in live mode.")
def test_live_query(app):
    result = app.generate(
        messages=[{"role": "user", "content": "tell me what you can do"}]
    )

    assert result == {
        "role": "assistant",
        "content": "I am an AI assistant that helps answer questions.",
    }


@pytest.mark.skipif(not LIVE_TEST_MODE, reason="Not in live mode.")
def test_sync_embeddings():
    model = CohereEmbeddingModel("embed-english-light-v3.0")

    result = model.encode(["test"])

    assert len(result[0]) == 384


@pytest.mark.skipif(not LIVE_TEST_MODE, reason="Not in live mode.")
@pytest.mark.asyncio
async def test_async_embeddings():
    model = CohereEmbeddingModel("embed-english-v3.0")

    result = await model.encode_async(["test"])

    assert len(result[0]) == 1024
