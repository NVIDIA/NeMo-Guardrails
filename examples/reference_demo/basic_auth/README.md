# Reference Demo

This is a demo to show increasingly complex examples of the art of the possible with NeMo Guardrails. The Dialog manager based on Colang is a rich interface that enables basic and conditional branching, reusing conversation flows, and intelligently parsing entities and variables. The example will make extensive use of `actions` which makes the workflow more extensible because one can register any Python function as a Colang action. 

Key features of the architecture of NeMo Guardrails and the underlying dialog manager that will be touched on in this example include: 

- Tracking information provided by the user
- Understanding context and resolving ambiguity
- Controlling the conversation flow
- Communicating with external services

## Steps performed in the demo: 

- Authenticate the user by asking for user id, first name, last name and verify against a database. Later on, one can replace this with a more complex authentication guardrail.
     - The developer can control the order of when bot asks questions and conditionally asks questions and requests for user input
    - The developer can selectively store values in a Python dictionary or JSON file locally
    -  The developer can selectively send specific parsed inputs to customizable actions
    - The user inputs multiple input variables and the dialog manager can take care of context and parsing information and then pass it onto Guardrails
- Loads user profile and informs the user of the bot's capabilities such as file summarization, opening IT tickets etc.

## How to run

Within the `reference_demo` folder run: ` nemoguardrails chat --config=. `

The following shows an example conversation flow: 

```
user:~/NeMo-Guardrails/examples/reference_demo$ nemoguardrails chat --config=.
Starting the chat...
> hey
What is your user id?
> 12345
Thank you for sharing your user id!
Thank you for sharing your user id!
What is your first name?
> alice
Good to meet you Alice!
Good to meet you Alice!
What is your last name?
> ecila
success till here
Thank you for sharing your last name too, Alice ecila!
Thank you for sharing your last name too, Alice ecila!
You have been authenticated Alice ecila!
> ^C
Aborted!
```
## Implementation Details

- The `ground_truth.json` contains details of some example users. This will be used for a basic authentication rail. One can change the details of this file to control the authentication process.
  

