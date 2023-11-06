# [Part 1] Basic Authentication

This is a demo to show increasingly complex examples of the art of the possible with NeMo Guardrails. The Dialog manager based on Colang is a rich interface that enables basic and conditional branching, reusing conversation flows, and intelligently parsing entities and variables. The example will make extensive use of `actions` which makes the workflow more extensible because one can register any Python function as a Colang action.

Key features of the architecture of NeMo Guardrails and the underlying dialog manager that will be touched on in this example include:

- Tracking information provided by the user
- Understanding context and resolving ambiguity
- Controlling the conversation flow
- Communicating with external services

## Steps performed in the demo:

- [Part 1] Authenticate the user by asking for user id, first name, last name and verify against a database. Later on, one can replace this with a more complex authentication guardrail. Concretely the following salient features will be displayed:
     - The developer can control the order of when bot asks questions and conditionally asks questions and requests for user input.
    - The developer can selectively store values in a Python dictionary or JSON file locally. This is helpful to develop a cache or store user details in a production environment.
    -  The developer can selectively send specific parsed inputs to customizable actions. So, sending only the first name, or last name for authentication rather than the entire message history and context.
    - The user inputs multiple input variables and the dialog manager can take care of context and parsing information and then pass it onto Guardrails for filtering and dialog management.
- [Part 2] Loads user profile and informs the user of the bot's capabilities such as file summarization, question answering with citations or the ability to "talk to your data", opening IT tickets etc.

## How to run

Follow the steps to install and setup Nemo Guardrails, then within the `reference_demo` folder run: ` nemoguardrails chat --config=. `

The following shows an example conversation flow for authentication (Part 1 of the reference demo):

```
user:~/NeMo-Guardrails/examples/reference_demo$ nemoguardrails chat --config=.
Starting the chat...
> hey
What is your user id?
> 12345
Thank you for sharing your user id!
What is your first name?
> alice
Good to meet you Alice!
What is your last name?
> ecila
Thank you for sharing your last name too, Alice ecila!
You have been authenticated Alice ecila!
> ^C
Aborted!
```
## Implementation Details

- The `ground_truth.json` contains details of some example users. This will be used for a basic authentication rail. One can change the details of this file to control the authentication process. For production versions one can increase the complexity of authentication and add third party APIs and two factor authentication within this workflow via actions.
