#!/usr/bin/env python3

import sys
import pandas as pd

def latency(df):
    df = df['End'] - df['Cli_start']
    return df.describe(percentiles=[.25,.50,.75,.99],include='all')

for filepath in sys.argv[1:]:

    df = pd.read_json(path_or_buf=filepath, orient='records')

    length = df['End'].max() - df['End'].min()
    throughput = len(df['End']) / length
    print("Throughput for {} = {}".format(filepath, throughput))
    print("Latency for {} =".format(filepath))
    print(latency(df))
