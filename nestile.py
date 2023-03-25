#!/usr/bin/env python3

# NES Tile Editor
# A program for creating and editing graphics for NES programs
# Author: Jerry McMahan Jr. (ported to python3 and tkinter by Theodore Kotz)
# Version: 0.3.0
# See changes.txt for changes and version info

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog

EDITSCALE=16
LAYER_SCALE=2
MAX_XBOX = 31
MAX_YBOX = 29
ROWSPAN=8
TILESCALE=2
TILESPAN=16
LAYER_OFFSET=ROWSPAN*LAYER_SCALE
TILEOFFSET=ROWSPAN*TILESCALE
BYTES_PER_TILE=16

nes_palette = (
   (0x80,0x80,0x80), (0x00,0x00,0xbb), (0x37,0x00,0xbf), (0x84,0x00,0xa6),
   (0xbb,0x00,0x6a), (0xb7,0x00,0x1e), (0xb3,0x00,0x00), (0x91,0x26,0x00),
   (0x7b,0x2b,0x00), (0x00,0x3e,0x00), (0x00,0x48,0x0d), (0x00,0x3c,0x22),
   (0x00,0x2f,0x66), (0x00,0x00,0x00), (0x05,0x05,0x05), (0x05,0x05,0x05),

   (0xc8,0xc8,0xc8), (0x00,0x59,0xff), (0x44,0x3c,0xff), (0xb7,0x33,0xcc),
   (0xff,0x33,0xaa), (0xff,0x37,0x5e), (0xff,0x37,0x1a), (0xd5,0x4b,0x00),
   (0xc4,0x62,0x00), (0x3c,0x7b,0x00), (0x1e,0x84,0x15), (0x00,0x95,0x66),
   (0x00,0x84,0xc4), (0x11,0x11,0x11), (0x09,0x09,0x09), (0x09,0x09,0x09),

   (0xff,0xff,0xff), (0x00,0x95,0xff), (0x6f,0x84,0xff), (0xd5,0x6f,0xff),
   (0xff,0x77,0xcc), (0xff,0x6f,0x99), (0xff,0x7b,0x59), (0xff,0x91,0x5f),
   (0xff,0xa2,0x33), (0xa6,0xbf,0x00), (0x51,0xd9,0x6a), (0x4d,0xd5,0xae),
   (0x00,0xd9,0xff), (0x66,0x66,0x66), (0x0d,0x0d,0x0d), (0x0d,0x0d,0x0d),

   (0xff,0xff,0xff), (0x84,0xbf,0xff), (0xbb,0xbb,0xff), (0xd0,0xbb,0xff),
   (0xff,0xbf,0xea), (0xff,0xbf,0xcc), (0xff,0xc4,0xb7), (0xff,0xcc,0xae),
   (0xff,0xd9,0xa2), (0xcc,0xe1,0x99), (0xae,0xee,0xb7), (0xaa,0xf7,0xee),
   (0xb3,0xee,0xff), (0xdd,0xdd,0xdd), (0x11,0x11,0x11), (0x11,0x11,0x11))


tileset_palette = ( "#000000", "#00FFFF", "#FF00FF", "#FFFF00")

nes_filetypes=(('Raw files', '.*'), ('NES files', '.nes'))

def callback(event):
    # print "clicked at", event.x, event.y
    print ("Event"+str( event ))

def get_color_string( color_tuple ):
    return "#{:02x}{:02x}{:02x}".format(color_tuple[0], color_tuple[1], color_tuple[2])

