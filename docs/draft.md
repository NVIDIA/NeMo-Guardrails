# Types of Rails

Guardrails (or rails for short) are implemented through **flows**. Depending on their role, rails can be split into:

1. Input rails: triggered when a new input from the user is received.
2. Output rails: triggered when a new output should be sent to the user.
3. Topical rails: triggered after a user message is interpreted, i.e., a canonical form has been identified.
4. Retrieval rails: triggered after the retrieval step has been performed, i.e., the `retrieve_relevant_chunks` action has finished.

## Input Rails

Input rails process the message from the user. For example:

```colang
define flow some input rail
  $allowed = execute check_jailbreak

  if not $allowed
    bot inform cannot answer
    stop
```

Input rails can alter the input by changing the `$user_message` context variable.

## Output Rails

Output rails process a bot message. The message to be processed is available in the context variable `$bot_message`. Output rails can alter the `$bot_message` variable, e.g., to mask sensitive information.

## Retrieval Rails

Retrieval rails process the retrieved chunks, i.e., the `$relevant_chunks` variable.


NOTE: this section will be moved in a different place when the documentation is reviewed.

## 3rd Party Rails

### Active Fence

NeMo Guardrails supports using the [ActiveFence ActiveScore API](https://docs.activefence.com/index.html) as an input rail out-of-the-box (you need to have the `ACTIVE_FENCE_API_KEY` environment variable set).

```yaml
rails:
  input:
    flows:
      # The simplified version
      - active fence moderation

      # The detailed version with individual risk scores
      # - active fence moderation detailed
```

The `active fence moderation` flow uses the maximum risk score with the 0.7 threshold to decide if the input should be allowed or not (i.e., if the risk score is above the threshold, it is considered a violation). The `active fence moderation detailed` has individual scores per category of violations.

To customize the scores, you have to overwrite the [default flows](../nemoguardrails/library/active_fence/flows.co) in your config. For example, to change the threshold for `active fence moderation` you can add the following flow to your config:

```colang
define subflow active fence moderation
  """Guardrail based on the maximum risk score."""
  $result = execute call active fence api

  if $result.max_risk_score > 0.9
    bot inform cannot answer
    stop
```
