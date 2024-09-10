.. _the-standard-library:

========================================
Colang Standard Library (CSL)
========================================

.. .. .. note::
.. ..     Feedbacks & TODOs:

.. ..     .. - CS: Add more explanation about in/out flow parameters

----------------------------------------
Introduction
----------------------------------------

The Colang Standard Library (CSL) provide an abstraction from the underlying event and action layer and offer a semantic interface to design interaction patterns between the bot and the user. Currently, there are the following library files available under ``nemoguardrails/colang/v2_x/library/`` (`Github link <../../../nemoguardrails/colang/v2_x/library>`_):

- ``core.co``: Fundamental core flows
- ``timing.co``: Timer dependent flows
- ``avatars.co``: Flows to handle multimodal interactive systems featuring an avatar interface
- ``llm.co``: LLM related core flows
- ``guardrails.co``: Guard-railing related flows
- ``utils.co``: Some useful helper and utility flows

To use the flows defined in these libraries you have two options:

1) Import the standard library files using the import statement: e.g. ``import llm``
2) Copy the corresponding `*.co` file directly inside your Colang script directory.

Note that the ``import <library>`` statement will import all available flows of the corresponding library.

------------------------------------------------------------------------------------------------------------------------------------------------------------------
Fundamental Core Flows (`core.co <../../../nemoguardrails/colang/v2_x/library/core.co>`_)
------------------------------------------------------------------------------------------------------------------------------------------------------------------

The core library that contains all relevant flows related to user and bot utterance events and actions.

**User Event Flows**

.. code-block:: colang

    # Wait for a user to have said given text
    flow user said $text -> $transcript

    # Wait for a user to have said something
    flow user said something -> $transcript

    # Wait for a user to say given text while talking
    flow user saying $text -> $transcript

    # Wait for any ongoing user utterance
    flow user saying something -> $transcript

    # Wait for start of user utterance
    flow user started saying something

    # Wait for a user to have said something unexpected (no active match statement)
    flow user said something unexpected -> $transcript

**Bot Action Flows**

.. code-block:: colang

    # Trigger a specific bot utterance
    flow bot say $text

    # Trigger the bot to inform about something (semantic 'bot say' wrapper)
    flow bot inform $text

    # Trigger the bot to ask something (semantic 'bot say' wrapper)
    flow bot ask $text

    # Trigger the bot to express something (semantic 'bot say' wrapper)
    flow bot express $text

    # Trigger the bot to respond with given text (semantic 'bot say' wrapper)
    flow bot respond $text

    # Trigger the bot to clarify something (semantic 'bot say' wrapper)
    flow bot clarify $text

    # Trigger the bot to suggest something (semantic 'bot say' wrapper)
    flow bot suggest $text

**Bot Event Flows**

.. code-block:: colang

    # Wait for the bot starting with the given utterance
    flow bot started saying $text

    # Wait for the bot starting with any utterance
    flow bot started saying something

    # Wait for the bot to finish saying given utterance
    flow bot said $text

    # Wait for the bot to finish with any utterance
    flow bot said something -> $text

    # Wait for the bot to finish informing about something
    flow bot informed something -> $text

    # Wait for the bot to finish asking about something
    flow bot asked something -> $text

    # Wait for the bot to finish expressing something
    flow bot expressed something -> $text

    # Wait for the bot to finish responding something
    flow bot responded something -> $text

    # Wait for the bot to finish clarifying something
    flow bot clarified something -> $text

    # Wait for the bot to finish suggesting something
    flow bot suggested something -> $text

**State Tracking Flows**

These are flows that track bot and user states in global variables.

.. code-block:: colang

    # Track bot talking state in global variable $bot_talking_state
    flow tracking bot talking state

    # Track user utterance state in global variables: $user_talking_state, $last_user_transcript
    flow tracking user talking state

**Development Helper Flows**

.. code-block:: colang

    # A flow to notify about any runtime Colang errors
    flow notification of colang errors

    # A flow to notify about the start of an undefined flow
    flow notification of undefined flow start

    # A flow to notify about an unhandled user utterance
    flow notification of unexpected user utterance


---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Timing Flows (`timing.co <../../../nemoguardrails/colang/v2_x/library/timing.co>`_)
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


.. code-block:: colang

    # Little helper flow to wait indefinitely
    flow wait indefinitely

    # Wait the specified number of seconds before continuing
    flow wait $time_s $timer_id="wait_timer_{uid()}"

    # Start a repeating timer
    flow repeating timer $timer_id $interval_s

    # Wait for when user was silent for $time_s seconds
    flow user was silent $time_s

    # Wait for when user was silent for $time_s seconds while bot was silent
    flow user didnt respond $time_s

    # Wait for the bot to be silent (no utterance) for given time
    flow bot was silent $time_s

    # Trigger a specific bot gesture delayed
    flow bot gesture with delay $gesture $delay


---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Interactive Avatar Modality Flows (`avatars.co <../../../nemoguardrails/colang/v2_x/library/avatars.co>`_)
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**User Event Flows**

