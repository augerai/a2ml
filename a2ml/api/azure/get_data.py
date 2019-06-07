import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
def get_data(): 
    df = pd.read_csv("https://www.openml.org/data/get_csv/18626236/baseball.arff", delimiter="\t", quotechar='"')
    # get integer labels
    le = LabelEncoder()
    le.fit(df["RS"].values)
    y = le.transform(df["RS"].values)
    df = df.drop(["RS"], axis=1)
    return { "X" : df, "y" : y }