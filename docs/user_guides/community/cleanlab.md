# Cleanlab Integration

The `cleanlab trustworthiness` flow uses trustworthiness score with a default threshold of 0.6 to determine if the output should be allowed or not (i.e., if the trustworthiness score is below the threshold, the response is considered "untrustworthy").

A high trustworthiness score generally correlates with high-quality responses. In a question-answering application, high trustworthiness is indicative of correct responses, while in general open-ended applications, a high score corresponds to the response being helpful and informative. Trustworthiness scores are less useful for creative or open-ended requests.

The mathematical derivation of the score is explained in [Cleanlab's documentation](https://help.cleanlab.ai/tutorials/tlm/#how-does-the-tlm-trustworthiness-score-work), and you can also access [trustworthiness score benchmarks](https://cleanlab.ai/blog/trustworthy-language-model/).

You can easily change the cutoff value for the trustworthiness score by adjusting the threshold in the [config](https://github.com/NVIDIA/NeMo-Guardrails/tree/develop/nemoguardrails/library/cleanlab/flows.co). For example, to change the threshold to 0.7, you can add the following flow to your config:

```colang
define subflow cleanlab trustworthiness
  """Guardrail based on trustworthiness score."""
  $result = execute call cleanlab api

  if $result.trustworthiness_score < 0.7
    bot response untrustworthy
    stop

define bot response untrustworthy
  "Don't place much confidence in this response"
```

## Setup

Install `cleanlab-studio` to use Cleanlab's trustworthiness score:

```
pip install cleanlab-studio
```

Then, you can get an API key for free by [creating a Cleanlab account](https://app.cleanlab.ai/?signup_origin=TLM) or experiment with TLM in the [playground](https://tlm.cleanlab.ai/). You can also [email Cleanlab](mailto:sales@cleanlab.ai) for any special requests or support.

Lastly, set the `CLEANLAB_API_KEY` environment variable with the API key.