.. code-block:: colang

    # Wait for a UI selection
    flow user selected choice $choice_id -> $choice

    # Wait for a UI selection to have happened (considering also choices that happened right before)
    flow user has selected choice $choice_id

    # Wait for user entering keystrokes in UI text field
    flow user typing $text -> $inputs

    # Wait for user to make a gesture
    flow user gestured $gesture -> $final_gesture

    # Wait for user to be detected as present (e.g. camera ROI)
    flow user became present -> $user_id

    # Wait for when the user talked while bot is speaking
    flow user interrupted bot talking $sentence_length=15


**Bot Action Flows**

.. code-block:: colang

    # Trigger a specific bot gesture
    flow bot gesture $gesture

    # Trigger a specific bot posture
    flow bot posture $posture

    # Show a 2D UI with some options to select from
    flow scene show choice $prompt $options

    # Show a 2D UI with detailed information
    flow scene show textual information $title $text $header_image

    # Show a 2D UI with a short information
    flow scene show short information $info

    # Show a 2D UI with some input fields to be filled in
    flow scene show form $prompt $inputs

**Bot Event Flows**

.. code-block:: colang

    # Wait for the bot to start with the given gesture
    flow bot started gesture $gesture

    # Wait for the bot to start with any gesture
    flow bot started a gesture -> $gesture

    # Wait for the bot to start with the given posture
    flow bot started posture $posture

    # Wait for the bot to start with any posture
    flow bot started a posture -> $posture

    # Wait for the bot to start with any action
    flow bot started an action -> $action

**State Tracking Flows**

These are flows that track bot and user states in global variables.

.. code-block:: colang

    # Track most recent visual choice selection state in global variable $choice_selection_state
    flow tracking visual choice selection state

**Helper & Utility Flows**

These are some useful helper and utility flows:

.. code-block:: colang

    # Stops all the current bot actions
    flow finish all bot actions

    # Stops all the current scene actions
    flow finish all scene actions

    # Handling the bot talking interruption reaction
    flow handling bot talking interruption $mode="inform"

**Posture Management Flows**

.. code-block:: colang

    # Activates all the posture management
    flow managing bot postures

    # Start and stop listening posture
    flow managing listening posture

    # Start and stop talking posture
    flow managing talking posture

    # Start and stop thinking posture
    flow managing thinking posture

    # Start and stop idle posture
    flow managing idle posture

------------------------------------------------------------------------------------------------------------------------------------------------------------------
LLM Flows (`llm.co <../../../nemoguardrails/colang/v2_x/library/llm.co>`_)
------------------------------------------------------------------------------------------------------------------------------------------------------------------

**LLM Enabled Bot Actions**

.. code-block:: colang

    # Trigger a bot utterance similar to given text
    flow bot say something like $text

**LLM Utilities**

.. code-block:: colang

    # Start response polling for all LLM related calls to receive the LLM responses an act on that
    flow polling llm request response $interval=1.0

**Interaction Continuation**

Flows to that will continue the current interaction for unhandled user actions/intents or undefined flows.

.. code-block:: colang

    # Activate all LLM based interaction continuations
    flow llm continuation

    # Generate a user intent event (finish flow event) for unhandled user utterance
    flow generating user intent for unhandled user utterance

    # Wait for the end of any flow with the name starting with 'user ' (considered a user intent)
    flow unhandled user intent -> $intent

    # Generate and start new flow to continue the interaction for an unhandled user intent
    flow continuation on unhandled user intent

    # Generate and start a new flow to continue the interaction for the start of an undefined flow
    flow continuation on undefined flow

    # Generate a flow that continues the current interaction
    flow llm generate interaction continuation flow -> $flow_name

    # Generate and continue with a suitable interaction
    flow llm continue interaction

**Interaction History Logging**

Flows to log interaction history to created required context for LLM prompts.

.. code-block:: colang

    # Activate all automated user and bot intent flows logging based on flow naming
    flow automating bot user intent logging

    # Marking user intent flows using only naming convention
    flow marking user intent flows

    # Generate user intent logging for marked flows that finish by themselves
    flow logging marked user intent flows

    # Marking bot intent flows using only naming convention
    flow marking bot intent flows

    # Generate user intent logging for marked flows that finish by themselves
    flow logging marked bot intent flows

**State Tracking Flows**

These are flows that track bot and user states in global variables.

.. code-block:: colang

    # Track most recent unhandled user intent state in global variable $user_intent_state
    flow tracking unhandled user intent state

------------------------------------------------------------------------------------------------------------------------------------------------------------------
Guardrail Flows (`guardrails.co <../../../nemoguardrails/colang/v2_x/library/guardrails.co>`_)
------------------------------------------------------------------------------------------------------------------------------------------------------------------

Flows to guardrail user inputs and LLM responses.

.. code-block:: colang

    # Check user utterances before they get further processed
    flow run input rails $input_text

    # Check llm responses before they get further processed
    flow run output rails $output_text

------------------------------------------------------------------------------------------------------------------------------------------------------------------
Utility Flows (`utils.co <../../../nemoguardrails/colang/v2_x/library/utils.co>`_)
------------------------------------------------------------------------------------------------------------------------------------------------------------------

Some useful common helper and utility flows.

.. code-block:: colang

    # Start a flow with the provided name and wait for it to finish
    flow await_flow_by_name $flow_name
