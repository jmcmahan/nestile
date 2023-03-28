#!/usr/bin/env python3
"""
Unit tests for the nestile NES Tile Editor
"""

from nestile import Tile

def unittest():
    """
    Example from https://www.nesdev.org/wiki/PPU_pattern_tables
    b"\x41\xC2\x44\x48\x10\x20\x40\x80\x01\x02\x04\x08\x16\x21\x42\x87"
    [[0, 1, 0, 0, 0, 0, 0, 3],     # .1.....3
     [1, 1, 0, 0, 0, 0, 3, 0],     # 11....3.
     [0, 1, 0, 0, 0, 3, 0, 0],     # .1...3..
     [0, 1, 0, 0, 3, 0, 0, 0],     # .1..3...
     [0, 0, 0, 3, 0, 2, 2, 0],     # ...3.22.
     [0, 0, 3, 0, 0, 0, 0, 2],     # ..3....2
     [0, 3, 0, 0, 0, 0, 2, 0],     # .3....2.
     [3, 0, 0, 0, 0, 2, 2, 2]]     # 3....222
    """
    base_bytes = b"\x41\xC2\x44\x48\x10\x20\x40\x80\x01\x02\x04\x08\x16\x21\x42\x87"
    print (base_bytes)
    first_tile = Tile().frombytes(base_bytes)
    print (first_tile)
    gen_bytes = first_tile.tobytes()
    print (gen_bytes)
    print(base_bytes == gen_bytes)
    sec_tile = Tile().frombytes(gen_bytes)
    print (sec_tile)
    print(first_tile == sec_tile)

# Main program loop
if __name__ == "__main__":
    unittest()
