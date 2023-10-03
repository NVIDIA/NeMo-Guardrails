# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set environment variables for better layer caching and non-interactive package installation
ENV DEBIAN_FRONTEND=noninteractive \
    ANTLR_JAR_VERSION=4.13.1

# Set the working directory
WORKDIR /app

# Install necessary dependencies in one layer for optimization
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        default-jre && \
    curl -O https://www.antlr.org/download/antlr-${ANTLR_JAR_VERSION}-complete.jar && \
    apt-get remove --purge -y curl && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the necessary files to the container at once
COPY . .

# Install the ANTLR4 Python runtime and other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Generate the parser and lexer from the grammar file
RUN java -jar antlr-${ANTLR_JAR_VERSION}-complete.jar -Dlanguage=Python3 ColangMini.g4 -visitor -o colang
RUN mv __init__.py colang/
# # Set the default command to run the parser implementation
# CMD ["python", "message_interpreter.py", "input_1.co"]
CMD ["/bin/bash"]
