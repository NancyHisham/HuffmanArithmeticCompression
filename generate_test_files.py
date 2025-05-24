import os
import random
from pathlib import Path

# Define base output directory
base_dir = Path("test_files")
base_dir.mkdir(exist_ok=True)

# Character distributions to simulate different file types
charsets = {
    "uniform": [chr(i) for i in range(32, 127)],  # All printable ASCII characters
    "skewed": ["a"] * 90 + ["b"] * 5 + ["c"] * 3 + ["d"] * 2,  # Mostly 'a'
    "binary_like": ["0", "1"],  # Binary-like data
    "text_heavy": list("ETAOINSHRDLU") * 10 + list("etaoinshrdlu") * 5 + [" "] * 20,  # Frequent English chars
}

# File sizes to generate (in kilobytes and megabytes)
sizes_bytes = [
    1 * 1024,            # 1 KB
    10 * 1024,           # 10 KB
    100 * 1024,          # 100 KB
    1 * 1024 * 1024,     # 1 MB
    10 * 1024 * 1024,    # 10 MB
    100 * 1024 * 1024    # 100 MB
]

# Function to generate file content
def generate_content(charset, size_bytes):
    return ''.join(random.choices(charset, k=size_bytes))

# Generate files
for dist_name, charset in charsets.items():
    dist_dir = base_dir / dist_name
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    for size_bytes in sizes_bytes:
        size_label = (
            f"{size_bytes // 1024}KB" if size_bytes < 1024 * 1024
            else f"{size_bytes // (1024 * 1024)}MB"
        )
        file_name = f"{dist_name}_{size_label}.txt"
        file_path = dist_dir / file_name
        
        print(f"Generating {file_name} ...")
        content = generate_content(charset, size_bytes)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

print("✅ All test files generated at:", base_dir.resolve())
