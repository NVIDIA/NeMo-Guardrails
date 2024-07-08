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

Alternatively, use the log statement ``log <expression>`` to append to the logging shown in the verbose mode, which will appear as "Colang debug info: <expression>".

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
