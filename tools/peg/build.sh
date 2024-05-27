#!/bin/bash

# create and activate virtual environment
python -m venv env
source env/bin/activate



# Check for java
if ! command -v java &> /dev/null
then
    echo "Java is required for ANTLR4. Installing..."
    sudo apt-get update
    sudo apt-get install -y default-jre
fi

# Check for curl
if ! command -v curl &> /dev/null
then
    echo "curl is required. Installing..."
    sudo apt-get update
    sudo apt-get install -y curl
fi

# Download and install ANTLR4 if it is not already installed
curl -s -O https://www.antlr.org/download/antlr-4.13.1-complete.jar

# Install requirements.txt
pip install --no-cache-dir -r requirements.txt > /dev/null 2>&1

# Generate parser files
java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 ColangMini.g4 -visitor -o colang > /dev/null 2>&1

mv __init__.py colang/ > /dev/null 2>&1

# Run the interpreter
echo " "
echo "To run the message interpreter, use the following command:"
echo "python message_interpreter.py input_1.co"
echo " "
echo "To run the flow interpreter, use the following command:"
echo "python flow_interpreter.py input_1.co"
