<!--
# Copyright 2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-->

## Before you Proceed
For an overview of grounding methods including fact-checking and hallucination detection, kindly read the [grounding rails](../grounding_rail/README.md) example first. 

Here, we will focus on how you can plug in custom fact-checking solutions, and we'll use the [AlignScore](https://aclanthology.org/2023.acl-long.634.pdf) model from the academic community to demonstrate it.

# Custom Fact Checking
This example includes the following items

- `kb/` - A folder containing our knowledge base to retrieve context from and fact check against. In this case, we include the March 2023 US Jobs report in `kb/report.md`.
- `alignscore_applet.py` - A python file containing code to deploy our recommended custom fact-checking method through Flask.
- `config.yml` - A config file defining the Large Language Model used.
- `general.co` - A colang file with some generic examples of colang `flows` and `messages`
- `factcheck.co` - A colang file demonstrating one way of implementing a Fact Checking rail using the `check_facts` action.

The fact checking rail enables you to check the validity of the bot response based on a knowledge base. When the bot provides its answer, we execute the `check_facts` action and store the response in the `accuracy` variable. The `check_facts` action is a wrapper function that can under the hood rely on any method that takes in two input texts, an evidence and a claim, and produces a score between 0.0 and 1.0 signifying how supported the claim is based on the evidence. In our case, the evidence is formed from the retrieved relevant chunks from the knowledge base, while the claim our chatbot's response to the user's query.

Note that the `config.yml` file can be updated as follows to specify a provider for our custom fact-checking solution.
```colang
custom_data:
  fact_checking:
    provider: custom  # the default is ask_llm
    parameters:
      ...
```
For building a new custom fact-checking solution, we are required to add a function and update the [`check_facts` wrapper](../../nemoguardrails/actions/fact_checking/fact_checking.py) to appropriately to invoke the new function.

## Examplar Custom Solution: AlignScore
Our toolkit provides support for the [AlignScore metric (Zha et al.)](https://aclanthology.org/2023.acl-long.634.pdf), which uses a RoBERTa-based model for scoring factual consistency in model responses with respect to the knowledge base.

In our testing, we observed an average latency of ~220ms on hosting AlignScore as a RESTful service, and ~45ms on direct inference with the model loaded in-memory. This makes it much faster than the `ask_llm` method. We also observe substantial improvements in accuracy over the `ask_llm` method, with a balanced performance on both factual and counterfactual statements. 

In order to use AlignScore, the `config.yml` file can be updated as follows:
```colang
custom_data:
  fact_checking:
    provider: align_score  # the default is ask_llm
    parameters:
      endpoint: "http://localhost:5000/alignscore_large"
```

Note that this method requires an on-prem deployment of the publicly available model. Please see the [AlignScore Deployment](#alignscore-deployment) section.

Since this method gives a continuous score between 0 and 1 (as compared to the binary classification among 0 or 1 using the `ask_llm` method), it also allows more fine-grained control of the Colang flow.


### AlignScore Deployment
In order to use AlignScore, follow these steps:
```bash
git clone https://github.com/yuh-zha/AlignScore.git
cd AlignScore
pip install .
python -m spacy download en_core_web_sm
wget https://huggingface.co/yzha/AlignScore/resolve/main/AlignScore-base.ckpt
wget https://huggingface.co/yzha/AlignScore/resolve/main/AlignScore-large.ckpt
```
With the above simple setup, we can load the model in-memory and perform inference on it as follows:
```python
model = AlignScore(model='roberta-large', batch_size=32, device='cuda:0', ckpt_path='path/to/downloaded/AlignScore-large.ckpt', evaluation_mode='nli_sp')
alignscore = model.score(contexts=["This is a piece of evidence"], claims=["This is a claim being tested against the evidence"])[0]
```
We've also provided an `alignscore_applet.py` file that you can copy over to your top-level AlignScore directory to run it as a simple Flask app.
```bash
cp nemoguardrails/nemoguardrails/examples/fact_checking/alignscore_applet.py /path/to/AlignScore/alignscore_applet.py
flask --app alignscore_applet run --host=0.0.0.0 --port=5000
```

## Try it yourself

With a basic understanding of building the rails, the next step is to try out the bot and customize it! You can continue to interact with the bot via the API, or use the `nemoguardrails` CLI to launch an interactive command line or web chat interface. Customize your bot by adding in new flows or documents to the knowledge base, and test out the effects of adding and removing the rails explored in this notebook and others.

Refer [Python API Documentation](../../docs/user_guide/interface-guide.md#python-api) for more information.

### UI

Guardrails allows users to interact with the server with a stock UI. To launch the
server and access the UI to interact with this example, the following steps are
recommended:

* Launch the server with the command: `nemoguardrails server`
* Once the server is launched, you can go to: `http://localhost:8000` to access
the UI
* Click "New Chat" on the top left corner of the screen and then proceed to
pick `grounding_rail` from the drop-down menu.

Refer [Guardrails Server Documentation](../../docs/user_guide/interface-guide.md#guardrails-server) for more information.

### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder:

```bash
nemoguardrails chat --config=.
```
Refer [Guardrails CLI Documentation](../../docs/user_guide/interface-guide.md#guardrails-cli) for more information.

* [Explore more examples](../README.md#examples) to help steer your bot!
