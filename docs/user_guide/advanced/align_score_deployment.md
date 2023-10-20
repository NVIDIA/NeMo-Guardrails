# AlignScore Deployment

**NOTE: THIS SECTION IS WORK IN PROGRESS.**

In order to deploy an AlignScore server, follow these steps:

1. Install the `alignscore` package from the GitHub repository:

```bash
git clone https://github.com/yuh-zha/AlignScore.git
cd AlignScore
pip install .
```

2. Download the Spacy `en_core_web_sm` model:

```bash
python -m spacy download en_core_web_sm`
```

3. Download the one or both of the AlignScore checkpoints:
```
curl -OL https://huggingface.co/yzha/AlignScore/resolve/main/AlignScore-base.ckpt
curl -OL https://huggingface.co/yzha/AlignScore/resolve/main/AlignScore-large.ckpt
```

4. Set the `ALIGN_SCORE_PATH` to point to the path where the checkpoints have been downloaded.

5. Start the AlignScore server.

```bash
python -m nemoguardrails.library.factchecking.alignscore.server --port
```

**TODO**: document the `--port` and `--models` options.
