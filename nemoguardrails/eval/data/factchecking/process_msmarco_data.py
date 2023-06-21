from datasets import load_dataset
import pandas as pd
import json
import tqdm

# Install the datasets library using pip install datasets 
# Load the dataset
dataset = load_dataset('ms_marco', 'v2.1')

# Use the validation split and convert to pandas dataframe
df = pd.DataFrame(dataset['validation'])

#Convert the dataframe to a json file with "question", "answers" and "evidence" as keys
fact_check_data = []

for idx, row in tqdm.tqdm(df.iterrows()):
    sample = {}
    sample['question'] = row['query']
    sample['answer'] = row['answers'][0]
    if row['passages']['is_selected'].count(1) == 1:
        sample['evidence'] = row['passages']['passage_text'][row['passages']['is_selected'].index(1)]
        fact_check_data.append(sample)

# Save the json file
with open('msmarco.json', 'w') as f:
    json.dump(fact_check_data, f)
