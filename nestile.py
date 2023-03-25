#!/usr/bin/env python3

# NES Tile Editor
# A program for creating and editing graphics for NES programs
# Author: Jerry McMahan Jr. (ported to python3 and tkinter by Theodore Kotz)
# Version: 0.3.0
# See changes.txt for changes and version info

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


def draw_box_i(canvas, i, scale, row_span, color, outline_color=None):
    x = (i  % row_span) * scale
    y = (i // row_span) * scale
    if outline_color is None:
        outline_color = color
    canvas.create_rectangle( x,y,x+scale-1,y+scale-1, fill=color, outline=outline_color)



def draw_tile(canvas: 'tk.Canvas', xoffset, yoffset, scale, tile: 'Tile', pal: list[str]):
    if tile is None:
        color = pal[0]
        canvas.create_rectangle(xoffset, yoffset,
                                xoffset+TILESIZE*scale-1, yoffset+TILESIZE*scale-1,
                                fill=color, outline=color)
        return
    for x in range(8):
        for y in range(8):
            color = pal[tile[y][x]]
            canvas.create_rectangle(xoffset+x*scale, yoffset+y*scale,
                                    xoffset+(x+1)*scale-1, yoffset+(y+1)*scale-1,
                                    fill=color, outline=color)

def print_tile_data(tile_data: list['Tile']):
    for tile in tile_data:
        if isinstance(tile, list):
            for row in tile:
                print(row)
        else:
            print(tile)
        print("---------------------------------------------------------")


def bytes_from_tile(tile: 'Tile') ->  bytes:
    """
    Given a tile in the form of 8x8 list or palette indexes
    returns a string or bytes containing raw NES graphics data (in binary),
    """
    if tile is None:
        return b"\0" * BYTES_PER_TILE
    hi_data = bytearray(b"")
    lo_data = bytearray(b"")
    for row in tile:
        hi_bits = 0
        lo_bits = 0
        for col in row:
            hi_bits = (hi_bits << 1)+((col >> 1) & 1)
            lo_bits = (lo_bits << 1)+(col & 1)
        hi_data.append(hi_bits)
        lo_data.append(lo_bits)
    return lo_data + hi_data

def tile_from_bytes(data:bytes) -> 'Tile':
    """
    Given a string of bytes containing raw NES graphics data (in binary),
    returns a tile in the form of 8x8 list or palette indexes
    """
    if (b"\0" * BYTES_PER_TILE) == data[0:BYTES_PER_TILE]:
        return None
    tile = []
    for y in range(8):
        hi_bits = (data[y+8] << 1)
        lo_bits = data[y]
        tile.append( [ ((hi_bits >> (i)) & 2) + ((lo_bits >> (i)) & 1)
                       for i in range(7,-1,-1) ] )
    return tile



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
    first_tile = tile_from_bytes(base_bytes)
    print (first_tile)
    gen_bytes = bytes_from_tile(first_tile)
    print (gen_bytes)
    print(base_bytes == gen_bytes)
    sec_tile = tile_from_bytes(gen_bytes)
    print (sec_tile)
    print(first_tile == sec_tile)



class NesTileEdit:
    """Class for the NES Tile Editor program

    """

    def __init__(self):
        # Initialize class variables
        self.chr_rom_size = CROM_INC

        # Note the real defaults are in _reset_data
        self.current_pal = [15, 2, 10, 6]
        # Index into self.current_pal, not nes_palette
        self.current_col = 1
        self.current_tile_num = 0
        self.filename = ''
        self.file_format = 'raw'
        self.modified = False
        # Holds information for drawing tiles on the tile layer
        self.tile_layout = (self.chr_rom_size // BYTES_PER_TILE) * [None]

        # Initialize tile map
        self.tile_at_xy = [ TLAYOUT_YSPAN*[None] for _ in range(TLAYOUT_XSPAN) ]
        # Holds iNES PRG and header data when opening iNES ROM's
        self.ines_data = None

        # Holds the tile bitmaps as 'Tile's
        self.tile_data = [None]* (self.chr_rom_size//BYTES_PER_TILE)

        self._reset_data()

        # Create widgets
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
        self._setup_ui()
        self._build_menu()

        # Widget display
        self._tileset_configure()
        self._edit_configure()
        self._colors_configure()
        self._tlayout_configure()

    def set_current_tile_num(self, idx: int ):
        self.current_tile_num = idx
        if self.tile_data[self.current_tile_num] is None:
            self.tile_data[self.current_tile_num] = [[0]*TILESIZE for _ in range(TILESIZE)]


    def _reset_data(self):
        self.current_pal = [15, 2, 10, 6]
        # Index into self.current_pal, not nes_palette
        self.current_col = 1
        self.filename = ''
        self.file_format = 'raw'
        self.modified = False
        # Holds information for drawing tiles on the tile layer
        self.tile_layout = (self.chr_rom_size // BYTES_PER_TILE) * [None]

        # Initialize tile map
        self.tile_at_xy = [ TLAYOUT_YSPAN*[None] for _ in range(TLAYOUT_XSPAN) ]
        # Holds iNES PRG and header data when opening iNES ROM's
        self.ines_data = None

        # Holds the tile bitmaps as 'Tile's
        self.tile_data = [None]* (self.chr_rom_size//BYTES_PER_TILE)
        self.set_current_tile_num(0)

    def _setup_ui(self):
        """
        Set widget properties
        Widget arrangement and display
        Setup events / signals
        """
        self.main_win.wm_title('Tile Set')
        self.main_win.geometry(str(TSET_WIDTH+24)+'x'+str(TSET_HEIGHT+2))
        self.main_win.resizable(False, False)
        self.main_win.protocol("WM_DELETE_WINDOW", self.destroy)
        self.tileset_pixmap.config(bg='#FF0000', width=TSET_WIDTH, height= TSET_HEIGHT)
        self.tileset_pixmap.grid(row=0, column=0)
        self.tileset_pixmap.bind("<Button-1>", self.tileset_click)
        self.tileset_pixmap.bind("<Button-4>", self.tileset_mousewheel)
        self.tileset_pixmap.bind("<Button-5>", self.tileset_mousewheel)

        self.edit_win.wm_title('Tile #' + str(self.current_tile_num))
        self.edit_win.geometry(str(EDIT_WIDTH+2)+'x'+str(EDIT_HEIGHT+COLORS_HEIGHT+4))
        self.edit_win.resizable(False, False)
        self.edit_win.protocol("WM_DELETE_WINDOW", self.destroy)
        self.edit_pixmap.config(width=EDIT_WIDTH, height=EDIT_HEIGHT, bg='#FF0000')
        self.edit_pixmap.grid(column=0, row=0, sticky="new")
        self.edit_pixmap.bind("<Button-1>", self._edit_leftclick)
        self.edit_pixmap.bind("<B1-Motion>", self._edit_leftclick)
        self.edit_pixmap.bind("<Button-3>", self._edit_rightclick)
        self.edit_pixmap.bind("<B3-Motion>", self._edit_rightclick)

        self.colors_pixmap.config(width=EDIT_WIDTH, height=COLORS_HEIGHT, bg='#FF0000')
        self.colors_pixmap.grid(column=0, row=1, sticky="sew")
        self.colors_pixmap.bind("<Button-1>", self.colors_leftclick)
        self.colors_pixmap.bind("<Button-3>", self.colors_rightclick)

        self.tlayout_win.wm_title('Tile Layer')
        self.tlayout_win.geometry(str(TLAYOUT_WIDTH+2)+'x'+str(TLAYOUT_HEIGHT+2))
        self.tlayout_win.resizable(False, False)
        self.tlayout_win.protocol("WM_DELETE_WINDOW", self.destroy)
        self.tlayout_pixmap.config(width=TLAYOUT_WIDTH, height=TLAYOUT_HEIGHT, bg='#FF0000')
        self.tlayout_pixmap.pack()
        self.tlayout_pixmap.bind("<Button-1>", self.tlayout_click)

    def _build_menu(self):
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
        main_file_menu.add_command(label="New", command=self.new_tileset,
                                        underline=0, accelerator="Ctrl+N")
        self.root.bind_all("<Control-n>", lambda x: self.new_tileset())
        main_file_menu.add_command(label="Open...", command=self.open_tileset,
                                        underline=0, accelerator="Ctrl+O")
        self.root.bind_all("<Control-o>", lambda x: self.open_tileset())
        main_file_menu.add_command(label="Save", command=self.save_tileset,
                                        underline=0, accelerator="Ctrl+S")
        self.root.bind_all("<Control-s>", lambda x: self.save_tileset())
        main_file_menu.add_command(label="Save As...", command=self.save_as_tileset,
                                        underline=5, accelerator="Ctrl+Shift+S")
        self.root.bind_all("<Control-S>", lambda x: self.save_as_tileset())
        main_file_menu.add_command(label="Quit", command=self.destroy,
                                        underline=0, accelerator="Ctrl+Q")
        self.root.bind_all("<Control-q>", lambda x: self.destroy())
        main_menubar.add_cascade(label="File", menu=main_file_menu, underline=0)

        main_edit_menu = tk.Menu(main_menubar)
        main_edit_menu.add_command(label="Config...", command=self.config_tileset, underline=0)

        main_menubar.add_cascade(label="Edit", menu=main_edit_menu, underline=0)



    # Generic callbacks

    def destroy(self):
        if not self._check_to_save_tileset():
            return False
        self.root.destroy()
        return True

    # Menubar callbacks

    def _check_to_save_tileset(self ):
        if self.modified:
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

        self._reset_data()

        self._tileset_configure()
        self._edit_configure()
        self._colors_configure()
        self._tlayout_configure()
        return True


    def open_tileset(self):
        if not self._check_to_save_tileset():
            return False

        filename = filedialog.askopenfilename(filetypes=nes_filetypes)
        if not filename:
            return False
        return self.do_open( filename )

    def close_tileset(self):
        """
        What does it even mean to Close a tile set?
        Is this just quit
        """
        return self.new_tileset()


    def _save_tileset_common(self, filename):
        if self.do_save( filename ):
            return True

        messagebox.showerror("Error", "Unable to save to `{}`".format(filename))
        return False

    def save_as_tileset(self):
        filename = filedialog.asksaveasfilename(filetypes=nes_filetypes, initialfile=self.filename )
        if not filename:
            return False

        return self._save_tileset_common(filename)

    def save_tileset(self):
        if not self.filename:
            # do save as if there's no filename for now
            return self.save_as_tileset()

        return self._save_tileset_common(self.filename)

    def config_tileset(self):
        """
        Gets configuration from the user
        Currently only supports changing ROM size
        needs more settings
        """
        if self.file_format != 'raw':
            msg = "Only supported in raw mode.\nUse File->New\nto reset raw mode"
            messagebox.showwarning("Warning", msg)
            return False

        msg = "CHR ROM Size (Number of 8K blocks)"
        result = simpledialog.askinteger('Configuration', msg,
                                         initialvalue=(self.chr_rom_size//CROM_INC))
        if not result:
            return False
        try:
            self.chr_rom_size = result * CROM_INC

            # resize tile data elements
            new_size = self.chr_rom_size // BYTES_PER_TILE
            if len(self.tile_data)>new_size:
                self.tile_layout = self.tile_layout[:new_size]
                self.tile_data = self.tile_data[:new_size]
                if self.current_tile_num >= new_size:
                    self.set_current_tile_num(0)
                    self._edit_configure()
            else:
                for _ in range(len(self.tile_data),new_size):
                    self.tile_layout.append(None)
                    self.tile_data.append(None)

            # update display
            self._tileset_configure()
            return True
        except ValueError:
            messagebox.showerror("Error", "Invalid size specified.")
        except Exception as err:
            messagebox.showerror("Error", f"Unexpected {err=}, {type(err)=}")
            raise
        return False



    # Tile set callbacks

    def _tileset_configure(self):
        # Clear out draw window (done in configure before, but trying to avoid
        # having my graphics drawn over.
        self.tileset_pixmap.config(scrollregion=(0,0,TSET_WIDTH,
             (TSET_OFFSET * self.chr_rom_size) // (TSET_SPAN * BYTES_PER_TILE))
        )
        self.tileset_pixmap.delete('all')

        x = 0
        y = 0
        for i, tile in enumerate(self.tile_data):
            draw_tile( self.tileset_pixmap, x, y, TSET_SCALE, tile, tileset_palette)
            if i == self.current_tile_num:
                self.tileset_pixmap.create_rectangle(x, y, x+TSET_OFFSET-1, y+TSET_OFFSET-1,
                                             fill='', outline='#00FFFF')
            x += TSET_OFFSET
            if x >= TSET_WIDTH:
                y += TSET_OFFSET
                x = 0


    def tileset_click(self, event):
        x = self.tileset_pixmap.canvasx(event.x)
        y = self.tileset_pixmap.canvasy(event.y)
        i = box_number(int(x), int(y), TSET_OFFSET, TSET_SPAN)
        if i != self.current_tile_num:
            if i >= len(self.tile_data):
                messagebox.showerror("Error", "Tile is beyond allocated ROM size.")
                return
            if self.tile_data[i] is None:
                self.tile_data[i] = [[0]*TILESIZE for j in range(TILESIZE)]
            x = (self.current_tile_num  % TSET_SPAN) * TSET_OFFSET
            y = (self.current_tile_num // TSET_SPAN) * TSET_OFFSET
            draw_tile(self.tileset_pixmap, x, y, TSET_SCALE,
                           self.tile_data[self.current_tile_num], tileset_palette)
            x = (i  % TSET_SPAN) * TSET_OFFSET
            y = (i // TSET_SPAN) * TSET_OFFSET
            self.tileset_pixmap.create_rectangle(x, y, x+TSET_OFFSET-1, y+TSET_OFFSET-1,
                                             fill='', outline='#00FFFF')
            self.set_current_tile_num(i)

            # Update edit box with new selected tile
            self._edit_configure()


    def tileset_mousewheel(self, event):
        if event.num==4: # Up
            self.tileset_pixmap.yview_scroll(-1, "units")
        else: # Down
            self.tileset_pixmap.yview_scroll(1, "units")

    # Tile edit area callbacks

    def _edit_configure(self):
        self.edit_win.wm_title('Tile #' + str(self.current_tile_num))
        self.edit_pixmap.delete('all')
        cur_pal = [nes_palette[i] for i in self.current_pal]
        draw_tile(self.edit_pixmap, 0, 0, EDITSCALE,
                       self.tile_data[self.current_tile_num], cur_pal)

    def _edit_leftclick(self, event):
        self.modified = True
        self.draw_tile_pixel(event.x, event.y, self.current_col)

    def _edit_rightclick(self, event):
        self.modified = True
        self.draw_tile_pixel(event.x, event.y, 0)


    # Tile edit color selection callbacks

    def _colors_configure(self):
        self.colors_pixmap.delete('all')
        #TKOTZ switch to enumerate
        for i in range(4):
            outline_color = color = nes_palette[self.current_pal[i]]
            if i == self.current_col:
                outline_color = "#00FFFF"
            draw_box_i( self.colors_pixmap, i, COLORS_BOXSIZE, COLORS_SPAN, color, outline_color)

    def colors_leftclick(self, event):
        i = self.current_col
        color = nes_palette[self.current_pal[i]]
        draw_box_i( self.colors_pixmap, i, COLORS_BOXSIZE, COLORS_SPAN, color)
        self.current_col = i = box_number(event.x, event.y, COLORS_BOXSIZE, COLORS_SPAN)
        color = nes_palette[self.current_pal[i]]
        draw_box_i( self.colors_pixmap, i, COLORS_BOXSIZE, COLORS_SPAN, color, "#00FFFF")

    def colors_rightclick(self, event):
        col = box_number( event.x, event.y, COLORS_BOXSIZE, COLORS_SPAN)
        self.create_palette_win(col)


    # Tile layer area callbacks

    def _tlayout_configure(self):
        self.tlayout_pixmap.delete('all')
        #TKOTZ need to draw all the tiles in the layer
        self.tlayout_pixmap.create_rectangle( 0, 0, 512, 480, fill="#000000")
        return True

    def tlayout_click(self, event):
        self.lay_tile(event.x, event.y)


    # Palette selection window functions and callbacks

    def create_palette_win(self, col):
        """
        Create window for selecting color from NES palette
        """
        palette_win = tk.Toplevel(self.root)
        palette_win.wm_title('Color Chooser #' + str(col))
        palette_win.resizable(False, False)

        palette_pick = tk.Canvas(palette_win, width=256, height=64, bg='#FFFFFF')
        palette_pick.grid(column=0, row=0, sticky="new")

        palette_pick_action = lambda event : self.palette_click( event, col )
        palette_pick.bind("<Button-1>", palette_pick_action)

        palette_close = ttk.Button(palette_win, text = 'Close', command = palette_win.destroy)
        palette_close.grid(column=0, row=1, sticky="sew")

        # Draws the colors blocks for selecting from the NES palette
        for i, color in enumerate(nes_palette):
            draw_box_i(palette_pick, i, PALETTE_BOXSIZE, PALETTE_SPAN, color)

    def palette_click(self, event, col):
        """
        Handle change in palette changing displayed colors to reflect it
        """
        new_color = box_number(event.x, event.y, PALETTE_BOXSIZE, PALETTE_SPAN)

        # Current palette info updated when old info no longer needed
        self.current_pal[col] = new_color

        # Redraw the colors bar to show updated palette selection
        self._colors_configure()

        # Redraw the edit window with updated palette
        self._edit_configure()

    # File I/O functions

    def do_save(self, filename: str) -> bool:
        """
        Saves the tile data to the file at filename
        """
        # Later, try to differentiate between different file formats here
        # but just treat everything like a raw binary file for now
        output_string = b"".join([bytes_from_tile(tile) for tile in self.tile_data ])

        with open(filename, 'wb') as fout:
            if self.file_format == 'raw':
                fout.write(output_string)
            elif self.file_format == 'ines':
                fout.write(self.ines_data + output_string)
            self.modified = False
            self.filename = filename
        return True

    def do_open(self, filename: str) -> bool:
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
            # if not iNES, make sure data length is a multiple of 8192
            if len(fdata) % CROM_INC == 0:
                self.chr_rom_size = len(fdata)
            else:
                fdata = fdata + (CROM_INC - (len(fdata) % CROM_INC)) * b'\0'
                self.chr_rom_size = CROM_INC * (int(len(fdata) / CROM_INC) + 1)

        if len(fdata) < self.chr_rom_size:
            self.chr_rom_size = len(fdata)

        self.tile_data = [tile_from_bytes( fdata[i*BYTES_PER_TILE:(i+1)*BYTES_PER_TILE] )
                          for i in range(0, len(fdata)//BYTES_PER_TILE) ]

        self.tile_layout = len(self.tile_data) * [None]

        # redraw the windows
        self.set_current_tile_num(0)
        self._tileset_configure()
        self._edit_configure()
        self._tlayout_configure()

    # Other cross domain functions

    def draw_tile_pixel( self, x, y, tile_color):
        """
        Modifies a pixel in the tile editor
        reflecting that change in the Tile set and Taile Layout
        """
        # Figure out discrete row and column of pixel
        col = x // EDITSCALE
        row = y // EDITSCALE

        # Bounds check row and column
        col = 0 if col < 0 else TILESIZE-1 if col > (TILESIZE-1) else col
        row = 0 if row < 0 else TILESIZE-1 if row > (TILESIZE-1) else row

        # Update edit pixmap
        # Given the col,row coordinates, and EDITSCALE of the pixels in the tile,
        # and the number of pixels the drawing area is across, draw a box at
        # the tile with the currently selected color
        color = nes_palette[self.current_pal[tile_color]]
        self.edit_pixmap.create_rectangle(col*EDITSCALE, row*EDITSCALE,
                                          (col+1)*EDITSCALE-1, (row+1)*EDITSCALE-1,
                                          fill=color, outline=color)

        # Update tileset pixmap
        # Same as above, but does it for the tileset window
        color = tileset_palette[tile_color]
        tile_row, tile_col = divmod(self.current_tile_num, TSET_SPAN)
        tile_x = col*TSET_SCALE+tile_col*TSET_OFFSET
        tile_y = row*TSET_SCALE+tile_row*TSET_OFFSET
        self.tileset_pixmap.create_rectangle(tile_x, tile_y,
                                             tile_x+TSET_SCALE-1, tile_y+TSET_SCALE-1,
                                             fill=color, outline=color)
        self.tile_data[self.current_tile_num][row][col]=tile_color

        # Updates all the tiles laid on the tile layer of the same kind
        t_info = self.tile_layout[self.current_tile_num]
        if t_info is None:
            return
        for t_layout in t_info:
            if self.tile_at_xy[t_layout[0]][t_layout[1]] == self.current_tile_num:
                color =  nes_palette[t_layout[2][tile_color]]

                lay_x = col * TLAYOUT_SCALE + t_layout[0] * TLAYOUT_OFFSET
                lay_y = row * TLAYOUT_SCALE + t_layout[1] * TLAYOUT_OFFSET

                self.tlayout_pixmap.create_rectangle(lay_x, lay_y,
                                                   lay_x+TLAYOUT_SCALE-1, lay_y+TLAYOUT_SCALE-1,
                                                   fill=color, outline=color)

    def lay_tile(self, x, y):
        """
        Draw the current tile at the block in location x, y with
        a x and y size of TLAYOUT_OFFSET
        """

        # Figure out discrete row and column of pixel
        col = x // TLAYOUT_OFFSET
        row = y // TLAYOUT_OFFSET

        # Bounds check row and column
        col = 0 if col < 0 else (TLAYOUT_XSPAN-1) if col > (TLAYOUT_XSPAN-1) else col
        row = 0 if row < 0 else (TLAYOUT_YSPAN-1) if row > (TLAYOUT_YSPAN-1) else row

        x_box = col * TLAYOUT_OFFSET
        y_box = row * TLAYOUT_OFFSET

        cur_pal = self.current_pal[:]
        draw_pal = [nes_palette[i] for i in cur_pal]
        draw_tile(self.tlayout_pixmap, x_box, y_box, TSET_SCALE,
                       self.tile_data[self.current_tile_num], draw_pal)

        self.tile_at_xy[col][row] = self.current_tile_num

        t_info = self.tile_layout[self.current_tile_num]

        if t_info is None:
            self.tile_layout[self.current_tile_num] = [[col, row, cur_pal]]
            return

        for t_layout in t_info:
            if t_layout[0:2] == [col, row]:
                t_layout[2] = cur_pal
                return

        self.tile_layout[self.current_tile_num].append([col, row, cur_pal])

    def main(self):
        self.root.mainloop()

# Main program loop
if __name__ == "__main__":
    nes_tile_edit = NesTileEdit()
    if len(sys.argv) > 1:
        if '--test' in sys.argv:
            unittest()
            sys.exit(0)
        elif len(sys.argv) > 2 or '-h' in sys.argv:
            print("Usage: {} [FILE]".format(sys.argv[0]))
            print("\tFILE - sets name of the FILE to open.")
            sys.exit(0)
        elif os.path.isfile(sys.argv[1]):
            nes_tile_edit.do_open( sys.argv[1] )
        else:
            nes_tile_edit.filename=sys.argv[1]
    nes_tile_edit.main()
