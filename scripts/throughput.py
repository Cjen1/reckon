#!/usr/bin/env python3
# type: ignore

import sys
import pandas as pd


def latency(df):
    df = df["t_result"] - df["t_submitted"]
    return df.describe(percentiles=[0.25, 0.50, 0.75, 0.99], include="all")

def interarrivial(df):
    df = df["t_submitted"]
    df = df.sort_values().diff()
    return df.describe(percentiles=[0.25, 0.5, 0.75, 0.99], include="all")

for filepath in sys.argv[1:]:

    df = pd.read_json(path_or_buf=filepath, orient="records")

    length = df["t_result"].max() - df["t_result"].min()
    throughput = len(df["t_result"]) / length
    errors = df["result"].unique()
    print("--------------------------------------------------")
    print(f"{filepath}")
    print("--------------------------------------------------")
    print(f"Errors: {errors}")
    print(f"Throughput: {throughput}")
    print("Latency:")
    print(latency(df))
    print("Inter-arrivial times for {} =".format(filepath))
    print(interarrivial(df))
