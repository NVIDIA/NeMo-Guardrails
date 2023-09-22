# Flows

The core abstraction in the NeMo Guardrails toolkit is a **flow**.

## Todos

- References should belong to a Spec and not a SpecOp in order to support assigning references in action and flow groups
- Implement when/or/else construct for branching
- Implement match failing with the 'not' keyword, also for internal flow events
- Abort actions from flows that get aborted
- Add support to abort a flow (e.g. with 'abort $flow_ref' or 'send $flow_ref.Stop()')
- Implement pause/resume mechanism for activated flows
- Add support for 'return VALUE' to finish a flow and assign return value to a variable
- Add support to 'abort VALUE' a flow to fail it
- Access strings in objects using curly brackets

## Events

The following is the list of standard events:

- `UtteranceUserActionFinished(final_transcript)`: a new utterance from the user has been received.
- `UserIntent(intent)`: a canonical form for the user utterance has been identified.
- `BotIntent(intent)`: a new bot intent has been decided i.e. what it should say.
- `StartUtteranceBotAction(content)`: the utterance for a bot message has been decided.
- `StartInternalSystemAction(action_name, is_system_action, action_parameters)`: it has been decided that an action should be started.
- `InternalSystemActionFinished(action_name, action_parameters, action_result)`: an action has finished.
- `Listen`: there's nothing let to do and the bot should listen for new user input/events.
- `ContextUpdate`: the context data has been updated.

## Context Variables

The following is the list of standard context variables:

- `last_user_message`: the last utterance from the user.
- `last_bot_message`: the last utterance from the bot.
- `relevant_chunks`: the relevant chunks of text related to what the user said.

## Reasoning Loop

### Type of statements

- Non-blocking statements (sliding elements)
  - Flow logic (e.g. if/else, while, variable assignments, return, abort, ...)
- Blocking statements (matching elements)
  - Flow control (start, activate, stop, deactivate) -> under the hood firs all initial or stopping actions need to be executed ('start flow' is like 'send StartFlow' & 'match FlowStarted')
  - Actions: Send event (e.g. start action)
  - Decisions: Match event

- Pattern irrelevant statements (no conflicts)
  - Flow logic
  - Send internal events (start flow, stop flow, flow finished, ect)
  - Match statements (decisions)
- Pattern breaking relevant statements (potential conflicts)
  - Send UMIM events (actions)

### Internal events

- StartFlow
- FlowStarted
- FlowFinished
- FlowFailed
- FlowPaused
- FlowResumed

### Processing overview

- All heads are at matching statements
- Pop next external event
- Process event event:
  - Check head relevance
  - Determine match/mismatch for all relevant heads
    - Mark mismatching heads as `paused`
    - Mark matching heads as `matched` and assign a *matching score* and *processing group id*
  - Iteratively process all matching heads until they are at a ?blocking? statement
    - heads can advance, branch or merge for flow logic elements (keep track of head history)
    - can generate new internal events for flow control elements (e.g. StartFlow, FlowAdvanced, FlowFinished)
  - Pop next internal event and repeat with processing event until internal event queue is empty
    - Multiple matching statements for a event will create a head tree where decision statements can build branching points
  - All heads are now at decision statements
  - Resolve all conflicting action statements using the heads graph (with same *processing group id* and in same interaction loop)
    - Mark loosing heads as `aborted`
    - Generate `FlowAborted` internal events
  - Execute all action statements that are not aborted
  - Continue advancing heads and processing internal events until all heads are at a decision statement

### Processing details

**Start story**:

1. Flow heads are all at first statement (could be anything, since nameless flows don't need to start with a match statement)
2. (Assign individual processing-group ids to each head)
3. For each processing group:
   - Repeat **Process head statements** (sliding) for all non-blocking heads in group until all are blocking
   - **Resolve conflicts** from heads in `action_statement` list and repeat previous step if list is non empty

4. All heads are at a matching statement
5. Pop next event and assign process group id from internal event queue if not empty and **Process event**

**Process event**

1. For all flow heads check if event is relevant and than if it is matching or not.
   - Append all relevant mismatches to a `paused_flow` list (and push `FlowsPaused` event)
   - Append all relevant matches to a `matched_flows` list (and push `FlowsMatched` event)
2. Process `FlowsMatched`event

3. Check for all relevant heads if event matches or not

- For activated flows (head > 0): If not matching, mark flow as `Paused`, otherwise mark as `Matched`;

**Process head statements** (sliding):

Dependent on type:
    - Flow logic: Execute statement and advance/branch/merge head
    - Send event: Block and append to `action_statement` list
    - Match event: Block and append to `matching_statement` list

**Resolve conflicts**:

- Heads in same interaction loop with different statements
- Check heads history for highest earliest matching score
​

1. For all flow heads, if the event is relevant, determine if matching or not.

- For activated flows (head > 0): If not matching, mark flow as `Paused`, otherwise mark as `Matched`;
- Generate `FlowsPaused` event
- Generate `FlowsMatched` event
- [Optional] Process the `FlowsPaused` event (potentially other flows will be matching) - second `FlowsMatched` event

1. Process the `FlowsMatched` event: advance all the matching flows; Generate `FlowsStarted` and `FlowsAdvanced`/`FlowsFinished` events;

- a flow will advance until:
  - a) the end of the flow is reached -> `FlowsFinished`
  - b) a start action element is reached -> `StartAction`
  - c) a start flow is reached -> `StartFlow`
  - d) a match statement is reached.
- NOTE: no head should advance past a "StartAction"
​
NOTE: continue to process the internal event loop until it's empty.
​

3. Decide which actions will be started (resolve conflicts if any)

- Resolve conflicts and decide which actions get started
- Generate `InternalActionStarted` for the actions that should be started
- [Optional] Generate `FlowsInterrupted` if some flows can be interrupted on actions.
- Go back to step 2 until no more matching flows.

## Changes

- Adding interaction loop id and type to flow config
- Adding interaction loop id to flow state
- ?Extend flow heads to list to enable multiple heads per flow
- Every named flow will have as a first element the StartFlow event matcher
  - Flow states need to be initialized from flow configs before starting to process events
  - Nameless flows will immediately start (probably in a activated mode)
