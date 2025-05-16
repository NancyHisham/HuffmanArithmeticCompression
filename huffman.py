import argparse
import json
import heapq
from pathlib import Path
from collections import defaultdict
import time
import os

class HuffmanNode:
    def __init__(self, char=None, freq=0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_frequency_table(data):
    freq = defaultdict(int)
    for symbol in data:
        freq[symbol] += 1
    return dict(freq)

def build_huffman_tree(freq_table):
    heap = [HuffmanNode(char, freq) for char, freq in freq_table.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
        merged = HuffmanNode(None, node1.freq + node2.freq)
        merged.left = node1
        merged.right = node2
        heapq.heappush(heap, merged)
    return heap[0]

def generate_codes(node, prefix="", code_map=None):
    if code_map is None:
        code_map = {}
    if node.char is not None:
        code_map[node.char] = prefix
    else:
        generate_codes(node.left, prefix + "0", code_map)
        generate_codes(node.right, prefix + "1", code_map)
    return code_map

def encode_data(data, code_map):
    return ''.join(code_map[byte] for byte in data)

def pad_encoded_data(encoded_data):
    extra_padding = 8 - len(encoded_data) % 8
    if extra_padding == 8:
        extra_padding = 0
    padded = encoded_data + '0' * extra_padding
    return padded, extra_padding

def get_byte_array(bitstring):
    return bytearray(int(bitstring[i:i+8], 2) for i in range(0, len(bitstring), 8))

def rebuild_tree_from_code_map(code_map):
    root = {}
    for k, v in code_map.items():
        node = root
        for bit in v:
            node = node.setdefault(bit, {})
        node['char'] = int(k)
    return root

def decode_bits(bitstring, tree):
    decoded_bytes = bytearray()
    node = tree
    for bit in bitstring:
        node = node[bit]
        if 'char' in node:
            decoded_bytes.append(node['char'])
            node = tree
    return bytes(decoded_bytes)

def compress(input_path, output_path):
    start_time = time.time()
    data = Path(input_path).read_bytes()
    original_size = len(data)

    freq_table = build_frequency_table(data)
    root = build_huffman_tree(freq_table)
    code_map = generate_codes(root)
    encoded = encode_data(data, code_map)
    padded, padding = pad_encoded_data(encoded)
    byte_array = get_byte_array(padded)

    metadata = {
        'code_map': {str(k): v for k, v in code_map.items()},
        'padding': padding
    }

    with open(output_path, 'wb') as f:
        header = json.dumps(metadata).encode()
        f.write(len(header).to_bytes(4, 'big'))  # Write 4-byte header size
        f.write(header)
        f.write(byte_array)

    end_time = time.time()
    compressed_size = os.path.getsize(output_path)

    compression_ratio = original_size / compressed_size if compressed_size != 0 else 0

    print(f"Compressed '{input_path}' ➜ '{output_path}'")
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print(f"Original size: {original_size} bytes")
    print(f"Compressed size: {compressed_size} bytes")
    print(f"diff in size: {original_size - compressed_size} bytes")
    print(f"Compression ratio: {compression_ratio:.2f}")

def decompress(input_path, output_path):
    start_time = time.time()

    with open(input_path, 'rb') as f:
        header_size = int.from_bytes(f.read(4), 'big')
        header = json.loads(f.read(header_size))
        code_map = header['code_map']
        padding = header['padding']
        data = f.read()

    bitstring = ''.join(f'{byte:08b}' for byte in data)
    bitstring = bitstring[:-padding] if padding else bitstring

    tree = rebuild_tree_from_code_map(code_map)
    decoded = decode_bits(bitstring, tree)

    with open(output_path, 'wb') as f:
        f.write(decoded)

    end_time = time.time()

    print(f"Decompressed '{input_path}' ➜ '{output_path}'")
    print(f"Time taken: {end_time - start_time:.4f} seconds")
    print(f"Decompressed size: {len(decoded)} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Huffman Compression Tool")
    parser.add_argument("mode", choices=["compress", "decompress"], help="Mode of operation")
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path (.huff for compress, original ext for decompress)")

    args = parser.parse_args()

    if args.mode == "compress":
        compress(args.input, args.output)
    else:
        decompress(args.input, args.output)