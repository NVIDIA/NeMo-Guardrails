import pandas as pd
from gpt4pandas import GPT4Pandas
df = pd.read_csv('/workspace/Experiment/titanic.csv',sep=',')

# Initialize the GPT4Pandas model
model_path = '/workspace/ckpt/gpt4all/ggml-vicuna-13b-4bit-rev1.bin'

Embarked_d={'C' : "Cherbourg", 'Q': "Queenstown", 'S' : "Southampton"}
n=len(df)
ls=[]
for i in range(n):
    temp=df.iloc[i,-1]
    if type(temp)==str :
        out=Embarked_d[temp]
        ls.append(out)
    else :
        ls.append('N/A')
        print(i,temp, type(temp))
df['port']=ls
df['Lived']=df['Survived'].apply(lambda x: 'survived' if x ==1 else 'died')
d=df.groupby(['Sex'])['Lived'].value_counts()
#flatten the groupedby pandas series to flatten dictionary
d2=d.reset_index(inplace=False)
gpt = GPT4Pandas(model_path, d2, verbose=False)