from nemoguardrails.llm.providers import register_llm_provider
import sys
 
# adding current to the system path
sys.path.append('/workspace/NeMo-Guardrails/nemoguardrails/examples/hf_mosaic')
#from .dolly import HFDollyLLM

from typing import Optional

from langchain.base_language import BaseLanguageModel
from langchain import HuggingFacePipeline
from langchain.llms.base import LLM
import transformers
from transformers import AutoTokenizer
import torch
from transformers import pipeline

# below class is inspired from https://github.com/databrickslabs/dolly/blob/master/examples/langchain.py#L57
class HFMosaicLLM(LLM):
    """A HuggingFace LLM."""
    llm: Optional[BaseLanguageModel] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        name = 'mosaicml/mpt-7b-instruct'

        config = transformers.AutoConfig.from_pretrained(name, trust_remote_code=True)
        config.init_device = 'cuda:0' # For fast initialization directly on GPU!
        tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")

        model = transformers.AutoModelForCausalLM.from_pretrained(
          name,
          config=config,
          torch_dtype=torch.bfloat16, # Load model weights in bfloat16
          trust_remote_code=True
        )

        pipe = pipeline('text-generation', model=model, tokenizer=tokenizer, device='cuda:0',max_new_tokens=200,do_sample=True,use_cache=True)

        self.llm=HuggingFacePipeline(pipeline=pipe)

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "hf_mosaic"

    def _call(self, prompt, stop, run_manager) -> str:
        return self.llm._call(prompt, stop, run_manager)

    async def _acall(self, prompt, stop, run_manager) -> str:
        return await self.llm._acall(prompt, stop, run_manager)


register_llm_provider("hf_mosaic", HFMosaicLLM)