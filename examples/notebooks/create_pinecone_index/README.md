# Creating a Pinecone Vector DB and Uploading Data

In order to use this guide, you will need to obtain a [Pinecone API key](https://www.pinecone.io/). The instructions to create a Pinecone database, and uploading a few select PDF files to the database are based on the [official examples](https://github.com/pinecone-io/examples/blob/master/docs/langchain-retrieval-augmentation.ipynb) provided by Pinecone. All the API key values are set in the environment and read from there. To test out the code, the Wikipedia page of NVIDIA has been used and you might see some outputs in the cells.

```python
import os
from uuid import uuid4

import fitz
import pinecone
import tiktoken
from datasets import Dataset
from tqdm.auto import tqdm
```

Define a helper function to parse PDF files. You can choose to read any format of text files.

```python
def load_data_from_pdfs(path):
    local_urls = []
    local_articles = []
    for x in tqdm(os.listdir(path)):
        if x.endswith(".pdf"):
            print(x)
            local_urls.append(path + x)
            doc = fitz.open(path+x)
            text = ""
            for page in doc:
                text += page.get_text()
            local_articles.append(text)
    data_local = {"id": [i for i in range(len(local_urls))], "text": [local_articles[i] for i in range(
        0, len(local_urls))], "url": [local_urls[i] for i in range(0, len(local_urls))]}
    return data_local
```

Create a Hugging Face format dataset

```python
data = load_data_from_pdfs("kb/")
our_dataset = Dataset.from_dict(data)
print(our_dataset)
```

```
      0%|          | 0/4 [00:00<?, ?it/s]

    nvidia.pdf
    Dataset({
        features: ['id', 'text', 'url'],
        num_rows: 1
    })
```

One can save the dataset in Hugging Face dataset format to disk to avoid processing again.

```python
our_dataset.save_to_disk("kb")
```

```
Saving the dataset (0/1 shards):   0%|          | 0/1 [00:00<?, ? examples/s]
```

Every record contains *a lot* of text. Our first task is therefore to identify a good preprocessing methodology for chunking these articles into more "concise" chunks to later be embedding and stored in our Pinecone vector database.

```python
tiktoken.encoding_for_model('gpt-4')
tokenizer = tiktoken.get_encoding('cl100k_base')

def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)
```

Now, we use LangChain's `RecursiveCharacterTextSplitter` to split our text into chunks of a specified max length using the function we defined above. Keep in mind that the processing strategy that one uses to populate the database must be same as when querying the database.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=20,
    length_function=tiktoken_len,
    separators=["\n\n", "\n", " ", ""]
)
```

Lets test it out!

```python
chunks = text_splitter.split_text(our_dataset[0]['text'])[:3]
chunks
```

```
['10/3/23, 11:26 AM\nNvidia - Wikipedia\nhttps://en.wikipedia.org/wiki/Nvidia\n1/25\nNvidia Corporation\nHeadquarters at Santa Clara in 2023\nTrade name\nNVIDIA\nType\nPublic\nTraded as\nNasdaq: NVDA (https://w\nww.nasdaq.com/market-a\nctivity/stocks/nvda)\nNasdaq-100 component\nS&P 100 component\nS&P 500 component\nIndustry\nComputer hardware\nComputer software\nCloud computing\nSemiconductors\nArtificial intelligence\nGPUs\nGraphics cards\nConsumer electronics\nVideo games\nFounded\nApril 5, 1993 in\nSunnyvale, California,\nU.S.\nFounders\nJensen Huang\nCurtis Priem\nChris Malachowsky\nNvidia\nNvidia Corporation[note 1][note 2] (/ɛnˈvɪdiə/ en-VID-ee-ə)\nis \nan \nAmerican \nmultinational \ntechnology \ncompany\nincorporated in Delaware and based in Santa Clara,\nCalifornia.[2] It is a software and fabless company which\ndesigns graphics processing units (GPUs), application\nprogramming interface (APIs) for data science and high-\nperformance computing as well as system on a chip units\n(SoCs) for the mobile computing and automotive market.\nNvidia is a dominant supplier of artificial intelligence\nhardware and software.[3][4] Its professional line of GPUs\nare used in workstations for applications in such fields as\narchitecture, engineering and construction, media and\nentertainment, \nautomotive, \nscientific \nresearch, \nand\nmanufacturing design.[5]\nIn addition to GPU manufacturing, Nvidia provides an API\ncalled CUDA that allows the creation of massively parallel',
 "called CUDA that allows the creation of massively parallel\nprograms which utilize GPUs.[6][7] They are deployed in\nsupercomputing sites around the world.[8][9] More recently,\nit has moved into the mobile computing market, where it\nproduces Tegra mobile processors for smartphones and\ntablets as well as vehicle navigation and entertainment\nsystems.[10][11][12] Its competitors include AMD, Intel,[13]\nQualcomm[14] and AI-accelerator companies such as\nGraphcore. It also makes AI-powered software for audio and\nvideo processing, e.g. Nvidia Maxine.[15]\nNvidia's GPUs are used for edge-to-cloud computing and\nsupercomputers. Nvidia expanded its presence in the\ngaming industry with its handheld game consoles Shield\nPortable, Shield Tablet, and Shield TV and its cloud gaming\nservice GeForce Now.\nNvidia's offer to acquire Arm from SoftBank in September\n2020 failed to materialize following extended regulatory\nscrutiny, leading to the termination of the deal in February\n2022 in what would have been the largest semiconductor\nacquisition.[16][17]\nHistory\n10/3/23, 11:26 AM\nNvidia - Wikipedia\nhttps://en.wikipedia.org/wiki/Nvidia\n2/25\nHeadquarters\nSanta Clara, California,\nU.S.\nArea served\nWorldwide\nKey people\nJensen Huang\n(President and CEO)\nProducts\nGraphics processing units\n(including with ray-tracing\ncapability in Nvidia RTX\nline)\nCentral processing units\nChipsets\nDrivers\nCollaborative software\nTablet computers\nTV accessories\nGPU-chips for laptops\nData processing units\nRevenue\n US$26.97 billion (2023)\nOperating\nincome\n US$4.224 billion (2023)\nNet income\n US$4.368 billion (2023)\nTotal assets",
 "Net income\n US$4.368 billion (2023)\nTotal assets\n US$41.18 billion (2023)\nTotal equity\n US$22.10 billion (2023)\nNumber of\nemployees\n26,196 (2023)\nSubsidiaries\nNvidia Advanced\nRendering Center\nMellanox Technologies\nCumulus Networks\nWebsite\nnvidia.com (https://www.n\nvidia.com/)\nFootnotes / references\nFinancials as of January 29, 2023[1]\nNvidia was founded on April 5, 1993,[18][19][20] by Jensen\nHuang (CEO as of 2023), a Taiwanese-American electrical\nengineer who was previously the director of CoreWare at LSI\nLogic and a microprocessor designer at AMD; Chris\nMalachowsky, \nan \nengineer \nwho \nworked \nat \nSun\nMicrosystems; and Curtis Priem, who was previously a\nsenior staff engineer and graphics chip designer at IBM and\nSun Microsystems.[21][22] The three men founded the\ncompany in a meeting at a Denny's roadside diner in East\nSan Jose (just off Interstate 680 at the Berryessa Road\ninterchange).[23]\nIn 1993, the three co-founders believed that the proper\ndirection for the next wave of computing was accelerated\ncomputing such as graphics-based computing because it\ncould solve problems that general-purpose computing could\nnot.[24] They also observed that video games were\nsimultaneously one of the most computationally challenging\nproblems and would have incredibly high sales volume; the\ntwo conditions do not happen very often.[24] Video games\nbecame the company's flywheel to reach large markets and\nfund \nhuge \nR&D \nto \nsolve \nmassive \ncomputational"]
