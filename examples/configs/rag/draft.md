**TODO**: split this in two and move to corresponding sections.

# Nemo Guardrails Reference Examples

This document details how to go about building workflows and applications using Nemo Guardrails. The examples contained are increasingly complex ways to use NeMo Guardrails. There are two examples:

- [BasicAuth]()
  Shows a simple authentication process. One can replace this by integrating with third party Authentication services.
- [PineconeRAG]()
  Uses Pinecone vector database for Retreival Augmented Generation.

## Getting Started

Broadly the following steps are involved:

1. [Develop a workflow]()
    This includes writing out a sample conversation including both the bot and the user responses and evaluating where certain rails will be triggered and plan how you will call these rails, eg do you need to pass any arguments or will there be data on the disk that's being read or written to? This also extends to understanding if functionality already exists in the Nemo guardrail core if you will be using third-party APIs or if it is better to extend the Nemo guardrail core for your use case.
2. [Develop different use cases within the workflow]()
    Writing out the colang flows, Python actions and integrating with any third-party APIs.
3. [Testing and Logging]()
    Best practices for testing, and logging the flows.


### Develop a workflow

Start with the workflow in mind and ideally build a sample conversation. The sample conversation should include as many use cases as possible within the same workflow. As an example, when I think about what I want in this reference demo I build the following sample conversation:

```
Bot: Hi what is your user ID
User:  my user ID is 1 2 3 4 5
Bot:  thank you for providing me your user ID what is your name
User:  my first name is siddha
Bot:  what's your last name
User:  ganju
Bot:  You are authenticated!
User:  What does Nvidia do?
Bot:  ...answers the question...and provides citation...
User: oh and what about <detailed questions about Nvidia>
Bot: ...answers the question...and provides citation...
User: can you tell me what an apple is
Bot: the documents you have access to do not provide this information
User: can you summarize this conversation
Bot: ..provides summary...
```

Now, putting the developer hat on and going over the sample conversation I can see that there are a few sub-components, for example for the enterprise bot, authentication is one use case, summarization is another and question answering with references is yet another use case, but all these three ties into one enterprise workflow. There may be other enterprise workflows with a different set of use cases. This sample conversation can be as detailed as you want. The main advantage of building a sample conversation is you can see where certain rails are expected to be triggered and what the flow of functions and actions looks like. The sample conversation can also inform you if you need access to third-party APIs or if you will need to build certain features within the core of Nemo Guardrails. For example, to build question answering with references we can use third-party tools such as Pinecone vector database and Langchain.

### Develop different use cases within the workflow

Start with the first use case and write down all the helper functions or Python actions. Because in the previous phase, you have already thought about where you will call the actions into the rails and what the skeleton of these actions looks like now you only need to write them out. Remember to test out the actions independently using test functions before you write out the rails. Use this opportunity to also ensure that logging works perfectly.

In this reference example we first build out the basic authentication flow, then search summarisation and question answering with references. All of these are additional applications built on top of core Nemo Guardrails and therefore need to be developed separately. To do this familiarity with the architecture of Nemo Guardrails core is essential and the best way to do that is to bring everything into the vscode, review the code and run things, track the flow, and use the debugger often.

Next, write out all the rails (in the `xx.co` files) and utilize the helper functions or Python actions. There are a few rules of thumb to remember while writing out the rails. Let's go through them here:

- Check that the flow order is correct and that all subflows are defined before the main flow. Ideally, you want to define subflows such that they are reusable components in your code. Its utility is similar to a helper function.
- Each sub-flow will likely have at least three components:
  - Bot requesting some information
  - User providing said information
  - Bot performing some action on this provided information (eg expressing gratitude or calling a Python action)
