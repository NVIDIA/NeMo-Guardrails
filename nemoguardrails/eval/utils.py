import json

from nemoguardrails.llm.providers import get_llm_provider, get_llm_provider_names
from nemoguardrails.rails.llm.config import Model

def initialize_llm(model_config: Model):
        """Initializes the model from LLM provider."""
        if model_config.engine not in get_llm_provider_names():
            raise Exception(f"Unknown LLM engine: {model_config.engine}")
        provider_cls = get_llm_provider(model_config)
        kwargs = {"temperature": 0, "max_tokens": 10}
        if model_config.engine in [
            "azure",
            "openai",
            "gooseai",
            "nlpcloud",
            "petals",
        ]:
            kwargs["model_name"] = model_config.model
        else:
            kwargs["model"] = model_config.model
        return provider_cls(**kwargs)

def load_dataset(dataset_path: str):
    """Loads a dataset from a file."""
    
    with open(dataset_path, "r") as f:
        if dataset_path.endswith(".json"):
            dataset = json.load(f)
        else:
            dataset = f.readlines()

    return dataset