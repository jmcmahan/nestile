#!/usr/bin/env python3

# NES Tile Editor
# A program for creating and editing graphics for NES programs
# Author: Jerry McMahan Jr. (ported to python3 and tkinter by Theodore Kotz)
# Version: 0.3.0
# See changes.txt for changes and version info

from collections import namedtuple
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
import os
import sys
import tkinter as tk

#Size of a Tile
TILESIZE=8
BYTES_PER_TILE=16

# ROM Sizes
CROM_INC = 8192
PROM_INC = 16384
INES_HEADER_SIZE = 16
INES_HEADER_PROMS_IDX=4
INES_HEADER_CROMS_IDX=5

#Size of Tile Editor Window
EDITSCALE=32
EDIT_WIDTH=TILESIZE*EDITSCALE
EDIT_HEIGHT=EDIT_WIDTH

#Size of Color Selector
COLORS_SPAN=4
COLORS_BOXSIZE=EDIT_WIDTH//COLORS_SPAN
COLORS_WIDTH=EDIT_WIDTH
COLORS_HEIGHT=COLORS_BOXSIZE

#Size of Tile Set Window
TSET_SCALE=3
TSET_SPAN=16
TSET_OFFSET=TILESIZE*TSET_SCALE
TSET_WIDTH=TSET_OFFSET*TSET_SPAN
TSET_HEIGHT=(TSET_OFFSET * CROM_INC) // (TSET_SPAN * BYTES_PER_TILE)

#size of Tile Layout Window
TLAYOUT_SCALE=3
TLAYOUT_XSPAN=32
TLAYOUT_YSPAN=30
TLAYOUT_OFFSET=TILESIZE*TLAYOUT_SCALE
TLAYOUT_WIDTH=TLAYOUT_XSPAN*TLAYOUT_OFFSET
TLAYOUT_HEIGHT=TLAYOUT_YSPAN*TLAYOUT_OFFSET

#size of Palette seleection Window
PALETTE_BOXSIZE=16
PALETTE_SPAN=16



nes_palette = (
    "#808080", "#0000bb", "#3700bf", "#8400a6",
    "#bb006a", "#b7001e", "#b30000", "#912600",
    "#7b2b00", "#003e00", "#00480d", "#003c22",
    "#002f66", "#000000", "#050505", "#050505",

    "#c8c8c8", "#0059ff", "#443cff", "#b733cc",
    "#ff33aa", "#ff375e", "#ff371a", "#d54b00",
    "#c46200", "#3c7b00", "#1e8415", "#009566",
    "#0084c4", "#111111", "#090909", "#090909",

    "#ffffff", "#0095ff", "#6f84ff", "#d56fff",
    "#ff77cc", "#ff6f99", "#ff7b59", "#ff915f",
    "#ffa233", "#a6bf00", "#51d96a", "#4dd5ae",
    "#00d9ff", "#666666", "#0d0d0d", "#0d0d0d",

    "#ffffff", "#84bfff", "#bbbbff", "#d0bbff",
    "#ffbfea", "#ffbfcc", "#ffc4b7", "#ffccae",
    "#ffd9a2", "#cce199", "#aeeeb7", "#aaf7ee",
    "#b3eeff", "#dddddd", "#111111", "#111111")

tileset_palette = (
    "#000000", "#00FFFF", "#FF00FF", "#FFFF00")

nes_filetypes = (
    ('Raw files', '.*'), ('NES files', '.nes'))