- When defining the sample conversations, it’s important to stick to the exact format i.e.
```
user "<USER MESSAGE>"
  <USER CANONICAL FORM>
bot <BOT CANONICAL FORM>
  "<BOT MESSAGE>"
```
- Canonical forms refer to the function definitions that are in the `.co` files, so their names have to be an exact match.
- It’s important for the sample conversation to be an actual conversation, rather than with placeholders. This sample converstation is sent to the LLM and eventually the LLM imitates the sample converstation during the real, live conversation with the user.
- Each of these components may have its definition, for example for “user providing said information”, it can look like this:
```
define user give firstname
    "My name is James"
    "I'm Julio"
    "Sono Andrea"
    "Siddha"
```
- One can add comments as part of the prompting to make it more informative and instructional. Often what happens is you might need to define a rail that might seem complicated (such as answering all questions if they don't relate to in-memory databases, in this example one way is to first define what in-memory databases are and then the bot informs the user that such questions cannot be answered). However, this requirement can be summarized in a single sentence and therefore a comment is potentially a better place for it. Also, recall that under the hood similarity search is happening so as long as the comment is clear it doesn't need a lot of diversity in examples. One should of course try out the comment, test it out on adversarial conditions, for example with edge cases, and see if it works before putting it into production. In practice, it has been observed that adding comments makes the LLM outputs perform better. An example of this can be seen in our basic authentication flow:
`#Extract only the first name. Wrap in Double Quotes. E.g. "Siddha"`

- Choosing the right models from OpenAI Or whichever model service you are using. If your workflow utilizes a chat-style interface make sure that the model works as a chat model. For example:
```
models:
  - type: main
    engine: openai
    model: text-davinci-003
```
The above works as a chat model, however, the following does not work as a chat model anymore.

```
models:
  - type: main
    engine: openai
    model: gpt-3.5-turbo
    parameters:
      temperature: 0.0
```
- If you have defined any actions in `actions.py` or, in `config.py`, remember to [register](https://github.com/NVIDIA/NeMo-Guardrails/blob/main/docs/user_guides/configuration-guide.md#custom-initialization) those actions within the `init` method. While running, lookout for standard output like the following which inform the developer that the action has been successfully added. This will be visible when running with the `-verbose` argument.
```
Event StartInternalSystemAction {'uid': '', 'event_created_at': '', 'source_uid': 'NeMoGuardrails', 'action_name': '<name_of_action>', 'action_params': {}, 'action_result_key': None, 'action_uid': '', 'is_system_action': False}
Executing action <name_of_action>
```
- Before running the entire application, ensure that individual components such as `actions.py` or, `config.py` etc, if present, have been compiled and there are no issues within.
- When calling any actions that receive direct arguments, so they receive a user defined variable, instead of the context dictionary, ensure that the arguments are prefixed with a `$`. For example: `$authenticated = execute authenticate_user(user_id=$user_id, firstname=$firstname, lastname=$lastname)`
- The `context` dictionary contains absolutely all information that Nemo Guardrails gathers during the conversation. Consider leveraging this for passing information to any backend that may need to be integrated into the application.


### Testing and Logging

Logging is the process of recording information about the operation of a system or application. Log messages can be used for a variety of purposes such as debugging, monitoring (to identify performance bottlenecks), security (to identify unauthorized access attempts or malicious activity), compliance, etc. For the first few production runs or during dogfooding it's always a good idea to keep the logs because of reduced downtime, improved security, Increased efficiency, and improved compliance.

In Nemo Guardarils there are two main ways to look under the hood and ensure that everything is working properly:
- Add logging yourself with a `DateTime` stamp to see the error trace if something breaks. That way for every run you will generate a log and it's always going to happen in the backend and you don't need to worry about it while doing the development. Specifically in the logfiles, you can see the errors (if any) that arise in the Python actions, the LLM responses, and any third-party APIs that you may be using.
- Running with the `–verbose` argument to see in real-time the LLM response and how the functions flow into each other in the workflow. Ofcourse the age-old debugging tactics of applying breakpoints, stepping into functions etc are also recommended.

You can set up the logs as follows:
```
LOG_FILENAME = datetime.now().strftime('logs/mylogfile_%H_%M_%d_%m_%Y.log')
log = logging.getLogger(__name__)
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
print(logging.getLoggerClass().root.handlers[0].baseFilename)
```

#### Key things to keep in mind while logging:

- Log at the right level: There are different levels of logging, such as debug, info, warn, and error. It is important to log at the appropriate level for the type of information being recorded. For example, you should not log debug information in production unless you are actively troubleshooting a problem.
- Log in a consistent format: Log messages should be formatted in a consistent way to make them easy to read and parse. This will make it easier to analyze logs and identify patterns.
- Store logs securely: Log files should be stored securely to prevent unauthorized access. This is especially important for logs that contain sensitive information.
