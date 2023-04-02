#!/usr/bin/env python3
"""
Unit tests for the nestile NES Tile Editor
"""

import unittest
from nestile import Tile

class TestNesTileEditor(unittest.TestCase):
    """Class containing the method to unit test nestile"""

    def test_tile_serialization(self):
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
        self.assertEqual(base_bytes, gen_bytes)
        sec_tile = Tile(gen_bytes)
        print (sec_tile)
        self.assertEqual(first_tile, sec_tile)
        gen_str=repr(first_tile)
        print (gen_str)
        tile3=Tile(gen_str)
        self.assertEqual(first_tile, tile3)
        tile4=Tile(first_tile)
        self.assertEqual(first_tile, tile4)
        tile4.set(7,7,3-tile4.get(7,7))
        print (tile4)
        self.assertNotEqual(first_tile, tile4)
        tile4.set(7,7,3-tile4.get(7,7))
        self.assertEqual(first_tile, tile4)


    def test_tile_edits(self):
        """
        Shifts tile around and makes sure we ge back to start
        """
        base_bytes = b"\x41\xC2\x44\x48\x10\x20\x40\x80\x01\x02\x04\x08\x16\x21\x42\x87"
        first_tile = Tile().frombytes(base_bytes)
        print (first_tile)
        tile4=Tile(first_tile)
        self.assertEqual(first_tile, tile4)
        tile4.invert()
        print ("Invert")
        print (tile4)
        tile4.shift_up()
        print ("shift_up")
        print (tile4)
        tile4.shift_right()
        print ("shift_right")
        print (tile4)
        tile4.invert()
        print ("invert")
        print (tile4)
        tile4.shift_left()
        print ("shift_left")
        print (tile4)
        tile4.shift_down()
        print ("shift_down")
        print (tile4)
        self.assertEqual(first_tile, tile4)


if __name__ == '__main__':
    unittest.main()
