# Red Teaming

This is a sample server configuration with support for red teaming. It contains the following:

1. A sample `challenges.json` file.
2. Two sample guardrails configurations.

To run the server with this configuration you can use the following command (assuming you've cloned the repository and are running the command from the root of the project):

```bash
$ nemoguardrails server --config=examples/red-teaming
```

The rated conversations will be saved in a CSV file named `ratings.csv` in the current working directory.