```

Lets see the lengths

```python
tiktoken_len(chunks[0]), tiktoken_len(chunks[1]), tiktoken_len(chunks[2])
```

```
(383, 387, 377)
```

Using the `text_splitter` we get much better sized chunks of text. We'll use this functionality during the indexing process later. Now let's take a look at embedding.

## Creating Embeddings

Building embeddings using LangChain's OpenAI embedding support is fairly straightforward. We first need to add our [OpenAI api key]() by running the next cell:

```python
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
```

*(Note that OpenAI is a paid service and so running the remainder of this notebook may incur some small cost)*

After initializing the API key we can initialize our `text-embedding-ada-002` embedding model like so:

```python
from langchain.embeddings.openai import OpenAIEmbeddings

model_name = 'text-embedding-ada-002'

embed = OpenAIEmbeddings(
    model=model_name,
    openai_api_key=OPENAI_API_KEY
)
```

Now we embed some example text from the data we just parsed.

```python
res = embed.embed_documents(our_dataset[0]['text'][:500])
len(res), len(res[0])
```

```
(500, 1536)
```

From this we get 1536-dimensional embeddings. Now we move on to initializing our Pinecone vector database.

## Vector Database

To create our vector database we first need a [free API key from Pinecone](https://app.pinecone.io). Then we initialize like so:

```python
index_name = 'nemoguardrailsindex'
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
# find ENV (cloud region) next to API key in console
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT') or 'gcp-starter'

