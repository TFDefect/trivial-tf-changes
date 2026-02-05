
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from scripts.collect_metrics import collect_metrics

target_commit = "b7a5df34ec7e520db89e213d72599bf905262ae9"
print(f"Running JIT for {target_commit}...")
try:
    collect_metrics(os.getcwd(), target_commit=target_commit)
    print("Execution finished.")
except Exception as e:
    print(f"Execution failed: {e}")

if os.path.exists("metrics.csv"):
    print("metrics.csv found. Content:")
    with open("metrics.csv", "r", encoding="utf-8") as f:
        print(f.read())
else:
    print("metrics.csv NOT found.")
