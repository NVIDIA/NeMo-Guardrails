# Guardrails against LLM Vulnerabilities - Evaluation Results

NeMo Guardrails provides several mechanisms for protecting an LLM-powered chat application against security vulnerabilities, such as jailbreaks and prompt injections.
Here we present our first experiments when using a mix of dialogue and moderation rails to protect a sample Guardrails app against attacks.
Our sample app is the [ABC example](./../../examples/bots/abc/README.md), but the core ideas can be used for any Guardrails configuration.

## LLM Security Scanning

While most of the recent LLMs, especially commercial ones, are aligned to be more safe and secure, you should bear in mind that any LLM-powered application is prone to a wide range of attaks, for example see the [OWASP Top 10 for LLM](https://owasp.org/www-project-top-10-for-large-language-model-applications/).

## Garak for LLM vulnerability scanning

[Garak](https://github.com/leondz/garak/) is an open-source tool for scanning against the most common LLM vulnerabilities. It provides a comprehensive list of vulnerabilities, grouped into several categories.
Think at Garak as an LLM alternative to network security scanners such as [nmap](https://nmap.org/) or others.

## Guardrails against LLM Vulnerabilities - Main Results

Our sample ABC guardrails configuration has been scanned using Garak against vulnerabilities, using 4 different configurations offering an increasing protection against LLM vulnerabilities:
* Baseline 1: no protection (full Garak results [here](./../_assets/html/abc_bare_llm.report.html)).
* Baseline 2: using the general instructions in the prompt (full Garak results [here](./../_assets/html/abc_with_general_instructions.report.html)).
* Guardrails 1: using the dialogue rails implemented in the ABC configuration + general instruction (full Garak results [here](./../_assets/html/abc_with_general_instructions_and_dialog_rails.report.html)).
* Guardrails 2: dialogue rails + moderation rails (LLM Self-Checking - jailbreak and output moderation) + general instruction (full Garak results [here](./../_assets/html/abc_with_full_guardrails.report.html)).

The results for each vulnerability tested by Garak are summarized in the table below.
The table reports the protection rate against attacks for each type of vulnerability (higher is better).

| Garak vulnerability \ Guardrails configuration | Baseline 1 | Baseline 2 | Guardrails 1 | Guardrails 2 |
|------------------------------------------------|------------|------------|--------------|--------------|
| module continuation                            | 92.8%      | 69.5%      | 99.3%        | 100.0%       |
| module dan                                     | 27.3%      | 40.7%      | 61.3%        | 52.7%        |
| module encoding                                | 90.3%      | 98.2%      | 100.0%       | 100.0%       |
| module glitch                                  | 61.8%      | 43.6%      | 4.8%         | 0.0%         |
| module goodside                                | 32.2%      | 32.2%      | 66.7%        | 66.7%        |
| module knownbadsignatures                      | 4.0%       | 97.3%      | 100.0%       | 100.0%       |
| module leakreplay                              | 76.8%      | 85.7%      | 89.6%        | 100.0%       |
| module lmrc                                    | 85.0%      | 81.9%      | 86.5%        | 94.4%        |
| module malwaregen                              | 50.2%      | 92.2%      | 93.7%        | 100.0%       |
| module packagehallucination                    | 97.4%      | 100.0%     | 100.0%       | 100.0%       |
| module realpublicityprompts                    | 100.0%     | 100.0%     | 100.0%       | 100.0%       |
| module snowball                                | 34.5%      | 82.1%      | 99.0%        | 100.0%       |
| module xss                                     | 92.5%      | 100.0%     | 100.0%       | 100.0%       |

Even if the ABC example is using a powerful LLM (`gpt-3.5-turbo-instruct`), without guardrails it is still vulnerable to several types of attacks.
While using a general instruction in the prompt can reduce the attack success rate (and increase the protection rate reported in the table), only when using a mix of dialogue and moderation rails the LLM app is safer.
It is worth noticing that even just using dialogue rails results in very good protection.

At the same time, this experiment does not investigate if legitimate user requests are also blocked by the guardrails.
We will provide these results in a next release.

## Details about Categories of LLM Vulnerabilities

If you are interested about additional information about each vulnerability category in Garak, please consult the full results [here](./../_assets/html/) and [Garak GitHub](https://github.com/leondz/garak/) page.
