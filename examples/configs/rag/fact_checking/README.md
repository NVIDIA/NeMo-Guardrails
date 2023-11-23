# Custom Fact Checking

This examples showcases the use of [AlignScore](https://aclanthology.org/2023.acl-long.634.pdf) for fact-checking.

The structure of the config folder is the following:

- `kb/` - A folder containing our knowledge base to retrieve context from and fact check against. This folder includes the March 2023 US Jobs report in `kb/report.md`.
- `config.yml` - The config file holding all the configuration options.
- `general.co` - A colang file with some generic examples of colang `flows` and `messages`.
- `factcheck.co` - A colang file that contains the fact-checking related flows. .
