import pandas as pd

df = pd.read_csv('datasets/evaluation/indian_sms_eval.csv')
print(f"Total rows: {len(df)}")
print("\nCategory counts:")
print(df['category'].value_counts())
print("\nLanguage counts:")
print(df['language'].value_counts())
print("\nLabel counts:")
print(df['label'].value_counts())
