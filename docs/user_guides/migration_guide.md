# Migrating from Colang 1 to Colang 2

## Migration Script

This script is designed to migrate colang modules and packages (co files) from Colang 1.0 format to Colang 2.x. It performs several transformations on the content of the files, i.e., syntax transformation, such as converting certain keywords and changing the case of certain identifiers.

### How it Works

The script walks through the directory specified by the `path` argument and applies the transformations to each file ending with `.co`. The transformations include:

- Converting `define flow` to `flow`
- Converting `define subflow` to `flow`
- Converting `define bot` to `flow bot`
- Converting `define user` to `flow user`
- Converting `execute` to `await`
- Converting snake_case identifiers after `await` to CamelCase and append it with key word `Action` while preserving any arguments used.
- Converting `else when` to `or when`
- Converting `stop` to `abort`
- Converting quoted strings after `bot` to `bot say` or `or bot say`
- Converting quoted strings after `user` to `user said` or `or user said`
- Generate Anonymous flows, so when you are using a flow like below in colang 1
- Use `active` decorator for root flows (flows that need activation).
- Add `global` keyword to global variables.
- Converting `...` to corresponding syntax in colang 2
if you have a flow like below in colang 1
```colang
#  some instruction in natural language
$var_name = ...
```
it translates it to colang 2 as below

```colang

#$name = await GenerateValueAction(instructions="some instruction in natural language")
```

or if we have a flow like below in colang 1
```colang
bot ...

# or
user ...
```
it translates it to colang 2 as below
```colang
UtteranceBotActionFinished()
# or
UtteranceUserActionFinished()

```

- If rails are defined in `config.yml` a `_rails.co` file is generated with the rails defined in it.

```colang
define flow
  user express greeting
  bot express greeting
```

is transformed to

```co
@active
flow express_greeting
  user express greeting
  bot express greeting
```

> Note: It is a convention to use past tense for user flows and present tense for bot flows. However, the migration script does not enforce this convention. We strongly advice you to do so manually.

The script keeps track of the number of lines processed and the number of changes made in each file. It also counts the total number of files changed.

> Warning: The script modifies the original files. It is recommended to use version control to track the changes made by the script. It also enables you to see the differences between the original and modified files.

### Potential Issues and Weaknesses

- The script assumes that the input files are correctly formatted. If a file is not correctly formatted, the script may not work as expected.
- The script uses regular expressions to find and replace certain patterns in the text. If the input files contain text that matches these patterns but should not be replaced, the script may produce incorrect results.
- The script renames the original files and writes the transformed content to new files with the original names. Use version control to track the changes made by the script.
- The script does not handle errors that may occur during file reading and writing operations. If an error occurs, the script logs the error and continues with the next file.
- using characters like `-`, `+` and tokens like `or`, `and`, etc is not supported in flow definition, the migratin script does not handle this conversion due to handling. In case you have them try to fix them
- It is a better practice to define global variables at the begining of the flow however the migration script does not enforce this. We strongly advice you to do so manually.



### Using NeMo Guardrails CLI

To use the `convert` command, you can use:

```bash
nemoguardrails convert /path/to/directory
```

The `convert` command has several options:

- `--verbose` or `--no-verbose`: If the migration should be verbose and output detailed logs. Default is `no-verbose`.
- `--validate` or `--no-validate`: If the migration should validate the output using Colang Parser. Default is `no-validate`.
- `--use-active-decorator` or `--no-use-active-decorator`: If the migration should use the active decorator. Default is `use-active-decorator`.
