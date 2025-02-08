from os import listdir
import pandas as pd

def read_all_files():
    files = listdir('./dataset/')
    print(files)
    return [f for f in files if f.endswith('_uuid.csv')]


if __name__ == '__main__':
    files = read_all_files()
    for f in files:
        df = pd.read_csv('./dataset/' + f)
        for column in ["Claim", 'Review Summary', "Review", "Verdict"]:
            # find not nan values
            print(f, column, df[column].count())