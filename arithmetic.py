import argparse
import json
import heapq
from pathlib import Path
from collections import defaultdict, Counter
import time
import os
from bitarray import bitarray

class ArithmeticCoding:
    def __init__(self, data):
        self.data = data
        self.frequencies = self.build_frequency_table()
        self.original_size = len(data)
        self.probs = {byte: freq / self.original_size for byte, freq in self.frequencies.items()}
        self.unique_chars = list(self.frequencies.keys())

    def encode(self):
        bits = bitarray()

        lower_limit = 0.0
        upper_limit = 1.0

        interval = self.get_interval(lower_limit, upper_limit)

        for byte in self.data:
            diff = upper_limit - lower_limit
            upper_limit = lower_limit + diff * interval[byte][1]
            lower_limit = lower_limit + diff * interval[byte][0]

        # binarization
        while upper_limit < 0.5 or lower_limit > 0.5: 
            if lower_limit > 0.5:
                bits.append(True)
                lower_limit = 2 * (lower_limit - 0.5)
                upper_limit = 2 * (upper_limit - 0.5)
            elif upper_limit < 0.5:
                bits.append(False)
                lower_limit *= 2
                upper_limit *= 2
        
        rem_bits = 0
        while upper_limit < 0.75 and lower_limit > 0.25:
            rem_bits += 1
            lower_limit = 2 * (lower_limit - 0.25)
            upper_limit = 2 * (upper_limit - 0.25)

        rem_bits += 1
        if lower_limit <= 0.25:
            bits.append(False)
            for _ in range(rem_bits):
                bits.append(True)
        else:
            bits.append(True)
            for _ in range(rem_bits):
                bits.append(False)

        
    def get_interval(self, lower_limit, upper_limit):
        diff = upper_limit - lower_limit
        interval = dict()
        
        for char in self.unique_chars:
            upper_limit = diff * self.probs[char]
            interval[char] = (lower_limit, upper_limit)
            lower_limit = upper_limit

        return interval


    def decode(self, tag):
        pass

    def build_frequency_table(self):
        frequencies = Counter(self.data)
        return dict(frequencies)
