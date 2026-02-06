
import csv
import os

file_path = "metrics.csv"
if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        print("Found Headers:")
        delta_headers = [h for h in headers if h.endswith('_delta')]
        print(f"Delta Headers: {delta_headers}")
        
        # Print first row data for delta columns
        try:
            row = next(reader)
            print("Row Values for Deltas:")
            for h in delta_headers:
                idx = headers.index(h)
                print(f" - {h}: {row[idx]}")
        except StopIteration:
            print("No data rows found.")
else:
    print("metrics.csv NOT found.")