def box_number(x, y, scale, row_span):
    """
    Finds the box number which contains the coordinates (x,y).
    Assumes rectangle is split up into boxes each of size x_len> by y_len,
    the boxes are numbered 0 through box_num starting at the upper left
    corner of the rectangle, and row_span boxes in a row.

    Returns the box number which contains the coordinates x, y
    """
    return (x // scale) + row_span * (y // scale)


class Tile:
    def __init__(self):
        """
        Initialize class variables
        """
        self._pixels = None

    def set(self, x: int, y: int, value: int ):
        if self._pixels is None:
            self._pixels = [[0]*TILESIZE for _ in range(TILESIZE)]
        self._pixels[y][x]=value

    def get(self, x: int, y: int ) -> int:
        if self._pixels is None:
            return 0
        return self._pixels[y][x]

    #def __iter__(self):
    #    if self._pixels is None:
    #        return iter([[0]*TILESIZE for _ in range(TILESIZE)])
    #    return iter(self._pixels)

    def __repr__(self):
        if self._pixels is None:
            return "None"
        return f"{type(self).__name__}\n\t"+"\n\t".join( str(row) for row in self._pixels)

    def __eq__(self, value):
        if self._pixels is None:
            return value==[[0]*TILESIZE for _ in range(TILESIZE)]
        return value==self._pixels

    def tobytes(self) ->  bytes:
        """
        Given a tile in the form of 8x8 list or palette indexes
        returns a string or bytes containing raw NES graphics data (in binary),
        """
        if self._pixels is None:
            return b"\0" * BYTES_PER_TILE
        hi_data = bytearray(b"")
        lo_data = bytearray(b"")
        for row in self._pixels:
            hi_bits = 0
            lo_bits = 0
            for col in row:
                hi_bits = (hi_bits << 1)+((col >> 1) & 1)
                lo_bits = (lo_bits << 1)+(col & 1)
            hi_data.append(hi_bits)
            lo_data.append(lo_bits)
        return lo_data + hi_data

    def frombytes(self, data:bytes):
        """
        Given a string of bytes containing raw NES graphics data (in binary),
        returns a tile in the form of 8x8 list or palette indexes
        """
        if (b"\0" * BYTES_PER_TILE) == data[0:BYTES_PER_TILE]:
            self._pixels = None
            return self
        self._pixels = []
        for y in range(TILESIZE):
            hi_bits = (data[y+8] << 1)
            lo_bits = data[y]
            self._pixels.append( [ ((hi_bits >> (i)) & 2) + ((lo_bits >> (i)) & 1)
                                  for i in range(7,-1,-1) ] )
        return self

    def draw(self,
             draw: "Func(start_x:int, start_y:int, stop_x:int, stop_y:int, 'Color')",
             pal: list['Color']):
        if self._pixels is None:
            draw(0, 0, TILESIZE, TILESIZE, pal[0])
            return
        for y, row in enumerate(self._pixels):
            for x, pixel in enumerate(row):
                draw(x, y, x+1, y+1, pal[pixel])


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


class TileSet:
    def __init__(self, rom_size=CROM_INC, filename=None):
        """
        Initialize class variables
        """
        if filename is not None:
            if os.path.isfile(filename):
                self.do_open( filename )
                return
            self.filename = filename
        else:
            self.filename = ''
        self.chr_rom_size = rom_size
        self.file_format = 'raw'
        self.modified = False
        # Holds iNES PRG and header data when opening iNES ROM's
        self.ines_data = None
        # Holds the tile bitmaps as 'Tile's
        self.tile_data = [Tile() for _ in range(self.chr_rom_size//BYTES_PER_TILE)]

    def reset(self):
        """
        Reinitialize class variables
        except data size is kept
        """
        self.filename = ''
        self.file_format = 'raw'
        self.modified = False
        # Holds iNES PRG and header data when opening iNES ROM's
        self.ines_data = None
        # Holds the tile bitmaps as 'Tile's
        self.tile_data = [Tile() for _ in range(self.chr_rom_size//BYTES_PER_TILE)]

    # File I/O functions

    def do_save(self, filename: str):
        """
        Saves the tile data to the file at filename
        """
        # Later, try to differentiate between different file formats here
        # but just treat everything like a raw binary file for now
        output_string = b"".join([tile.tobytes() for tile in self.tile_data ])

        with open(filename, 'wb') as fout:
            if self.file_format == 'raw':
                fout.write(output_string)
            elif self.file_format == 'ines':
                fout.write(self.ines_data + output_string)
            self.modified = False
            self.filename = filename


    def do_open(self, filename: str):
        """
        Reads the tile data from the file at filename
        """
        self.filename = filename
        with open(self.filename, 'rb') as fin:
            fdata = fin.read()

        if self.filename.split('.')[-1] == 'nes' and len(fdata) >= INES_HEADER_SIZE:
            self.file_format = 'ines'
            proms = fdata[INES_HEADER_PROMS_IDX]
            croms = fdata[INES_HEADER_CROMS_IDX]
            prom_size = INES_HEADER_SIZE + PROM_INC * proms
            self.chr_rom_size = CROM_INC * croms
            self.ines_data = fdata[0: prom_size]
            fdata = fdata[prom_size: prom_size + self.chr_rom_size]
        else:
            self.file_format = 'raw'
            self.ines_data = None
            # if not iNES, make sure data length is a multiple of 8192
            if len(fdata) % CROM_INC == 0:
                self.chr_rom_size = len(fdata)
            else:
                fdata = fdata + (CROM_INC - (len(fdata) % CROM_INC)) * b'\0'
                self.chr_rom_size = CROM_INC * (int(len(fdata) / CROM_INC) + 1)

        if len(fdata) < self.chr_rom_size:
            self.chr_rom_size = len(fdata)

        self.tile_data = [Tile().frombytes( fdata[i*BYTES_PER_TILE:(i+1)*BYTES_PER_TILE] )
                          for i in range(0, len(fdata)//BYTES_PER_TILE) ]
        self.modified = False


    def update_tile_pixel(self, idx, x, y, color):
        self.modified = True
        self.tile_data[idx].set(x,y,color)


    def __getitem__(self, key):
        return self.tile_data[key]

    #def __delitem__(self, key):
    #    del self.tile_data[key]

    #def __setitem__(self, key, value):
    #    self.tile_data[key]=value

    def __iter__(self):
        return iter(self.tile_data)

    def __len__(self):
        return len(self.tile_data)

    def __repr__(self):
        line = "\n---------------------------------------------------------"
        return f"{type(self).__name__}\n"+"\n".join( str(row)+line for row in self.tile_data)

class TileLayerEntry(namedtuple('TileLayerEntry', ['tile', 'palette'])):
    __slots__ = ()

class TileLayout(namedtuple('TileLayout', ['x', 'y', 'palette'])):
    __slots__ = ()

class TileLayerData:
    def __init__(self):
        """
        Initialize class variables
        """
        self.filename = ''
        self.modified = False
        # Holds information for drawing tiles on the tile layer
        # Initialize tile map
        self._tile_at_xy = [ TLAYOUT_YSPAN*[None] for _ in range(TLAYOUT_XSPAN) ]

    def reset(self):
        """
        reinitialize class variables
        """
        self.filename = ''
        self.modified = False
        # Holds information for drawing tiles on the tile layer
        # Initialize tile map
        self._tile_at_xy = [ TLAYOUT_YSPAN*[None] for _ in range(TLAYOUT_XSPAN) ]

    def tile_layout(self, tile_num: int) -> list([int, int, 'pallet']):
        return [TileLayout(x, y, data.palette)
                for x, col in enumerate(self._tile_at_xy)
                for y, data in enumerate(col)
                if data is not None and tile_num==data.tile ]


    def lay_tile(self, col: int, row: int, tile_num: int, pal: list[int]):
        self.modified = True
        self._tile_at_xy[col][row] = TileLayerEntry(tile_num, pal[:])

    def tile_at_xy(self, col: int, row: int):
        tle = self._tile_at_xy[col][row]
        if tle is None:
            return 0
        return tle.tile

class NesTileEditTk:
    def __init__(self, event_map: 'NesTileEdit'):
        """
        Initialize class variables
        """
        # Create widgets
        self.event_map = event_map
        self.root = tk.Tk()
        self.main_win = self.root
        self.tileset_pixmap = tk.Canvas(self.main_win)
        scroll_y = ttk.Scrollbar(self.main_win, orient="vertical",
                                 command=self.tileset_pixmap.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        self.tileset_pixmap.configure(yscrollcommand=scroll_y.set)

        self.edit_win = tk.Toplevel(self.root)
        self.edit_pixmap = tk.Canvas(self.edit_win)
        self.colors_pixmap = tk.Canvas(self.edit_win)

        self.tlayout_win = tk.Toplevel(self.root)
        self.tlayout_pixmap = tk.Canvas(self.tlayout_win)

        # Setup user interface
        self._setup_ui(event_map)
        self._build_menu(event_map)

    def _setup_ui(self, event_map: 'NesTileEdit'):
        """
        Set widget properties
        Widget arrangement and display
        Setup events / signals
        """
        self.main_win.wm_title('Tile Set')
        self.main_win.geometry(str(TSET_WIDTH+24)+'x'+str(TSET_HEIGHT+2))
        self.main_win.resizable(False, False)
        self.main_win.protocol("WM_DELETE_WINDOW", event_map.destroy)
        self.tileset_pixmap.config(bg='#FF0000', width=TSET_WIDTH, height= TSET_HEIGHT)
        self.tileset_pixmap.grid(row=0, column=0)
        self.tileset_pixmap.bind("<Button-1>", self._tileset_click)
        self.tileset_pixmap.bind("<Button-4>", self._tileset_mousewheel)
        self.tileset_pixmap.bind("<Button-5>", self._tileset_mousewheel)

        self.edit_win.wm_title('Tile #') #TKOTZ + str(self.current_tile_num))
        self.edit_win.geometry(str(EDIT_WIDTH+2)+'x'+str(EDIT_HEIGHT+COLORS_HEIGHT+4))
        self.edit_win.resizable(False, False)
        self.edit_win.protocol("WM_DELETE_WINDOW", event_map.destroy)
        self.edit_pixmap.config(width=EDIT_WIDTH, height=EDIT_HEIGHT, bg='#FF0000')
        self.edit_pixmap.grid(column=0, row=0, sticky="new")
        self.edit_pixmap.bind("<Button-1>", self._edit_leftclick)
        self.edit_pixmap.bind("<B1-Motion>", self._edit_leftclick)
        self.edit_pixmap.bind("<Button-3>", self._edit_rightclick)
        self.edit_pixmap.bind("<B3-Motion>", self._edit_rightclick)

        self.colors_pixmap.config(width=EDIT_WIDTH, height=COLORS_HEIGHT, bg='#FF0000')
        self.colors_pixmap.grid(column=0, row=1, sticky="sew")
        self.colors_pixmap.bind("<Button-1>", self._colors_leftclick)
        self.colors_pixmap.bind("<Button-3>", self._colors_rightclick)

        self.tlayout_win.wm_title('Tile Layer')
        self.tlayout_win.geometry(str(TLAYOUT_WIDTH+2)+'x'+str(TLAYOUT_HEIGHT+2))
        self.tlayout_win.resizable(False, False)
        self.tlayout_win.protocol("WM_DELETE_WINDOW", event_map.destroy)
        self.tlayout_pixmap.config(width=TLAYOUT_WIDTH, height=TLAYOUT_HEIGHT, bg='#FF0000')
        self.tlayout_pixmap.pack()
        self.tlayout_pixmap.bind("<Button-1>", self._tlayout_click)

    def _build_menu(self, event_map: 'NesTileEdit'):
        """
        <ui>
         <menubar name="MenuBar">
          <menu action="File">
           <menuitem action="New"/>
           <menuitem action="Open..."/>
           <menuitem action="Save"/>
           <menuitem action="Save As..."/>
           <menuitem action="Quit"/>
          </menu>
          <menu action="Edit">
           <menuitem action="Config..."/>
          </menu>
         </menubar>
        </ui>
        """
        main_menubar = tk.Menu(self.main_win)
        self.main_win.config(menu = main_menubar)

        main_file_menu = tk.Menu(main_menubar)
        main_file_menu.add_command(label="New", command=event_map.new_tileset,
                                        underline=0, accelerator="Ctrl+N")
        self.root.bind_all("<Control-n>", lambda x: event_map.new_tileset())
        main_file_menu.add_command(label="Open...", command=event_map.open_tileset,
                                        underline=0, accelerator="Ctrl+O")
        self.root.bind_all("<Control-o>", lambda x: event_map.open_tileset())
        main_file_menu.add_command(label="Save", command=event_map.save_tileset,
                                        underline=0, accelerator="Ctrl+S")
        self.root.bind_all("<Control-s>", lambda x: event_map.save_tileset())
        main_file_menu.add_command(label="Save As...", command=event_map.save_as_tileset,
                                        underline=5, accelerator="Ctrl+Shift+S")
        self.root.bind_all("<Control-S>", lambda x: event_map.save_as_tileset())
        main_file_menu.add_command(label="Quit", command=event_map.destroy,
                                        underline=0, accelerator="Ctrl+Q")
        self.root.bind_all("<Control-q>", lambda x: event_map.destroy())
        main_menubar.add_cascade(label="File", menu=main_file_menu, underline=0)

        main_edit_menu = tk.Menu(main_menubar)
        main_edit_menu.add_command(label="Config...", command=event_map.config_tileset, underline=0)

        main_menubar.add_cascade(label="Edit", menu=main_edit_menu, underline=0)

    def destroy(self):
        self.root.destroy()

    def mainloop(self):
        self.root.mainloop()

    # Tile set callbacks

    def _tileset_click(self, event):
        x = self.tileset_pixmap.canvasx(event.x)
        y = self.tileset_pixmap.canvasy(event.y)
        i = box_number(int(x), int(y), TSET_OFFSET, TSET_SPAN)
        self.event_map.set_current_tile_num(i)

    def tileset_updatehighlight(self, tile_set: 'TileSet', old_tile_num:int, new_tile_num:int):
        # redraw old Tile without highlight
        x_off = (old_tile_num  % TSET_SPAN) * TSET_OFFSET
        y_off = (old_tile_num // TSET_SPAN) * TSET_OFFSET

        # create draw callback to draw tile to
        def _draw( start_x, start_y, stop_x, stop_y, color ):
            self.tileset_pixmap.create_rectangle(
                x_off+start_x*TSET_SCALE,  y_off+start_y*TSET_SCALE,
                x_off+stop_x*TSET_SCALE-1, y_off+stop_y*TSET_SCALE-1,
                fill=color, outline=color)

        tile_set[old_tile_num].draw( _draw, tileset_palette)

        # draw highlight around new tile
        x_off = (new_tile_num  % TSET_SPAN) * TSET_OFFSET
        y_off = (new_tile_num // TSET_SPAN) * TSET_OFFSET
        self.tileset_pixmap.create_rectangle(
            x_off, y_off,
            x_off+TSET_OFFSET-1, y_off+TSET_OFFSET-1,
            fill='', outline='#00FFFF')

    def _tileset_mousewheel(self, event):
        if event.num==4: # Up
            self.tileset_pixmap.yview_scroll(-1, "units")
        else: # Down
            self.tileset_pixmap.yview_scroll(1, "units")

    # Tile edit area callbacks

    def _edit_leftclick(self, event):
        # Figure out discrete row and column of pixel
        col = event.x // EDITSCALE
        row = event.y // EDITSCALE

        # Bounds check row and column
        col = 0 if col < 0 else TILESIZE-1 if col > (TILESIZE-1) else col
        row = 0 if row < 0 else TILESIZE-1 if row > (TILESIZE-1) else row

        self.event_map.draw_tile_pixel_fg(col, row)

    def _edit_rightclick(self, event):
        # Figure out discrete row and column of pixel
        col = event.x // EDITSCALE
        row = event.y // EDITSCALE

        # Bounds check row and column
        col = 0 if col < 0 else TILESIZE-1 if col > (TILESIZE-1) else col
        row = 0 if row < 0 else TILESIZE-1 if row > (TILESIZE-1) else row

        self.event_map.draw_tile_pixel_bg(col, row)


    def update_tile_pixel(self, tlayer, tile_num, pal, tile_color, col, row):
        # Update edit pixmap
        # Given the col,row coordinates, and EDITSCALE of the pixels in the tile,
        # and the number of pixels the drawing area is across, draw a box at
        # the tile with the currently selected color
        color = nes_palette[pal[tile_color]]
        self.edit_pixmap.create_rectangle(col*EDITSCALE, row*EDITSCALE,
                                          (col+1)*EDITSCALE-1, (row+1)*EDITSCALE-1,
                                          fill=color, outline=color)

        # Update tileset pixmap
        # Same as above, but does it for the tileset window
        color = tileset_palette[tile_color]
        tile_x = col*TSET_SCALE+(tile_num % TSET_SPAN)*TSET_OFFSET
        tile_y = row*TSET_SCALE+(tile_num // TSET_SPAN)*TSET_OFFSET
        self.tileset_pixmap.create_rectangle(tile_x, tile_y,
                                             tile_x+TSET_SCALE-1, tile_y+TSET_SCALE-1,
                                             fill=color, outline=color)

        # Updates all the tiles laid on the tile layer of the same kind
        t_info = tlayer.tile_layout(tile_num)
        for t_layout in t_info:
            color =  nes_palette[t_layout.palette[tile_color]]

            lay_x = col * TLAYOUT_SCALE + t_layout.x * TLAYOUT_OFFSET
            lay_y = row * TLAYOUT_SCALE + t_layout.y * TLAYOUT_OFFSET

            self.tlayout_pixmap.create_rectangle(
                lay_x, lay_y,lay_x+TLAYOUT_SCALE-1, lay_y+TLAYOUT_SCALE-1,
                fill=color, outline=color)

    # Tile edit color selection callbacks

    def _colors_leftclick(self, event):
        i = box_number(event.x, event.y, COLORS_BOXSIZE, COLORS_SPAN)
        self.event_map.update_current_col(i)

    def _colors_rightclick(self, event):
        col = box_number( event.x, event.y, COLORS_BOXSIZE, COLORS_SPAN)
        self._create_palette_win(col)


    # Palette selection window functions and callbacks

    def _create_palette_win(self, col):
        """
        Create window for selecting color from NES palette
        """
        palette_win = tk.Toplevel(self.root)
        palette_win.wm_title('Color Chooser #' + str(col))
        palette_win.resizable(False, False)

        palette_pick = tk.Canvas(palette_win, width=256, height=64, bg='#FFFFFF')
        palette_pick.grid(column=0, row=0, sticky="n")

        palette_pick_action = lambda event : self._palette_click( event, col )
        palette_pick.bind("<Button-1>", palette_pick_action)

        palette_close = ttk.Button(palette_win, text = 'Close', command = palette_win.destroy)
        palette_close.grid(column=0, row=1, sticky="s")

        # Draws the colors blocks for selecting from the NES palette
        for i, color in enumerate(nes_palette):
            x = (i  % PALETTE_SPAN) * PALETTE_BOXSIZE
            y = (i // PALETTE_SPAN) * PALETTE_BOXSIZE
            palette_pick.create_rectangle(x,y,
                                          x+PALETTE_BOXSIZE-1,y+PALETTE_BOXSIZE-1,
                                          fill=color, outline=color)

    def _palette_click(self, event, col):
        """
        Handle change in palette changing displayed colors to reflect it
        """
        new_color = box_number(event.x, event.y, PALETTE_BOXSIZE, PALETTE_SPAN)

        self.event_map.palette_update(col, new_color)

    # Tile layer area callbacks

    def _tlayout_click(self, event):
        # Figure out discrete row and column of pixel
        col = event.x // TLAYOUT_OFFSET
        row = event.y // TLAYOUT_OFFSET

        # Bounds check row and column
        col = 0 if col < 0 else (TLAYOUT_XSPAN-1) if col > (TLAYOUT_XSPAN-1) else col
        row = 0 if row < 0 else (TLAYOUT_YSPAN-1) if row > (TLAYOUT_YSPAN-1) else row

        self.event_map.lay_tile(col, row)

    def lay_tile(self, col, row, tile: 'Tile', pal: list[int]):
        x_off = col * TLAYOUT_OFFSET
        y_off = row * TLAYOUT_OFFSET

        # create draw callback to draw tile to tlayout_pixmap
        def _draw( start_x, start_y, stop_x, stop_y, color ):
            self.tlayout_pixmap.create_rectangle(
                x_off+start_x*TLAYOUT_SCALE,  y_off+start_y*TLAYOUT_SCALE,
                x_off+stop_x*TLAYOUT_SCALE-1, y_off+stop_y*TLAYOUT_SCALE-1,
                fill=color, outline=color)

        tile.draw( _draw, [nes_palette[i] for i in pal] )

    def tileset_configure(self, tile_set: 'TileSet', current_tile_num: int):
        # Clear out draw window (done in configure before, but trying to avoid
        # having my graphics drawn over.
        self.tileset_pixmap.config(scrollregion=(0,0,TSET_WIDTH,
                                                 (TSET_OFFSET * len(tile_set)) // TSET_SPAN) )
        self.tileset_pixmap.delete('all')

        x = 0
        y = 0
        for i, tile in enumerate(tile_set):
            # create draw callback to draw tile to tileset_pixmap
            def _draw( start_x, start_y, stop_x, stop_y, color ):
                self.tileset_pixmap.create_rectangle(
                    x+start_x*TSET_SCALE, y+start_y*TSET_SCALE,
                    x+stop_x*TSET_SCALE-1, y+stop_y*TSET_SCALE-1,
                    fill=color, outline=color)

            tile.draw( _draw, tileset_palette)

            if i == current_tile_num:
                self.tileset_pixmap.create_rectangle(x, y, x+TSET_OFFSET-1, y+TSET_OFFSET-1,
                                             fill='', outline='#00FFFF')
            x += TSET_OFFSET
            if x >= TSET_WIDTH:
                y += TSET_OFFSET
                x = 0

    def edit_configure(self, current_tile_num: int, tile: 'Tile', pal: list):
        self.edit_win.wm_title('Tile #' + str(current_tile_num))
        self.edit_pixmap.delete('all')

        # create draw callback to draw tile to edit_pixmap
        def _draw( start_x, start_y, stop_x, stop_y, color ):
            self.edit_pixmap.create_rectangle(
                start_x*EDITSCALE, start_y*EDITSCALE,
                stop_x*EDITSCALE-1, stop_y*EDITSCALE-1,
                fill=color, outline=color)

        tile.draw( _draw, [nes_palette[i] for i in pal] )

    def colors_configure(self, pal: list, selected_col: int):
        self.colors_pixmap.delete('all')
        for i, col_idx in enumerate(pal):
            color = nes_palette[col_idx]
            x = i * COLORS_BOXSIZE
            if i == selected_col:
                self.colors_pixmap.create_rectangle(x,0,
                                                    x+COLORS_BOXSIZE-1, COLORS_BOXSIZE-1,
                                                    fill=color, outline="#00FFFF")
            else:
                self.colors_pixmap.create_rectangle(x,0,
                                                    x+COLORS_BOXSIZE-1, COLORS_BOXSIZE-1,
                                                    fill=color, outline=color)

    def tlayout_configure(self, tile_set: 'TileSet', tlayout: 'TileLayerData'):
        self.tlayout_pixmap.delete('all')
        #TKOTZ need to draw all the tiles in the layer
        self.tlayout_pixmap.create_rectangle( 0, 0, 512, 480, fill="#000000")
        return True



class NesTileEdit:
    """Class for the NES Tile Editor program

    """

    def __init__(self, filename=None):
        # Initialize class variables
        self._tile_set = TileSet(CROM_INC, filename)
        self._tlayer = TileLayerData()
        self._ui = NesTileEditTk(self)

        self.current_pal = [15, 2, 10, 6]
        # Index into self.current_pal, not nes_palette
        self.current_col = 1

        self.current_tile_num = 0

        # Widget display
        self._ui.tileset_configure(self._tile_set, self.current_tile_num)
        self._ui.edit_configure(self.current_tile_num,
                                self._tile_set[self.current_tile_num],
                                self.current_pal)
        self._ui.colors_configure(self.current_pal, self.current_col)
        self._ui.tlayout_configure(self._tile_set, self._tlayer)

        print(self._tile_set)


    def set_current_tile_num(self, idx: int ):
        if idx != self.current_tile_num and idx < len(self._tile_set):
            self._ui.tileset_updatehighlight(self._tile_set, self.current_tile_num, idx)

            self.current_tile_num = idx

            # Update edit box with new selected tile
            self._ui.edit_configure(self.current_tile_num,
                                    self._tile_set[self.current_tile_num],
                                    self.current_pal)


    # Generic callbacks

    def destroy(self):
        if not self._check_to_save_tileset():
            return False
        self._ui.destroy()
        return True

    # Menubar callbacks

    def _check_to_save_tileset(self ):
        if self._tile_set.modified:
            result = messagebox.askyesnocancel("Question", "Save current file?")

            if result is None:
                # Cancel
                return False
            if not result:
                # No
                return True
            # Yes
            if not self.save_as_tileset():
                messagebox.showerror("Error", "Unable to save tile set!")
                return False
        return True

    def new_tileset(self):
        if not self._check_to_save_tileset():
            return False

        self._tile_set.reset()
        self._tlayer.reset()
        self.current_pal = [15, 2, 10, 6]
        # Index into self.current_pal, not nes_palette
        self.current_col = 1
        self.current_tile_num = 0

        # Widget display
        self._ui.tileset_configure(self._tile_set, self.current_tile_num)
        self._ui.edit_configure(self.current_tile_num,
                                self._tile_set[self.current_tile_num],
                                self.current_pal)
        self._ui.colors_configure(self.current_pal, self.current_col)
        self._ui.tlayout_configure(self._tile_set, self._tlayer)
        return True


    def open_tileset(self):
        if not self._check_to_save_tileset():
            return False

        filename = filedialog.askopenfilename(filetypes=nes_filetypes)
        if not filename:
            return False

        self._tile_set.do_open( filename )

        self._tlayer.reset()

        # redraw the windows
        self.set_current_tile_num(0)
        self._ui.tileset_configure(self._tile_set, self.current_tile_num)
        self._ui.edit_configure(self.current_tile_num,
                                self._tile_set[self.current_tile_num],
                                self.current_pal)
        self._ui.tlayout_configure(self._tile_set, self._tlayer)
        return True


    def close_tileset(self):
        """
        What does it even mean to Close a tile set?
        Is this just quit
        """
        return self.new_tileset()


    def save_as_tileset(self):
        filename = filedialog.asksaveasfilename(filetypes=nes_filetypes,
                                                initialfile=self._tile_set.filename )
        if not filename:
            return

        self._tile_set.do_save( filename )

    def save_tileset(self):
        if not self._tile_set.filename:
            # do save as if there's no filename for now
            self.save_as_tileset()
        else:
            self._tile_set.do_save(self._tile_set.filename)

    def config_tileset(self):
        """
        Gets configuration from the user
        Currently only supports changing ROM size
        needs more settings
        """
        return
        #    if self.file_format != 'raw':
        #        msg = "Only supported in raw mode.\nUse File->New\nto reset raw mode"
        #        messagebox.showwarning("Warning", msg)
        #        return False
        #
        #    msg = "CHR ROM Size (Number of 8K blocks)"
        #    result = simpledialog.askinteger('Configuration', msg,
        #                                     initialvalue=(self.chr_rom_size//CROM_INC))
        #    if not result:
        #        return False
        #    try:
        #        self.chr_rom_size = result * CROM_INC
        #
        #        # resize tile data elements
        #        new_size = self.chr_rom_size // BYTES_PER_TILE
        #        if len(self.tile_data)>new_size:
        #            self.tile_layout = self.tile_layout[:new_size]
        #            self.tile_data = self.tile_data[:new_size]
        #            if self.current_tile_num >= new_size:
        #                self.set_current_tile_num(0)
        #                self._edit_configure()
        #        else:
        #            for _ in range(len(self.tile_data),new_size):
        #                self.tile_layout.append(None)
        #                self.tile_data.append(None)
        #
        #        # update display
        #        self._tileset_configure()
        #        return True
        #    except ValueError:
        #        messagebox.showerror("Error", "Invalid size specified.")
        #    except Exception as err:
        #        messagebox.showerror("Error", f"Unexpected {err=}, {type(err)=}")
        #        raise
        #    return False



    def palette_update(self, palette_idx, new_nes_color):
        # Current palette info updated when old info no longer needed
        self.current_pal[palette_idx] = new_nes_color

        # Redraw the colors bar to show updated palette selection
        self._ui.colors_configure(self.current_pal, self.current_col)

        # Redraw the edit window with updated palette
        self._ui.edit_configure(self.current_tile_num,
                                self._tile_set[self.current_tile_num],
                                self.current_pal)

    def update_current_col(self, new_col):
        if new_col != self.current_col:
            self.current_col = new_col
            # Redraw the colors bar to show updated palette selection
            self._ui.colors_configure(self.current_pal, self.current_col)

    # Other cross domain functions

    def _draw_tile_pixel( self, col, row, tile_color):
        """
        Modifies a pixel in the tile editor
        reflecting that change in the Tile set and Taile Layout
        """
        self._tile_set.update_tile_pixel(self.current_tile_num,col,row,tile_color)
        self._ui.update_tile_pixel(self._tlayer, self.current_tile_num,
                                   self.current_pal, tile_color,
                                   col, row)

    def draw_tile_pixel_fg( self, col, row):
        self._draw_tile_pixel(col, row, self.current_col)

    def draw_tile_pixel_bg( self, col, row):
        self._draw_tile_pixel(col, row, 0)

    def lay_tile(self, col, row):
        """
        Draw the current tile at the block in location col, row
        """
        self._tlayer.lay_tile( col, row, self.current_tile_num, self.current_pal)
        self._ui.lay_tile( col, row, self._tile_set[self.current_tile_num], self.current_pal)


    def main(self):
        self._ui.mainloop()

# Main program loop
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if '--test' in sys.argv:
            unittest()
            sys.exit(0)
        elif len(sys.argv) > 2 or '-h' in sys.argv:
            print("Usage: {} [FILE]".format(sys.argv[0]))
            print("\tFILE - sets name of the FILE to open.")
            sys.exit(0)
        else:
            nes_tile_edit = NesTileEdit(sys.argv[1])
    else:
        nes_tile_edit = NesTileEdit(sys.argv[1])

    nes_tile_edit.main()
