import pandas as pd


def summarize_csv(path):
    df = pd.read_csv(path)
    return {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "numeric_summary": df.describe(include="all").fillna("").to_dict(),
    }