class NesTileEdit:
    """Class for the NES Tile Editor program

    """

    def __init__(self):

        # Initialize class variables
        self.current_pal = [15, 2, 10, 6]
        # Index into self.current_pal, not nes_palette
        self.current_col = 1
        self.current_tile_num = 0
        self.chr_rom_size = 8192
        self.filename = ''
        self.format = 'raw'
        self.modified = False
        # Holds information for drawing tiles on the tile layer
        self.tile_layout = self.chr_rom_size // 2 * [None]
        self.quitting = False

        # Initialize tile map
        self.tile_at_xy = [ (MAX_YBOX+1)*[None] for x in range(MAX_XBOX+1) ]
        # Holds iNES PRG and header data when opening iNES ROM's
        self.ines_data = None

        self.tile_data = [None]* (self.chr_rom_size//BYTES_PER_TILE)

        # Create widgets
        # Set widget properties
        # Widget arrangement and display
        # Setup events / signals
        self.main_win = tk.Tk()
        self.main_win.wm_title('Tile Set')
        self.main_win.geometry('280x512')
        self.main_win.resizable(False, False)
        self.main_win.protocol("WM_DELETE_WINDOW", self.destroy)
        self.tileset_pixmap = tk.Canvas(self.main_win, bg='#FF0000',
                                        width=256, height=16 * self.chr_rom_size // 256,
                                        scrollregion=(0,0,256,16 * self.chr_rom_size // 128))
        self.tileset_pixmap.grid(row=0, column=0)
        self.tileset_pixmap.bind("<Button-1>", self.tileset_click)
        self.tileset_pixmap.bind("<Button-4>", self.tileset_mousewheel)
        self.tileset_pixmap.bind("<Button-5>", self.tileset_mousewheel)

        scroll_y = ttk.Scrollbar(self.main_win, orient="vertical",
                                 command=self.tileset_pixmap.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")

        self.tileset_pixmap.configure(yscrollcommand=scroll_y.set) #, xscrollcommand=scroll_x.set)

        self.edit_win = tk.Toplevel(self.main_win)
        self.edit_win.wm_title('Tile #' + str(self.current_tile_num))
        self.edit_win.geometry('128x192')
        self.edit_win.resizable(False, False)
        self.edit_win.protocol("WM_DELETE_WINDOW", self.destroy)
        self.edit_pixmap = tk.Canvas(self.edit_win, width=128, height=128, bg='#000000')
        self.edit_pixmap.grid(column=0, row=0, sticky="new")
        self.edit_pixmap.bind("<Button-1>", self.edit_leftclick)
        self.edit_pixmap.bind("<B1-Motion>", self.edit_leftclick)
        self.edit_pixmap.bind("<Button-3>", self.edit_rightclick)
        self.edit_pixmap.bind("<B3-Motion>", self.edit_rightclick)

        self.colors_pixmap = tk.Canvas(self.edit_win, width=128, height=32, bg='#00FF00')
        self.colors_pixmap.grid(column=0, row=1, sticky="sew")
        self.colors_pixmap.bind("<Button-1>", self.colors_leftclick)
        self.colors_pixmap.bind("<Button-3>", self.colors_rightclick)
        self.colors_configure()

        self.layer_win = tk.Toplevel(self.main_win)
        self.layer_win.wm_title('Tile Layer')
        self.layer_win.geometry('512x480')
        self.layer_win.resizable(False, False)
        self.layer_win.protocol("WM_DELETE_WINDOW", self.destroy)
        self.layer_pixmap = tk.Canvas(self.layer_win, width=512, height=480, bg='#00FF00')
        self.layer_pixmap.pack()
        self.layer_pixmap.bind("<Button-1>", self.layer_click)
        self.layer_configure()

        # Setup user interface

        # main_ui = """<ui>
        #               <menubar name="MenuBar">
        #                <menu action="File">
        #                 <menuitem action="New"/>
        #                 <menuitem action="Open"/>
        #                 <menuitem action="Save"/>
        #                 <menuitem action="Quit"/>
        #                </menu>
        #                <menu action="Edit">
        #                 <menuitem action="Config"/>
        #                </menu>
        #               </menubar>
        #              </ui>
        #           """
        self.main_menubar = tk.Menu(self.main_win)
        self.main_win.config(menu = self.main_menubar)

        self.main_file_menu = tk.Menu(self.main_menubar)
        self.main_file_menu.add_command(label="New", command=self.new_tileset)
        self.main_file_menu.add_command(label="Open", command=self.open_tileset)
        self.main_file_menu.add_command(label="Save", command=self.save_tileset)
        self.main_file_menu.add_command(label="Quit", command=self.destroy)
        self.main_menubar.add_cascade(label="File", menu=self.main_file_menu)

        self.main_edit_menu = tk.Menu(self.main_menubar)
        self.main_edit_menu.add_command(label="Config", command=self.config_tileset)

        self.main_menubar.add_cascade(label="Edit", menu=self.main_edit_menu)



        # Widget display
        self.new_tileset()

        self.tileset_pixmap.focus_force()


    # Generic callbacks

    def destroy(self):
        if not self.check_to_save_tileset():
            return False
        self.main_win.destroy()
        return True

    # Menubar callbacks

    def check_to_save_tileset(self ):
        if self.modified:
            result = messagebox.askyesnocancel("Question", "Save current file?")

            if result is None:
                # Cancel
                return False
            if not result:
                # No
                return True
            # Yes
            if not self.save_tileset():
                messagebox.showerror("Error", "Unable to save tile set!")
                return False
        return True

    def new_tileset(self):
        if not self.check_to_save_tileset():
            return False

        self.chr_rom_size = 8192
        self.format = 'raw'
        self.tile_data = [None]* (self.chr_rom_size//BYTES_PER_TILE)

        self.tileset_configure()

        self.modified = False
        self.current_tile_num = 0
        if self.tile_data[self.current_tile_num] is None:
            self.tile_data[self.current_tile_num] = [[0]*ROWSPAN for x in range(ROWSPAN)]
        self.update_tile_edit()
        return True


    def open_tileset(self):
        if not self.check_to_save_tileset():
            return False

        filename = filedialog.askopenfilename(filetypes=nes_filetypes)
        if not filename:
            return False
        return self.do_open( filename )



    def close_tileset(self):
        return self.new_tileset()


    def save_tileset(self):
        # if self.filename:
        # do same as if there's no filename for now
        filename = filedialog.asksaveasfilename(filetypes=nes_filetypes)
        if not filename:
            return False

        if self.do_save( filename ):
            return True

        messagebox.showerror("Error", "Unable to save to `{}`".format(filename))
        return False

    def config_tileset(self):
        if self.format != 'raw':
            msg = "Only supported in raw mode.\nUse File->New\nto reset raw mode"
            messagebox.showwarning("Warning", msg)
            return False

        result = simpledialog.askinteger('Configuration', "CHR ROM Size (Bytes)",
                                         initialvalue=self.chr_rom_size)
        if result is None:
            return False
        try:
            self.chr_rom_size = result
            if self.chr_rom_size % 8192:
                self.chr_rom_size = 8192 + self.chr_rom_size - (self.chr_rom_size % 8192)
            if not self.chr_rom_size:
                self.chr_rom_size = 8192

            self.tileset_configure()

            self.current_tile_num = 0
            self.update_tile_edit()
            return True
        except ValueError:
            messagebox.showerror("Error", "Invalid size specified.")
        except Exception as err:
            messagebox.showerror("Error", f"Unexpected {err=}, {type(err)=}")
            raise
        return False



    # Tile set callbacks

    def tileset_configure(self):
        # Clear out draw window (done in configure before, but trying to avoid
        # having my graphics drawn over.
        self.tileset_pixmap.config(scrollregion=(0,0,256,16 * self.chr_rom_size // 128))
        self.tileset_pixmap.create_rectangle(0, 0, 256, 16 * self.chr_rom_size // 128,
                                             fill='#FF0000')
        self.tileset_pixmap.create_rectangle(0, 0, 256, 16 * self.chr_rom_size // 256,
                                             fill='#000000', outline='#FF00FF')
        x = 0
        y = 0
        for i, tile in enumerate(self.tile_data):
            self.draw_tile( self.tileset_pixmap, x, y, TILESCALE, tile, tileset_palette)
            if i == self.current_tile_num:
                self.tileset_pixmap.create_rectangle(x, y, x+TILEOFFSET-1, y+TILEOFFSET-1,
                                             fill='', outline='#00FFFF')
            x += TILEOFFSET
            if x >= TILESPAN*TILEOFFSET:
                y += TILEOFFSET
                x = 0


    def tileset_click(self, event):
        x = self.tileset_pixmap.canvasx(event.x)
        y = self.tileset_pixmap.canvasy(event.y)
        i = self.box_number(int(x), int(y), 16, 16, 16)
        if i != self.current_tile_num:
            if i >= len(self.tile_data):
                messagebox.showerror("Error", "Tile is beyond allocated ROM size.")
                return
            if self.tile_data[i] is None:
                self.tile_data[i] = [[0]*ROWSPAN for j in range(ROWSPAN)]
            x = (self.current_tile_num  % TILESPAN) * TILEOFFSET
            y = (self.current_tile_num // TILESPAN) * TILEOFFSET
            self.draw_tile(self.tileset_pixmap, x, y, TILESCALE,
                           self.tile_data[self.current_tile_num], tileset_palette)
            x = (i  % TILESPAN) * TILEOFFSET
            y = (i // TILESPAN) * TILEOFFSET
            self.tileset_pixmap.create_rectangle(x, y, x+TILEOFFSET-1, y+TILEOFFSET-1,
                                             fill='', outline='#00FFFF')
            self.current_tile_num=i

            # Update edit box with new selected tile
            self.update_tile_edit()


    def tileset_mousewheel(self, event):
        if event.num==4: # Up
            self.tileset_pixmap.yview_scroll(-1, "units")
        else: # Down
            self.tileset_pixmap.yview_scroll(1, "units")

    # Tile edit area callbacks

    def edit_leftclick(self, event):
        self.modified = True
        self.draw_tile_pixel(event.x, event.y, 16, 16, self.current_col)

    def edit_rightclick(self, event):
        self.modified = True
        self.draw_tile_pixel(event.x, event.y, 16, 16, 0)


    # Tile edit color selection callbacks

    def colors_configure(self):
        for i in range(4):
            outline_color = color = get_color_string( nes_palette[self.current_pal[i]] )
            if i == self.current_col:
                outline_color = "#00FFFF"
            self.draw_box_i( self.colors_pixmap, i, 32, 32, 4, color, outline_color)

    def colors_leftclick(self, event):
        i = self.current_col
        color = get_color_string( nes_palette[self.current_pal[i]] )
        self.draw_box_i( self.colors_pixmap, i, 32, 32, 4, color)
        self.current_col = i = self.box_number(event.x, event.y, 32, 32, 4)
        color = get_color_string( nes_palette[self.current_pal[i]] )
        self.draw_box_i( self.colors_pixmap, i, 32, 32, 4, color, "#00FFFF")

    def colors_rightclick(self, event):
        col = self.box_number( event.x, event.y, 32, 32, 4)
        self.create_palette_win(col)


    # Tile layer area callbacks

    def layer_configure(self):
        self.layer_pixmap.create_rectangle( 0, 0, 512, 480, fill="#000000")
        return True

    def layer_click(self, event):
        self.lay_tile(event.x, event.y, 16, 16)


    # Palette selection window functions and callbacks

    def create_palette_win(self, col):
        # Create window for selecting color palette
        palette_win = tk.Toplevel(self.main_win)
        palette_win.wm_title('Color Chooser #' + str(col))
        palette_win.resizable(False, False)

        palette_pick = tk.Canvas(palette_win, width=256, height=64, bg='#FFFFFF')
        palette_pick.grid(column=0, row=0, sticky="new")

        palette_pick_action = lambda event : self.palette_click( event, col )
        palette_pick.bind("<Button-1>", palette_pick_action)

        palette_close = ttk.Button(palette_win, text = 'Close', command = palette_win.destroy)
        palette_close.grid(column=0, row=1, sticky="sew")

        # Draws the colors blocks for selecting from the NES palette
        for i in range(len(nes_palette)):
            color = get_color_string(nes_palette[i])
            self.draw_box_i(palette_pick, i, 16, 16, 16, color)

    def palette_click(self, event, col):
        # Handle change in palette changing displayed colors to reflect it
        new_color = self.box_number(event.x, event.y, 16, 16, 16)

        # Current palette info updated when old info no longer needed
        self.current_pal[col] = new_color

        # Redraw the colors bar to show updated palette selection
        self.colors_configure()

        # Redraw the edit window with updated palette
        self.update_tile_edit()


    # Other functions

    def box_number(self, x, y, x_len, y_len, row_span):
        """
        Finds the box number which contains the coordinates (x,y).
        Assumes rectangle is split up into boxes each of size x_len> by y_len,
        the boxes are numbered 0 through box_num starting at the upper left
        corner of the rectangle, and row_span boxes in a row.

        Returns the box number which contains the coordinates x, y
        """
        return (x // x_len) + row_span * (y // y_len)


    def draw_box_i( self, canvas, i, x_len, y_len, rowspan, color, outline_color=None):
        x = (i  % rowspan) * x_len
        y = (i // rowspan) * y_len
        if outline_color is None:
            outline_color = color
        canvas.create_rectangle( x,y,x+x_len-1,y+y_len-1, fill=color, outline=outline_color)


    def draw_tile_pixel( self, x, y, x_len, y_len, tile_color):
        # Figure out discrete row and column of pixel
        col = x // x_len
        row = y // y_len

        # Bounds check row and column
        col = 0 if col < 0 else ROWSPAN-1 if col > (ROWSPAN-1) else col
        row = 0 if row < 0 else ROWSPAN-1 if row > (ROWSPAN-1) else row

        # Update edit pixmap
        # Given the col,row coordinates, and EDITSCALE of the pixels in the tile,
        # and the number of pixels the drawing area is across, draw a box at
        # the tile with the currently selected color
        color = get_color_string(nes_palette[self.current_pal[tile_color]])
        self.edit_pixmap.create_rectangle(col*EDITSCALE, row*EDITSCALE,
                                          (col+1)*EDITSCALE-1, (row+1)*EDITSCALE-1,
                                          fill=color, outline=color)

        # Update tileset pixmap
        # Same as above, but does it for the tileset window
        color = tileset_palette[tile_color]
        tile_row, tile_col = divmod(self.current_tile_num, TILESPAN)
        tile_x = col*TILESCALE+tile_col*TILEOFFSET
        tile_y = row*TILESCALE+tile_row*TILEOFFSET
        self.tileset_pixmap.create_rectangle(tile_x, tile_y,
                                             tile_x+TILESCALE-1, tile_y+TILESCALE-1,
                                             fill=color, outline=color)
        self.tile_data[self.current_tile_num][row][col]=tile_color

        # Updates all the tiles laid on the tile layer of the same kind
        t_info = self.tile_layout[self.current_tile_num]
        if t_info is None:
            return
        for t_layout in t_info:
            if self.tile_at_xy[t_layout[0]][t_layout[1]] == self.current_tile_num:
                color =  get_color_string(nes_palette[t_layout[2][tile_color]])

                lay_x = col * LAYER_SCALE + t_layout[0] * LAYER_OFFSET
                lay_y = row * LAYER_SCALE + t_layout[1] * LAYER_OFFSET

                self.layer_pixmap.create_rectangle(lay_x, lay_y,
                                                   lay_x+LAYER_SCALE-1, lay_y+LAYER_SCALE-1,
                                                   fill=color, outline=color)


    def draw_tile( self, canvas, xoffset, yoffset, scale, tile_data, pal):
        if tile_data is None:
            color = pal[0]
            canvas.create_rectangle(xoffset, yoffset, xoffset+8*scale-1, yoffset+8*scale-1,
                                    fill=color, outline=color)
            return
        for x in range(8):
            for y in range(8):
                color = pal[tile_data[y][x]]
                canvas.create_rectangle(xoffset+x*scale, yoffset+y*scale,
                                        xoffset+(x+1)*scale-1, yoffset+(y+1)*scale-1,
                                        fill=color, outline=color)


    def update_tile_edit(self):
        self.edit_win.wm_title('Tile #' + str(self.current_tile_num))
        cur_pal = [get_color_string(nes_palette[i]) for i in self.current_pal]
        self.draw_tile(self.edit_pixmap, 0, 0, EDITSCALE,
                       self.tile_data[self.current_tile_num], cur_pal)

    def bytes_from_tile(self, tile: 'Tile') ->  bytes:
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

    def do_save(self, filename):
        # Later, try to differentiate between different file formats here
        # but just treat everything like a raw binary file for now
        output_string = b"".join([self.bytes_from_tile(tile) for tile in self.tile_data ])

        with open(filename, 'wb') as fout:
            if self.format == 'raw':
                fout.write(output_string)
            elif self.format == 'ines':
                fout.write(self.ines_data + output_string)
            self.modified = False
            self.filename = filename
        return True

    def print_tile_data(self, tile_data: list['Tile']):
        for tile in tile_data:
            if isinstance(tile, list):
                for row in tile:
                    print(row)
            else:
                print(tile)
            print("---------------------------------------------------------")

    def tile_from_bytes(self, data:bytes) -> 'Tile':
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

    def do_open(self, filename):
        self.filename = filename
        with open(self.filename, 'rb') as fin:
            fdata = fin.read()

        if self.filename.split('.')[-1] == 'nes':
            self.format = 'ines'
            proms = fdata[4]
            croms = fdata[5]
            prom_size = 16 + 16384 * proms
            self.chr_rom_size = 8192 * croms
            self.ines_data = fdata[0: prom_size]
            fdata = fdata[prom_size: prom_size + self.chr_rom_size]
        else:
            self.format = 'raw'
            # if not iNES, make sure data length is a multiple of 8192
            if len(fdata) % 8192 == 0:
                self.chr_rom_size = len(fdata)
            else:
                fdata = fdata + (8192 - (len(fdata) % 8192)) * b'\0'
                self.chr_rom_size = 8192 * (int(len(fdata) / 8192) + 1)

        if len(fdata) < self.chr_rom_size:
            self.chr_rom_size = len(fdata)

        self.tile_data = [self.tile_from_bytes( fdata[i*BYTES_PER_TILE:(i+1)*BYTES_PER_TILE] )
                          for i in range(0, len(fdata)//BYTES_PER_TILE) ]

        # redraw the windows
        self.tileset_configure()

    def lay_tile(self, x, y, x_len, y_len):
        # Draw the current tile at the block in location x, y with a x and y
        # size of x_len and y_len

        # Figure out discrete row and column of pixel
        col = x // x_len
        row = y // y_len

        # Bounds check row and column
        col = 0 if col < 0 else MAX_XBOX if col > MAX_XBOX else col
        row = 0 if row < 0 else MAX_YBOX if row > MAX_YBOX else row

        x_box = col * x_len
        y_box = row * y_len

        cur_pal = self.current_pal[:]
        draw_pal = [get_color_string(nes_palette[i]) for i in cur_pal]
        self.draw_tile(self.layer_pixmap, x_box, y_box, TILESCALE,
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



    # Example from https://www.nesdev.org/wiki/PPU_pattern_tables
    # b"\x41\xC2\x44\x48\x10\x20\x40\x80\x01\x02\x04\x08\x16\x21\x42\x87"
    # [[0, 1, 0, 0, 0, 0, 0, 3],     # .1.....3
    #  [1, 1, 0, 0, 0, 0, 3, 0],     # 11....3.
    #  [0, 1, 0, 0, 0, 3, 0, 0],     # .1...3..
    #  [0, 1, 0, 0, 3, 0, 0, 0],     # .1..3...
    #  [0, 0, 0, 3, 0, 2, 2, 0],     # ...3.22.
    #  [0, 0, 3, 0, 0, 0, 0, 2],     # ..3....2
    #  [0, 3, 0, 0, 0, 0, 2, 0],     # .3....2.
    #  [3, 0, 0, 0, 0, 2, 2, 2]]     # 3....222


    def unittest(self):
        base_bytes = b"\x41\xC2\x44\x48\x10\x20\x40\x80\x01\x02\x04\x08\x16\x21\x42\x87"
        print (base_bytes)
        first_tile = self.tile_from_bytes(base_bytes)
        print (first_tile)
        gen_bytes = self.bytes_from_tile(first_tile)
        print (gen_bytes)
        print(base_bytes == gen_bytes)
        sec_tile = self.tile_from_bytes(gen_bytes)
        print (sec_tile)
        print(first_tile == sec_tile)

    def main(self):
        self.main_win.mainloop()

# Main program loop
if __name__ == "__main__":
    nes_tile_edit = NesTileEdit()
    nes_tile_edit.main()
