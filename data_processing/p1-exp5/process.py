import pandas as pd

# Load the CSV file
df = pd.read_csv("S3_S4_no_colocation.csv")

# Calculate averages
avg_fetch_time = df["fetch_time"].mean()
avg_response_size = df["response_size"].mean()

print(f"Average Fetch Time: {avg_fetch_time:.2f} seconds")
print(f"Average Response Size: {avg_response_size:.2f} bytes")
