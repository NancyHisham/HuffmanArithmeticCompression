import time
import os
import argparse

class LZWCompressor:
    def __init__(self, max_dict_size=65535):
        self.max_dict_size = max_dict_size # 2^16-1 --> 16 bits needed ~ 2 bytes


    def lzw_compress(self, input_path, output_path):
        start_time = time.time()
        dictionary = {bytes([i]): i for i in range(256)}
        dict_size = 256
        
        with open(input_path, 'rb') as infile, \
        open(output_path, 'wb') as outfile:
            w = b""
            while True:
                c = infile.read(1)
                if not c:
                    break

                wc = w + c
                if wc in dictionary:
                    w = wc
                else:
                    outfile.write(dictionary[w].to_bytes(2, 'big'))
                    if dict_size < self.max_dict_size:
                        dictionary[wc] = dict_size
                        dict_size += 1
                    w = c

            if w: # to account for the last word if not written
                outfile.write(dictionary[w].to_bytes(2, 'big'))

        end_time = time.time()
        diff = end_time - start_time
        org_size = os.path.getsize(input_path)
        comp_size = os.path.getsize(output_path)
        ratio = (org_size / comp_size) if comp_size > 0 else 0 

        print(f"Compressed '{input_path}' : '{output_path}'")
        print(f"Time taken: {diff:.4f} seconds")
        print(f"Original size: {org_size} bytes")
        print(f"Compressed size: {comp_size} bytes")
        print(f"diff in size: {org_size - comp_size} bytes")
        print(f"Compression ratio: {ratio:.2f}")


    def lzw_decompress(self, input_path, output_path):
        start_time = time.time()
        dictionary = {i: bytes([i]) for i in range(256)}
        dict_size = 256
        total_bytes_written = 0  # Track decompressed size

        with open(input_path, 'rb') as infile, \
            open(output_path, 'wb') as outfile:
            
            data = infile.read()
            if len(data) < 2: # because we saved the int into 2 bytes
                return

            # Read 2 bytes at a time and convert to integer
            codes = [int.from_bytes(data[i:i+2], 'big') for i in range(0, len(data), 2)]
            
            # print(f'{codes=}')
            
            w = dictionary[codes[0]]
            outfile.write(w)
            total_bytes_written += len(w)

            for k in codes[1:]:
                if k in dictionary:
                    entry = dictionary[k]
                elif k == dict_size: # Special case: current code is not in dictionary yet
                    entry = w + w[0:1]
                else:
                    raise ValueError(f"Invalid compressed code: {k}")

                outfile.write(entry)

                if dict_size < self.max_dict_size:
                    # add new word in dictionary
                    dictionary[dict_size] = w + entry[0:1] # entry[0:1] is the first char
                    dict_size += 1
                w = entry

        end_time = time.time()
        diff = end_time - start_time
        print(f"Decompressed '{input_path}' : '{output_path}'")
        print(f"Time taken: {diff:.4f} seconds")
        print(f"Decompressed size: {total_bytes_written} bytes")

    def verify(self, original_path, decompressed_path):
        with open(original_path, 'rb') as f1, open(decompressed_path, 'rb') as f2:
            if f1.read() == f2.read():
                print("====== Original and Decompressed files are EQUAL! ======")
            else:
                print("Files are different")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["compress", "decompress"], help="Mode")
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")

    args = parser.parse_args()
    lzw = LZWCompressor()

    if args.mode == "compress":
        lzw.lzw_compress(args.input, args.output)
    else:
        lzw.lzw_decompress(args.input, args.output)
