import subprocess
import os
import filecmp
import re
import csv

# Compression tool configs
algorithms = {
    "huffman": {"script": "huffman.py", "ext": ".huff"},
    "arithmetic": {"script": "arithmetic.py", "ext": ".arith"},
    "lzw": {"script": "lzw.py", "ext": ".lzw"},
}

test_dir = "test_files\\uniform"
results = []

def run_and_capture(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running command:", cmd)
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
        result.check_returncode()  # raises exception
    return result.stdout


def parse_output(output):
    """Extract time and compression ratio from stdout"""
    time_match = re.search(r"Time taken:\s*([\d.]+)", output)
    ratio_match = re.search(r"Compression ratio:\s*([\d.]+)", output)
    return (
        float(time_match.group(1)) if time_match else -1,
        float(ratio_match.group(1)) if ratio_match else -1,
    )

def evaluate():
    file_path = test_dir
    for filename in os.listdir(file_path):
        print(filename)
        input_path = os.path.join(file_path, filename)
        for algo, config in algorithms.items():
            filename_without_ext = os.path.splitext(filename)[0]
            compressed = f"{filename_without_ext}_{algo}{config['ext']}"
            decompressed = f"{filename_without_ext}_{algo}_decoded.txt"

            print(f"Testing {algo} on {filename} {compressed}")

            # Compress
            comp_cmd = f"python {config['script']} compress {input_path} {compressed}"
            comp_out = run_and_capture(comp_cmd)
            comp_time, ratio = parse_output(comp_out)

            # Decompress
            decomp_cmd = f"python {config['script']} decompress {compressed} {decompressed}"
            decomp_out = run_and_capture(decomp_cmd)
            time_match = re.search(r"Time taken:\s*([\d.]+)", decomp_out)
            decomp_time=float(time_match.group(1)) if time_match else -1
            correct = filecmp.cmp(input_path, decompressed, shallow=False)

            results.append({
                "file": filename,
                "algorithm": algo,
                "compression_time": comp_time,
                "decompression_time": decomp_time,
                "compression_ratio": ratio,
                "correct": correct,
            })

            # Clean up
            os.remove(compressed)
            os.remove(decompressed)

def save_results():
    with open("results_uniform.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

if __name__ == "__main__":
    evaluate()
    save_results()
    print("✓ Evaluation complete. Results saved to results.csv")