pinecone.init(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENVIRONMENT
)
```

If this is a new index, then it takes a few minutes to create the new index. So the following code might return `NULL` at first.

```python
if index_name not in pinecone.list_indexes():
    # we create a new index
    pinecone.create_index(
        name=index_name,
        metric='cosine',
        dimension=len(res[0])  # 1536 dim of text-embedding-ada-002
    )
```

Verify that it was created, or ensure that the old index exists. If you are using a free version of Pinecone then the indexes are purged on a regular basis if not being used.

```python
for index_name in pinecone.list_indexes():
  print(index_name)
```

```
nemoguardrailsindex
```

Then we connect to the selected index:

```python
index = pinecone.GRPCIndex(index_name)
```

```python
index.describe_index_stats()
```

```yaml
{'dimension': 1536,
 'index_fullness': 0.0,
 'namespaces': {'': {'vector_count': 0}},
 'total_vector_count': 0}
```

If this is a new Pinecone index, then we expect to see a `total_vector_count` of `0`, as we haven't added any vectors yet. If its a previously existing index then it should have a non-zero value.

## Indexing

We can perform the indexing task using the LangChain vector store object. But for now it is much faster to do it via the Pinecone python client directly. We will do this in batches of `100` or more.

```python
batch_limit = 10

texts = []
metadatas = []

for i, record in enumerate(tqdm(our_dataset)):
    # first get metadata fields for this record
    metadata = {
        'id': str(record['id']),
        'source': record['url']
    }
    # now we create chunks from the record text
    record_texts = text_splitter.split_text(record['text'])
    # create individual metadata dicts for each chunk
    record_metadatas = [{
        "chunk": j, "text": text, **metadata
    } for j, text in enumerate(record_texts)]
    # append these to current batches
    texts.extend(record_texts)
    metadatas.extend(record_metadatas)
    # if we have reached the batch_limit we can add texts
    if len(texts) >= batch_limit:
        ids = [str(uuid4()) for _ in range(len(texts))]
        embeds = embed.embed_documents(texts)
        index.upsert(vectors=zip(ids, embeds, metadatas))
        texts = []
        metadatas = []

if len(texts) > 0:
    ids = [str(uuid4()) for _ in range(len(texts))]
    embeds = embed.embed_documents(texts)
    index.upsert(vectors=zip(ids, embeds, metadatas))
```

```
  0%|          | 0/1 [00:00<?, ?it/s]
```

We've now indexed everything. It might take a minute for the indexing to actually happen. We can check the number of vectors in our index like so:

```python
index.describe_index_stats()
```

```yaml
{'dimension': 1536,
 'index_fullness': 0.00061,
 'namespaces': {'': {'vector_count': 61}},
 'total_vector_count': 61}
```

That is it for now. You have created a Pinecone Vector database, initialized it and uploaded data of your choice to it. Now, you can head over to NeMo Guardrails and interact with the database.
