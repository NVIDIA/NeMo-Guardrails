# Getting Started

## Docker

One can use the docker file to build the image and run the container. The docker file is located at `tools/peg/Dockerfile`.

## Script

Also there is a script to install the required dependencies and run the parser. The script is located at `tools/peg/setup.sh`.

## Manual


### Install ANTLR4

```zsh
$ cd /usr/local/lib
$ curl -O https://www.antlr.org/download/antlr-4.13-complete.jar
$ export CLASSPATH=".:/usr/local/lib/antlr-4.13-complete.jar:$CLASSPATH"
$ alias antlr4='java -jar /usr/local/lib/antlr-4.13-complete.jar'
$ alias grun='java org.antlr.v4.gui.TestRig'
```

### Install Python3 ANTLR Runtime

```zsh
pip3 install antlr4-python3-runtime
```

### Generate Parser

Generate the parser. This will generate the required base classes for the parser. Every time the grammar is updated, this step needs to be repeated. The generated files are already included in this repo.

> **NOTE**
> The users do not need to install ANTLR4 to use Nemo-Guardrails but they only need to install Python3 ANTLR Runtime. However, the contributors need to install ANTLR4 to generate the parser whenever the grammar changes.

```zsh
antlr4 -Dlanguage=Python3 MiniColang.g4 -visitor  -o ./colang

```

> **Warning**
> Move the `__init__.py` to the `colang` dir before executing following commands.

## Run the Parser

To run the parser, use the following commands.

```zsh

python message_interpreter.py ./inputs/input_1.co
python flow_interpreter.py ./inputs/input_1.co

```

> **Warning**
> Every valid input file must be passed through `utils.transform_to_braces` function before passing it to the parser. This function will transform the input file to a valid input file for the parser. The function is located at `utils.py` file. This is a work around INDENT and DEDENT tokens in the grammar.
