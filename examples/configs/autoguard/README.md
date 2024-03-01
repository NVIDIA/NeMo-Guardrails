# AutoGuard

This example showcases the use of AutoGuard guardrails.

The structure of the config folders is the following:
- `autoguard_config` - example configuration folder for all guardrails (except factcheck)
  - `config.yml` - The config file holding all the configuration options.
  - `prompts.yml` - The config file holding the adjustable content categories to use with AutoGuard.
- `autoguard_factcheck_config` - example configuration folder for AutoGuard's factcheck
  - `config.yml` - The config file holding all the configuration options.
  - `prompts.yml` - The config file holding the adjustable content categories to use with AutoGuard's factcheck endpoint.
