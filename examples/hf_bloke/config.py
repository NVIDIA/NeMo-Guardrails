from nemoguardrails.llm.providers import register_llm_provider
import sys
 
# adding current to the system path
sys.path.append('/workspace/NeMo-Guardrails/nemoguardrails/examples/hf_bloke')
#from .dolly import HFDollyLLM

from typing import Optional

from langchain.base_language import BaseLanguageModel
from langchain import HuggingFacePipeline
from langchain.llms.base import LLM
import transformers
import torch
from transformers import LlamaForCausalLM, GenerationConfig, pipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, LlamaTokenizer, AutoModel
from transformers import AutoConfig, AutoModelForCausalLM


def load_model(model_name, device, num_gpus, load_8bit=False, debug=False):
    if device == "cpu":
        kwargs = {}
    elif device == "cuda":
        kwargs = {"torch_dtype": torch.float16}
        if num_gpus == "auto":
            kwargs["device_map"] = "auto"
        else:
            num_gpus = int(num_gpus)
            if num_gpus != 1:
                kwargs.update({
                    "device_map": "auto",
                    "max_memory": {i: "13GiB" for i in range(num_gpus)},
                })
    elif device == "mps":
        kwargs = {"torch_dtype": torch.float16}
        # Avoid bugs in mps backend by not using in-place operations.
        print("mps not supported")
    else:
        raise ValueError(f"Invalid device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(model_name,
        low_cpu_mem_usage=True, **kwargs)

    
    if (device == "cuda" and num_gpus == 1) :
        model.to(device)

    if debug:
        print(model)

    return model, tokenizer

class HFBlokeLLM(LLM):
    """A HuggingFace LLM."""
    llm: Optional[BaseLanguageModel] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        model_name='/workspace/ckpt/bloke/' # loading model ckpt from disk
        device='cuda'
        num_gpus=2 # making sure GPU-GPU are NVlinked, GPUs-GPUS with NVSwitch
        model, tokenizer=load_model(model_name, device, num_gpus, debug=False)

        #repo_id="TheBloke/Wizard-Vicuna-13B-Uncensored-HF"
        #pipe = pipeline("text-generation", model=repo_id, device_map={"":"cuda:0"}, max_new_tokens=256, temperature=0.1, do_sample=True,use_cache=True)
        pipe = pipeline(
            "text-generation",
            model=model, 
            tokenizer=tokenizer, 
            max_new_tokens=256,
            temperature=0.1,
            do_sample=True,)
        self.llm=HuggingFacePipeline(pipeline=pipe)

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "hf_bloke"

    def _call(self, prompt, stop, run_manager) -> str:
        return self.llm._call(prompt, stop, run_manager)

    async def _acall(self, prompt, stop, run_manager) -> str:
        return await self.llm._acall(prompt, stop, run_manager)


register_llm_provider("hf_bloke", HFBlokeLLM)