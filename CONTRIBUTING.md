# Contributing to NeMo Guardrails

Thank you for your interest in contributing to NeMo Guardrails! This document will help you get started with setting up your development environment and provide some guidelines for contributing.

## Setting Up the Development Environment

1. Ensure you have Python 3.x installed on your system. You can check your Python version by running:

```
python --version
```

2. Create a virtual environment to isolate your project's dependencies:

```
python -m venv colang_venv
```

Replace `colang_venv` with the desired name for your virtual environment directory.

3. Activate the virtual environment:

- On Windows:

  ```
  nemoguardrails_venv\Scripts\activate
  ```

- On macOS and Linux:

  ```
  source nemoguardrails_venv/bin/activate
  ```

4. Clone the project repository:

```
git clone https://github.com/NVIDIA/NeMo-Guardrails.git
```

5. Navigate to the project directory:

```
cd nemoguardrails
```

6. Install the development dependencies from `requirements-dev.txt`:

```
pip install -r requirements-dev.txt
```

This will install pre-commit, pylint, mypy, and any other development tools specified in the `requirements-dev.txt` file.

7. Set up pre-commit hooks:

```
pre-commit install
```

This will ensure that the pre-commit checks, including Black, pylint, and mypy, are run before each commit.

## Folder Structure

The project is structured as follows:
- `nemoguardrails/actions/`: implementation of various actions.
- `nemoguardrails/cli/`: implementation of the NeMo Guardrails CLI.
- `nemoguardrails/flows/`: implementation of the Colang Flows runtime.
- `nemoguardrails/language/`: Colang language parser.
- `nemoguardrails/llm`: various utilities for working with LLMs.
- `nemoguardrails/rails/`: implementation of various rails systems.
- `nemoguardrails/rails/llm`: rails for LLMs.

## Coding Style

We follow the Black coding style for this project.

## Submitting Your Changes

Once you have made your changes and ensured they follow the coding style, you can submit a pull request on GitHub. Please provide a clear and concise description of the changes you've made, and reference any related issues or discussions.

### Signing Your Work

We require that all contributors "sign-off" on their commits. This certifies that the contribution is your original work, or you have rights to submit it under the same license, or a compatible license.

Any contribution which contains commits that are not Signed-Off will not be accepted.

To sign off on a commit you simply use the `--signoff` (or `-s`) option when committing your changes:
  ```bash
  $ git commit -s -m "Add cool feature."
  ```
  This will append the following to your commit message:
  ```
  Signed-off-by: Your Name <your@email.com>
  ```

Full text of the DCO:

  ```
  Developer Certificate of Origin
  Version 1.1

  Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
  1 Letterman Drive
  Suite D4700
  San Francisco, CA, 94129

  Everyone is permitted to copy and distribute verbatim copies of this license document, but changing it is not allowed.

  Developer's Certificate of Origin 1.1

  By making a contribution to this project, I certify that:

  (a) The contribution was created in whole or in part by me and I have the right to submit it under the open source license indicated in the file; or

  (b) The contribution is based upon previous work that, to the best of my knowledge, is covered under an appropriate open source license and I have the right under that license to submit that work with modifications, whether created in whole or in part by me, under the same open source license (unless I am permitted to submit under a different license), as indicated in the file; or

  (c) The contribution was provided directly to me by some other person who certified (a), (b) or (c) and I have not modified it.

  (d) I understand and agree that this project and the contribution are public and that a record of the contribution (including all personal information I submit with it, including my sign-off) is maintained indefinitely and may be redistributed consistent with this project or the open source license(s) involved.
  ```

Thank you for contributing to NeMo Guardrails!
