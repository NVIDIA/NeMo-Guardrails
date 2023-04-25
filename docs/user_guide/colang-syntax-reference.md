# Colang Language Reference

This document provides a reference for the keywords and statements supported by Colang.

### Keywords Reference

- `bot`: used both when defining a bot message (`define bot ...`) and when using in a flow (`bot ...`)
- `break`: break out of a while loop;
- `continue`: continue to the next iteration of a `while` loop; outside of a loop is similar to `pass` in python;
- `create`: create a new event;
- `define`: used in defining user/bot messages and flows;
- `else`: for `if` and `when` blocks;
- `execute`: for executing actions;
- `event`: for matching an event;
- `flow`: used in defining a flow (`define flow`)
- `goto`: go to the specified label;
- `if`: used in typical `if` block;
- `include`: used to include another `rails` configuration;
- `label`: mark a label in a flow;
- `meta`: provide meta information about a flow;
- `priority`: set the priority of a flow
- `return`: end the current flow;
- `set`: set the content of a context variable;
- `user`: used both when defining a user message (`define user ...`) and when using in a flow (`user ...`)
- `while`: typical `while` loop, similar to python;
- `when`: branching based on the stream of events.

### Statements

#### Simple Statements

A simple statement is comprised within a single logical line.

- `bot`: the bot said something.
- `break`: break the current while loop.
- `continue`: goes again to the beginning of the current loop; if no loop, it has no effect.
- `return`: ends the current flow.
- `execute`: executes an action.
- `event`: an event has occurred.
- `goto`: go to a specific label.
- `include`: include another rails configuration.
- `label`: define a label.
- `meta`: define meta information for a flow.
- `set`: set the value of a context variable.
- `user`: the user said something.

#### Compound Statements

Compound statements contain (groups of) other statements;

- `define action`: define an action and its parameters (for documentation purposes).
- `define bot`: define a bot message.
- `define flow`: define a flow.
  - `parallel`: a parallel flow can have multiple parallel instances at the same time;
  - `test`: a test flow is only used for testing
  - `sample`: a sample flow is meant for documentation only
  - `extension`: an extension flow can interrupt other flows on "decision elements"
  - `continuous`: continuous flows cannot be interrupted i.e. they will be aborted if they can't continue.
- `define user`: define examples for a user message.
- `else`: alternative path for `if` / `when`
- `if`: conditional branching.
- `while`: repeated execution.
- `when`: branching based on event.
