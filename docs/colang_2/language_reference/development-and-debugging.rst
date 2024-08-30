.. _development-and-debugging:

========================================
Development and Debugging
========================================

.. .. note::
..     Feedbacks & TODOs:

Currently, the Colang story designing and building environment is fairly limited but will be improved on in the future.

-----------------------------------------
Integrated Development Environment (IDE)
-----------------------------------------

- We suggest using `Visual Studio Code <https://code.visualstudio.com/>`_ and the Colang highlighting extension (`Github link <https://github.com/NVIDIA/NeMo-Guardrails/tree/main/vscode_extension>`_) to help with highlighting Colang code.
- You can use the Visual Studio Code launch setting to run a Colang story with nemoguardrails in a python environment by pressing F5 (`launch.json <https://github.com/NVIDIA/NeMo-Guardrails/blob/main/.vscode/launch.json>`_)
- You can show generated and received events by adding the ``--verbose`` flag when starting nemoguardrails, that will also show all generated LLM prompts and responses
- To see even more details and show the internal run-time logs use ``--debug-level=INFO`` or set it equal to ``DEBUG``

-------------------------
Log and Print Statements
-------------------------

To help debugging your Colang flows you can use the print statement ``print <expression>`` to print something to the standard output.

.. code-block:: colang
    :caption: development_debugging/print_statement/main.co

    flow main
        user said something as $flow
        print $flow.transcript

.. code-block:: text

    > Hi

    Hi

Alternatively, use the log statement ``log <expression>`` to append to the logging shown in the verbose mode, which will appear as "Colang Log <flow_instance_uid> :: <expression>".

Furthermore, the Colang function ``flows_info`` can be used to return more information about a flow instance:

.. code-block:: colang
    :caption: development_debugging/flows_info/main.co

    flow main
        await a
        match RestartEvent()

    flow a
        $info = flows_info($self.uid)
        print pretty_str($info)


.. code-block:: json

    {
        "flow_instance_uid": "(a)2c62...",
        "flow_id": "a",
        "loop_id": "(main)8f3d...",
        "status": "starting",
        "flow_hierarchy": [
            "(main)8170..."
        ],
        "active_statement_at_lines": [
            6
        ],
        "meta_tags": []
    }

Where ``pretty_str`` converts the returned dictionary object to a nicely formatted string. If no parameter is provided to the function it will return a dictionary containing all the currently active flow instances.

-------------------------
CLI Debugging Commands
-------------------------

The NeMo Guardrail CLI provides a couple of additional debugging commands that always start with the ``!`` character, e.g.:

.. code-block:: text

    > !list-flows
    ┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ ID ┃ Flow Name                                 ┃ Loop                            ┃ Flow Instances          ┃ Source                          ┃
    ┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ 1  │ tracking visual choice selection state    │ named ('state_tracking')        │ 924ad                   │ /colang/v2_x/library/avatars.co │
    │ 2  │ tracking bot talking state                │ named ('state_tracking')        │ 28804                   │ /colang/v2_x/library/core.co    │
    │ 3  │ wait                                      │ new                             │ 9e18b                   │ /colang/v2_x/library/timing.co  │
    │ 4  │ user was silent                           │ named ('user_was_silent')       │ c1dfd                   │ /colang/v2_x/library/timing.co  │
    │ 5  │ polling llm request response              │ named ('llm_response_polling')  │ a003b                   │ /colang/v2_x/library/llm.co     │
    │ 6  │ continuation on unhandled user utterance  │ parent                          │ 342c6                   │ /colang/v2_x/library/llm.co     │
    │ 7  │ automating intent detection               │ parent                          │ c5c0a                   │ /colang/v2_x/library/llm.co     │
    │ 8  │ marking user intent flows                 │ named ('intent_log')            │ ad2b4                   │ /colang/v2_x/library/llm.co     │
    │ 9  │ logging marked user intent flows          │ named ('intent_log')            │ a5dd9                   │ /colang/v2_x/library/llm.co     │
    │ 10 │ marking bot intent flows                  │ named ('intent_log')            │ 8873e                   │ /colang/v2_x/library/llm.co     │
    │ 11 │ logging marked bot intent flows           │ named ('intent_log')            │ 3d331                   │ /colang/v2_x/library/llm.co     │
    │ 12 │ user has selected choice                  │ parent                          │ 78b3b,783b6,c4186,cd667 │ /colang/v2_x/library/avatars.co │
    │ 13 │ user interrupted bot talking              │ parent                          │ 6e576                   │ /colang/v2_x/library/avatars.co │
    │ 14 │ bot posture                               │ parent                          │ d9f32                   │ /colang/v2_x/library/avatars.co │
    │ 15 │ handling bot talking interruption         │ named ('bot_interruption')      │ 625f1                   │ /colang/v2_x/library/avatars.co │
    │ 16 │ managing idle posture                     │ named ('managing_idle_posture') │ 0bfe3                   │ /colang/v2_x/library/avatars.co │
    │ 17 │ _user_said                                │ parent                          │ db5e4,d2cb3,b7b85,095e0 │ /colang/v2_x/library/core.co    │
    │ 18 │ _user_said_something_unexpected           │ parent                          │ cb676                   │ /colang/v2_x/library/core.co    │
    │ 19 │ user said                                 │ parent                          │ c4a05,45f2c,cd4ab,fecc2 │ /colang/v2_x/library/core.co    │
    │ 20 │ bot started saying something              │ parent                          │ fc2a7,8d5f1             │ /colang/v2_x/library/core.co    │
    │ 21 │ notification of colang errors             │ named ('colang_errors_warning') │ cd5a8                   │ /colang/v2_x/library/core.co    │
    │ 22 │ notification of undefined flow start      │ parent                          │ 20d10                   │ /colang/v2_x/library/core.co    │
    │ 23 │ wait indefinitely                         │ parent                          │ 3713b                   │ /colang/v2_x/library/core.co    │
    └────┴───────────────────────────────────────────┴─────────────────────────────────┴─────────────────────────┴─────────────────────────────────┘

.. code-block:: colang
    :caption: All CLI debugging commands

    list-flows [--all] [--order_by_name] # Shows all active flows in a table in order of their interaction loop priority and name
    tree # Shows the flow hierarchy tree of all active flows

-------------
Useful Flows
-------------

In the Colang Standard Library there are a couple of helpful flows that help in the development process of a Colang story:

**notification of undefined flow start**.
Sometimes it is easy to misspell a flow name. By default Colang will just generate a ``StartFlow(flow_id=<name_of_flow>)`` internal event. But if no flow with that name exists, nothing will happen. This can be confusing and difficult to find. To get help with that you can activate the flow ``notification of undefined flow start`` which will detect these cases and print and log a corresponding message and optionally lets the bot respond.

**notification of unexpected user utterance**.
This flow helps you to detect if certain ``UtteranceUserAction.Finished()`` events are not matched to and therefore will create no bot response, which is probably almost never the case.

**notification of colang errors**.
When running a Colang story there can be runtime errors due to invalid attribute access or LLM related parsing errors. This error will generate a ``ColangError(error_type: str, error: str)`` event. Usually nothing will match to this event and the bot will remain silent. While debugging a this can be confusing and the flow ``notification of colang errors`` from the standard library will help make this more transparent by printing and logging a corresponding message and optionally letting the bot respond.
