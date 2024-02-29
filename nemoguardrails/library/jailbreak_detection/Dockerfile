# Use python:3.10 as the base image
FROM python:3.10-slim

# Install git
RUN apt-get update && apt-get install -y git && apt-get install gcc -y && apt-get install g++ -y && apt-get install python3-dev -y && apt-get clean

# Upgrade pip
 RUN pip install --upgrade pip

# Copy the source code
COPY . /app

# Set working directory
WORKDIR /app

# Install the minimal set of requirements for jailbreak detection Server
RUN pip install -r requirements.txt

# Set the device on which the model should load e.g., "cpu", "cuda:0", etc.
ENV JAILBREAK_CHECK_DEVICE=cpu

# Predownload the GPT2 model.
RUN python -c "from transformers import GPT2LMHeadModel, GPT2TokenizerFast; GPT2LMHeadModel.from_pretrained('gpt2-large'); GPT2TokenizerFast.from_pretrained('gpt2-large');"

# Expose a port for the server
EXPOSE 1337

# Start the server as the default command
ENTRYPOINT ["/usr/local/bin/python", "server.py"]
CMD ["--port=1337"]
