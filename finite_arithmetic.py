import argparse
import json
import heapq
from pathlib import Path
from collections import defaultdict, Counter
import time
import os
from bitarray import bitarray


class ArithmeticCodingEncoder:
    def __init__(self, input_path, precision=16):
        self.input_path = input_path
        self.data = Path(input_path).read_bytes()
        self.num_bytes = len(self.data)
        self.frequencies = self.build_frequency_table()
        self.probs = {byte: freq / self.num_bytes for byte, freq in self.frequencies.items()}
        self.unique_chars = sorted(self.frequencies.keys())
        self.cum_freq = self.build_cumulative_freq_table()
        self.output_path = input_path + ".arith"
        self.precision = precision

    def encode(self):
        bits = bitarray()
        whole = 1 << self.precision        # 2^32
        half = whole >> 1             # 2^31
        quarter = whole >> 2          # 2^30

        lower_limit = 0
        upper_limit = whole
        rem_bits = 0

        start_time = time.time()
        for byte in self.data:
            range_ = upper_limit - lower_limit
            sym_low, sym_high = self.cum_freq[byte]
            total = self.total_freq

            upper_limit = lower_limit + (range_ * sym_high) // total
            lower_limit = lower_limit + (range_ * sym_low) // total

            # rescaling
            while upper_limit < half or lower_limit > half: 
                if lower_limit > half:
                    self.output_bit(bits, 1)
                    for _ in range(rem_bits):
                        self.output_bit(bits, 0)
                    lower_limit = (lower_limit - half) << 1
                    upper_limit = ((upper_limit - half) << 1)
                    rem_bits = 0
                elif upper_limit < half:
                    self.output_bit(bits, 0)
                    for _ in range(rem_bits):
                        self.output_bit(bits, 1)
                    lower_limit <<= 1
                    upper_limit <<= 1
                    rem_bits = 0
            
            while upper_limit < 3*quarter and lower_limit > quarter:
                rem_bits += 1
                lower_limit = 2 * (lower_limit - quarter)
                upper_limit = 2 * (upper_limit - quarter)

        rem_bits += 1
        if lower_limit <= quarter:
            self.output_bit(bits, 0)
            for _ in range(rem_bits):
                self.output_bit(bits, 1)
        else:
            self.output_bit(bits, 1)
            for _ in range(rem_bits):
                self.output_bit(bits, 0)


        with open(self.output_path, 'wb') as f:
            num_symbols = len(self.unique_chars)
            f.write(num_symbols.to_bytes(2, 'big'))
            for byte, freq in self.frequencies.items():
                f.write(bytes([byte]))              # 1 byte
                f.write(freq.to_bytes(4, 'big'))    # 4 bytes
            f.write(self.num_bytes.to_bytes(4, 'big'))
            f.write(bits)

        end_time = time.time()
        original_size = self.num_bytes
        compressed_size = os.path.getsize(self.output_path)

        compression_ratio = original_size / compressed_size if compressed_size != 0 else 0

        print(f"Compressed '{self.input_path}' ➜ '{self.output_path}'")
        print(f"Time taken: {end_time - start_time:.4f} seconds")
        print(f"Original size: {original_size} bytes")
        print(f"Compressed size: {compressed_size} bytes")
        print(f"diff in size: {original_size - compressed_size} bytes")
        print(f"Compression ratio: {compression_ratio:.2f}")


    def build_frequency_table(self):
        frequencies = Counter(self.data)
        return dict(frequencies)

    def build_cumulative_freq_table(self):
        cum_freq = {}
        total = 0
        for char in self.unique_chars:
            cum_freq[char] = (total, total + self.frequencies[char])
            total += self.frequencies[char]
        self.total_freq = total
        return cum_freq
    
    def output_bit(self, bits, value):
        bits.append(bool(value))

class ArithmeticCodingDecoder:
    def __init__(self, input_path, precision=16):
        self.frequencies, self.num_bytes, self.data = self.read_file(input_path)
        self.unique_chars = sorted(self.frequencies.keys())
        self.cum_freq = self.build_cumulative_freq_table()
        split_tup = os.path.splitext(input_path)
        self.output_path = os.path.join("output", split_tup[0])
        self.precision = precision

    def decode(self):
        bits = bitarray()
        bits.frombytes(self.data)
        whole = 1 << self.precision        # 2^32
        half = whole >> 1             # 2^31
        quarter = whole >> 2          # 2^30

        lower_limit = 0
        upper_limit = whole

        start_time = time.time()

        i = 1
        tag = 0
        while i <= self.precision and i <= len(bits):
            if bits[i-1] == 1:
                tag += 1 << (self.precision - i)
            i += 1

        output = bytearray()
        total = self.total_freq
        n = 0

        while True:
            range_ = upper_limit - lower_limit

            for char in self.unique_chars:
                sym_low, sym_high = self.cum_freq[char]

                upper_temp = lower_limit + (range_ * sym_high) // total
                lower_temp = lower_limit + (range_ * sym_low) // total

                if lower_temp <= tag < upper_temp:
                    output.append(char)
                    lower_limit = lower_temp
                    upper_limit = upper_temp
                    n += 1
                    break  # move to next symbol
            else:
                # No matching symbol found; input is malformed
                raise ValueError("Failed to decode: No interval matched tag")

            if n >= self.num_bytes:
                break
            
            # rescaling
            while upper_limit < half or lower_limit > half: 
                if lower_limit > half:
                    lower_limit = (lower_limit - half) << 1
                    upper_limit = (upper_limit - half) << 1
                    tag = (tag - half) << 1
                elif upper_limit < half:
                    lower_limit <<= 1
                    upper_limit <<= 1
                    tag <<= 1
                if i <= len(bits):
                    if bits[i-1] == 1:
                        tag += 1
                    i += 1

            while upper_limit < 3*quarter and lower_limit > quarter:
                lower_limit = 2 * (lower_limit - quarter)
                upper_limit = 2 * (upper_limit - quarter)
                tag = 2 * (tag - quarter)
                if i <= len(bits):
                    if bits[i-1] == 1:
                        tag += 1 
                    i += 1

        with open(self.output_path, 'wb') as f:
            f.write(output)

        end_time = time.time()

        print(f"Time taken: {end_time - start_time:.4f} seconds")
        print(f"Decompressed size: {len(output)} bytes")

    def build_cumulative_freq_table(self):
        cum_freq = {}
        total = 0
        for char in self.unique_chars:
            cum_freq[char] = (total, total + self.frequencies[char])
            total += self.frequencies[char]
        self.total_freq = total
        return cum_freq

    def read_file(self, file_path):
        frequency_table = {}
        with open(file_path, 'rb') as f:
            num_symbols = int.from_bytes(f.read(2), 'big')
            for _ in range(num_symbols):
                byte = f.read(1)[0]  # single byte
                freq = int.from_bytes(f.read(4), 'big')
                frequency_table[byte] = freq
            num_bytes = int.from_bytes(f.read(4), 'big')
            data = f.read()
        return frequency_table, num_bytes, data
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arithmetic Coding Compression Tool")
    parser.add_argument("mode", choices=["compress", "decompress"], help="Mode of operation")
    parser.add_argument("input", help="Input file path")
    parser.add_argument("--precision", type=int, default=16, help="Compression precision (default: 16)")

    args = parser.parse_args()

    if args.mode == "compress":
        encoder = ArithmeticCodingEncoder(args.input, args.precision)
        encoder.encode()
    else:
        decoder = ArithmeticCodingDecoder(args.input, args.precision)
        decoder.decode()
