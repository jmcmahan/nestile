#!/usr/bin/env python3
"""
NES Tile Editor
A program for creating and editing graphics for NES programs
Author: Jerry McMahan Jr. (ported to python3 and tkinter by Theodore Kotz)
Version: 0.3.0
See changes.txt for changes and version info
"""

from collections import namedtuple
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
import os
import re
import sys
import tkinter as tk
import traceback

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

#size of Palette selection Window
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

default_palette = (15, 2, 10, 6)


class NesTileEditTk:
    """Class encapsulating the UI components for the NES Tile Editor program"""
    def __init__(self, event_map: 'NesTileEdit'):
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
        """ Set widget properties. Widget arrangement and display.
        Setup events / signals."""
        self.main_win.wm_title('Tile Set')
        self.main_win.geometry(str(TSET_WIDTH+20)+'x'+str(TSET_HEIGHT+1))
        self.main_win.resizable(False, False)
        self.main_win.protocol("WM_DELETE_WINDOW", event_map.destroy)
        self.tileset_pixmap.config(bg='#FF0000', width=TSET_WIDTH-1, height= TSET_HEIGHT-1)
        self.tileset_pixmap.grid(row=0, column=0)
        self.tileset_pixmap.bind("<Button-1>", self._tileset_click)
        self.tileset_pixmap.bind("<Button-4>", self._tileset_mousewheel)
        self.tileset_pixmap.bind("<Button-5>", self._tileset_mousewheel)

        self.edit_win.wm_title('Tile #')
        self.edit_win.geometry(str(EDIT_WIDTH+1)+'x'+str(EDIT_HEIGHT+COLORS_HEIGHT+2))
        self.edit_win.resizable(False, False)
        self.edit_win.protocol("WM_DELETE_WINDOW", event_map.destroy)
        self.edit_pixmap.config(width=EDIT_WIDTH-1, height=EDIT_HEIGHT-1, bg='#FF0000')
        self.edit_pixmap.grid(column=0, row=0, sticky="new")
        self.edit_pixmap.bind("<Button-1>", self._edit_leftclick)
        self.edit_pixmap.bind("<B1-Motion>", self._edit_leftclick)
        self.edit_pixmap.bind("<Button-3>", self._edit_rightclick)
        self.edit_pixmap.bind("<B3-Motion>", self._edit_rightclick)

        self.colors_pixmap.config(width=EDIT_WIDTH-1, height=COLORS_HEIGHT-1, bg='#FF0000')
        self.colors_pixmap.grid(column=0, row=1, sticky="sew")
        self.colors_pixmap.bind("<Button-1>", self._colors_leftclick)
        self.colors_pixmap.bind("<Button-3>", self._colors_rightclick)

        self.tlayout_win.wm_title('Tile Layer')
        self.tlayout_win.geometry(str(TLAYOUT_WIDTH+1)+'x'+str(TLAYOUT_HEIGHT+1))
        self.tlayout_win.resizable(False, False)
        self.tlayout_win.protocol("WM_DELETE_WINDOW", event_map.destroy)
        self.tlayout_pixmap.config(width=TLAYOUT_WIDTH-1, height=TLAYOUT_HEIGHT-1, bg='#FF0000')
        self.tlayout_pixmap.pack()
        self.tlayout_pixmap.bind("<Button-1>", self._tlayout_click)

    def _build_menu(self, event_map: 'NesTileEdit'):
        """Creates the UI menu"""
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
        main_edit_menu.add_command(label="Cut", command=event_map.tile_copy,
                                        underline=2, accelerator="Ctrl+X")
        self.root.bind_all("<Control-x>", lambda x: event_map.tile_cut())
        main_edit_menu.add_command(label="Copy", command=event_map.tile_copy,
                                        underline=0, accelerator="Ctrl+C")
        self.root.bind_all("<Control-c>", lambda x: event_map.tile_copy())
        main_edit_menu.add_command(label="Paste", command=event_map.tile_paste,
                                        underline=0, accelerator="Ctrl+V")
        self.root.bind_all("<Control-v>", lambda x: event_map.tile_paste())
        main_edit_menu.add_command(
            label="Settings...", command=event_map.config_tileset, underline=5)
        main_menubar.add_cascade(label="Edit", menu=main_edit_menu, underline=0)

        main_tile_menu = tk.Menu(main_menubar)
        main_tile_menu.add_command(label="Shift Up", command=event_map.tile_shift_up,
                                        underline=6, accelerator="Shift+Up")
        self.root.bind_all("<Shift-Up>", lambda x: event_map.tile_shift_up())
        main_tile_menu.add_command(label="Shift Down", command=event_map.tile_shift_down,
                                        underline=6, accelerator="Shift+Down")
        self.root.bind_all("<Shift-Down>", lambda x: event_map.tile_shift_down())
        main_tile_menu.add_command(label="Shift Left", command=event_map.tile_shift_left,
                                        underline=6, accelerator="Shift+Left")
        self.root.bind_all("<Shift-Left>", lambda x: event_map.tile_shift_left())
        main_tile_menu.add_command(label="Shift Right", command=event_map.tile_shift_right,
                                        underline=6, accelerator="Shift+Right")
        self.root.bind_all("<Shift-Right>", lambda x: event_map.tile_shift_right())
        main_tile_menu.add_command(label="Invert Colors", command=event_map.tile_invert,
                                        underline=0, accelerator="~")
        self.root.bind_all("~", lambda x: event_map.tile_invert())
        main_tile_menu.add_command(label="Flip Horizontal", command=event_map.tile_hflip,
                                        underline=0, accelerator="!")
        self.root.bind_all("!", lambda x: event_map.tile_hflip())
        main_tile_menu.add_command(label="Flip Vertical", command=event_map.tile_vflip,
                                        underline=0, accelerator="@")
        self.root.bind_all("@", lambda x: event_map.tile_vflip())
        main_tile_menu.add_command(label="Rotate CCW", command=event_map.tile_ccwrotate,
                                        underline=0, accelerator="#")
        self.root.bind_all("#", lambda x: event_map.tile_ccwrotate())
        main_tile_menu.add_command(label="Rotate CW", command=event_map.tile_cwrotate,
                                        underline=0, accelerator="$")
        self.root.bind_all("$", lambda x: event_map.tile_cwrotate())
        main_menubar.add_cascade(label="Tile", menu=main_tile_menu, underline=0)

    def destroy(self):
        '''Shutsdown and cleans up the UI'''
        self.root.destroy()

    def mainloop(self):
        '''Main event loop of the UI'''
        self.root.mainloop()

    def _tileset_click(self, event):
        x = self.tileset_pixmap.canvasx(event.x)
        y = self.tileset_pixmap.canvasy(event.y)
        i = box_number(int(x), int(y), TSET_OFFSET, TSET_SPAN)
        self.event_map.set_current_tile_num(i)

    def tileset_updatehighlight(self, tile_set: 'TileSet', old_tile_num:int, new_tile_num:int):
        '''Changes the selected tile in the tileset window
        Args:
            tile_set : the tileset shown in the window
            old_tile_num: the number of the tile lose selection
            new_tile_num: the number of the tile to show as selected
        '''
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

    def update_tile_pixel(self, tlayer, tile_num, pal, pixel_update):
        '''Updates a pixel in current tile across all windows'''
        # Update edit pixmap
        color = nes_palette[pal[pixel_update.color]]
        self.edit_pixmap.create_rectangle(
            pixel_update.x*EDITSCALE, pixel_update.y*EDITSCALE,
            (pixel_update.x+1)*EDITSCALE-1, (pixel_update.y+1)*EDITSCALE-1,
            fill=color, outline=color)
        # Update tileset pixmap
        color = tileset_palette[pixel_update.color]
        tile_x = pixel_update.x*TSET_SCALE+(tile_num % TSET_SPAN)*TSET_OFFSET
        tile_y = pixel_update.y*TSET_SCALE+(tile_num // TSET_SPAN)*TSET_OFFSET
        self.tileset_pixmap.create_rectangle(
            tile_x, tile_y, tile_x+TSET_SCALE-1, tile_y+TSET_SCALE-1, fill=color, outline=color)
        # Updates all the tiles laid on the tile layer of the same kind
        t_info = tlayer.tile_layout(tile_num)
        for t_layout in t_info:
            color =  nes_palette[t_layout.palette[pixel_update.color]]
            lay_x = pixel_update.x * TLAYOUT_SCALE + t_layout.x * TLAYOUT_OFFSET
            lay_y = pixel_update.y * TLAYOUT_SCALE + t_layout.y * TLAYOUT_OFFSET
            self.tlayout_pixmap.create_rectangle(
                lay_x, lay_y,lay_x+TLAYOUT_SCALE-1, lay_y+TLAYOUT_SCALE-1,
                fill=color, outline=color)

    def update_tile(self, tlayer, tile_set, tile_num, pal):
        '''Updates current tile across all windows'''
        tile = tile_set[tile_num]
        # Update edit pixmap
        self.edit_redraw_all( tile_num, tile, pal)

        # Update tileset pixmap
        self.tileset_updatehighlight( tile_set, tile_num, tile_num)

        x_off = 0
        y_off = 0
        # create draw callback to draw tile to tlayout_pixmap
        def _draw( start_x, start_y, stop_x, stop_y, color ):
            self.tlayout_pixmap.create_rectangle(
                x_off+start_x*TLAYOUT_SCALE,  y_off+start_y*TLAYOUT_SCALE,
                x_off+stop_x*TLAYOUT_SCALE-1, y_off+stop_y*TLAYOUT_SCALE-1,
                fill=color, outline=color)

        # Updates all the tiles laid on the tile layer of the same kind
        t_info = tlayer.tile_layout(tile_num)
        for t_layout in t_info:
            x_off = t_layout.x * TLAYOUT_OFFSET
            y_off = t_layout.y * TLAYOUT_OFFSET
            tile.draw(_draw, [nes_palette[i] for i in t_layout.palette])

    def _colors_leftclick(self, event):
        i = box_number(event.x, event.y, COLORS_BOXSIZE, COLORS_SPAN)
        self.event_map.update_current_col(i)

    def _colors_rightclick(self, event):
        col = box_number( event.x, event.y, COLORS_BOXSIZE, COLORS_SPAN)
        self._create_palette_win(col)

    def _create_palette_win(self, col):
        """Create window for selecting color from NES palette"""
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
        """Handle change in palette changing displayed colors to reflect it"""
        new_color = box_number(event.x, event.y, PALETTE_BOXSIZE, PALETTE_SPAN)
        self.event_map.palette_update(col, new_color)

    def _tlayout_click(self, event):
        # Figure out discrete row and column of pixel
        col = event.x // TLAYOUT_OFFSET
        row = event.y // TLAYOUT_OFFSET

        # Bounds check row and column
        col = 0 if col < 0 else (TLAYOUT_XSPAN-1) if col > (TLAYOUT_XSPAN-1) else col
        row = 0 if row < 0 else (TLAYOUT_YSPAN-1) if row > (TLAYOUT_YSPAN-1) else row

        self.event_map.lay_tile(col, row)

    def lay_tile(self, col, row, tile: 'Tile', pal: list[int]):
        '''Draw `tile` at position `col`, `row` with `pal`colors in the tile layer
        Args:
            col: the x position
            row: the y position
            tile: the Tile data of the tile
            pal: the color palette a list of 4 nes colors(0-63)
        '''
        x_off = col * TLAYOUT_OFFSET
        y_off = row * TLAYOUT_OFFSET

        # create draw callback to draw tile to tlayout_pixmap
        def _draw( start_x, start_y, stop_x, stop_y, color ):
            self.tlayout_pixmap.create_rectangle(
                x_off+start_x*TLAYOUT_SCALE,  y_off+start_y*TLAYOUT_SCALE,
                x_off+stop_x*TLAYOUT_SCALE-1, y_off+stop_y*TLAYOUT_SCALE-1,
                fill=color, outline=color)

        tile.draw( _draw, [nes_palette[i] for i in pal] )

    def tileset_redraw_all(self, tile_set: 'TileSet', current_tile_num: int):
        '''Redraws the tileset window
        Args:
            tile_set : the tileset shown in the window
            current_tile_num: the number of the tile to show as selected
        '''
        # Clear out draw window (done in configure before, but trying to avoid
        # having my graphics drawn over.
        if tile_set.filename == '':
            self.main_win.wm_title('Tile Set')
        else:
            self.main_win.wm_title(f"Tile Set - {tile_set.filename}")
        self.tileset_pixmap.config(
            scrollregion=(0,0,TSET_WIDTH,(TSET_OFFSET * len(tile_set)) // TSET_SPAN) )
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

    def edit_redraw_all(self, current_tile_num: int, tile: 'Tile', pal: list):
        '''Redraws the main tile view of the tile edit window
        Args:
            current_tile_num: the number of the tile
            tile: the Tile data of the tile
            pal: the current color palette a list of 4 nes colors(0-63)
        '''
        self.edit_win.wm_title('Tile #' + str(current_tile_num))
        self.edit_pixmap.delete('all')
        # create draw callback to draw tile to edit_pixmap
        def _draw( start_x, start_y, stop_x, stop_y, color ):
            self.edit_pixmap.create_rectangle(
                start_x*EDITSCALE, start_y*EDITSCALE,
                stop_x*EDITSCALE-1, stop_y*EDITSCALE-1,
                fill=color, outline=color)

        tile.draw( _draw, [nes_palette[i] for i in pal] )

    def colors_redraw_all(self, pal: list, selected_col: int):
        '''Redraws the tile color display in the tile edit window
        Args:
            pal: the current color palette a list of 4 nes colors(0-63)
            selected_col: the current tile color (0-3) to show as selected
        '''
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

    def tlayout_redraw_all(self, tile_set: 'TileSet', tlayout: 'TileLayerData'):
        '''Redraws the tilelayout information with updated information.
        Args:
            tile_set : the TileSet to draw tiles from
            tlayout : the TileLayerData to use to populate the display
        '''
        if tlayout.filename == '':
            self.tlayout_win.wm_title('Tile Layer')
        else:
            self.tlayout_win.wm_title(f"Tile Layer - {tlayout.filename}")
        self.tlayout_pixmap.delete('all')
        x_off = 0
        y_off = 0
        empty = Tile()
        # create draw callback to draw tile to tlayout_pixmap
        def _draw( start_x, start_y, stop_x, stop_y, color ):
            self.tlayout_pixmap.create_rectangle(
                x_off+start_x*TLAYOUT_SCALE,  y_off+start_y*TLAYOUT_SCALE,
                x_off+stop_x*TLAYOUT_SCALE-1, y_off+stop_y*TLAYOUT_SCALE-1,
                fill=color, outline=color)

        for x in range(TLAYOUT_XSPAN):
            for y in range(TLAYOUT_YSPAN):
                tle = tlayout.tile_at_xy(x,y)
                if tle is None:
                    empty.draw(_draw, tileset_palette)
                else:
                    tile_set[tle.tile].draw(_draw, [nes_palette[i] for i in tle.palette])
                y_off += TLAYOUT_OFFSET
            x_off += TLAYOUT_OFFSET
            y_off = 0

    def clipboard_set( self, value ):
        """Sets the contents of the clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(value)

    def clipboard_get( self ):
        """Gets the contents of the clipboard"""
        return self.root.clipboard_get()

    @staticmethod
    def showwarning( warning: str ):
        '''Display warning to the user
        Args:
             warning : the message to display
        '''
        messagebox.showwarning("Warning", warning)

    @staticmethod
    def showerror( error: str ):
        '''Display error to the user
        Args:
            error : the message to display
        '''
        messagebox.showerror("Error", error)

    @staticmethod
    def askyesnocancel( question: str ) -> bool:
        '''Ask user a yes or no question with option to cancel
        Args:
            question : str of message to display in box

        Returns:
            True: Yes was selected
            False: No was selected
            None: Request was cancelled
        '''
        return messagebox.askyesnocancel("Question", question)

    @staticmethod
    def askconfigsettings( config: dict, callback: 'Callable' ):
        '''Ask user for configuration settings
        Args:
            config : a dict containing config items and current values
            callback : a function to call when the configuration is complete
        '''
        msg = "CHR ROM Size (Number of 8K blocks)"
        result = simpledialog.askinteger('Configuration', msg,
           initialvalue=config["crom_size"])

        if not result:
            return
        callback({"crom_size": result})

def box_number(x:int, y:int, scale:int, row_span:int) -> int:
    """Returns the box index starting at the top left and going left to right which contains the
    coordinates (x, y), assuming each box is scale by scale and there are row_span boxes in a row.
    """
    return (x // scale) + row_span * (y // scale)


class Tile:
    """Represents a single 8x8 Tile that could be mapped to various windows"""
    def __init__(self, data_yx=None):
        if data_yx is None:
            self._pixels = None
        elif isinstance(data_yx, list):
            self._pixels = [ row[:TILESIZE] for row in data_yx[:TILESIZE] ]
        elif isinstance(data_yx, str):
            self.from_str( data_yx )
        elif isinstance(data_yx, Tile):
            if data_yx._pixels is None:
                self._pixels = None
            else:
                self._pixels = [ row[:] for row in data_yx._pixels ]
        elif isinstance(data_yx, (bytes, bytearray)):
            self.frombytes(data_yx)
        else:
            self._pixels = None

    def set(self, x: int, y: int, value: int ):
        """Set color value(0-3) of pixel at (x,y)"""
        if self._pixels is None:
            self._pixels = [[0]*TILESIZE for _ in range(TILESIZE)]
        self._pixels[y][x]=value

    def get(self, x: int, y: int ) -> int:
        """Returns color value(0-3) of pixel at (x,y)"""
        if self._pixels is None:
            return 0
        return self._pixels[y][x]

    def __repr__(self):
        if self._pixels is None:
            return f"{type(self).__name__}(None)"
        return ( f"{type(self).__name__}([\n    " +
            ',\n    '.join( repr(row) for row in self._pixels) + "\n    ])" )

    def __eq__(self, value):
        if self._pixels is None:
            return value==[[0]*TILESIZE for _ in range(TILESIZE)]
        return value==self._pixels

    def tobytes(self) ->  bytes:
        """Returns tile data as bytes containing raw NES graphics data,"""
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
        """Given bytes containing raw NES graphics data (in binary), sets tile data"""
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

    def from_str(self, data: str):
        """Sets tile data given a Tile string repr"""
        clean_whitespace = "".join(data.split())
        if clean_whitespace == f"{type(self).__name__}(None)":
            self._pixels = None
        else:
            regex = re.compile(f"^{type(self).__name__}"r"\(\[\[([0-3,]*)\],"
                                r"\[([0-3,]*)\],\[([0-3,]*)\],\[([0-3,]*)\],"
                                r"\[([0-3,]*)\],\[([0-3,]*)\],\[([0-3,]*)\],"
                                r"\[([0-3,]*)\]\]\)$")
            list_rows=regex.match(clean_whitespace).groups()
            self._pixels=[[int(val) for val in row.split(",")] for row in list_rows]

    def draw(self, draw: 'Callable', pal: list['Color']):
        """Draws the tile on to pixel resolution draw function.
        Args:
            draw: a callback function to request drawing the tile to in an assumed 8x8 grid
                of the form Func(start_x:int, start_y:int, stop_x:int, stop_y:int, 'Color')
            pal: a list of 4 'Color's that will passed into the draw function when drawing.
        """
        if self._pixels is None:
            draw(0, 0, TILESIZE, TILESIZE, pal[0])
            return
        for y, row in enumerate(self._pixels):
            for x, pixel in enumerate(row):
                draw(x, y, x+1, y+1, pal[pixel])

    def shift_up(self):
        """Shifts tile up 1 pixel"""
        if self._pixels is not None:
            self._pixels = self._pixels[1:] + [self._pixels[0]]

    def shift_down(self):
        """Shifts tile down 1 pixel"""
        if self._pixels is not None:
            self._pixels = [self._pixels[-1]] + self._pixels[:-1]

    def shift_left(self):
        """Shifts tile left 1 pixel"""
        if self._pixels is not None:
            self._pixels = [ row[1:]+[row[0]] for row in self._pixels]

    def shift_right(self):
        """Shifts tile right 1 pixel"""
        if self._pixels is not None:
            self._pixels = [ [row[-1]]+row[:-1] for row in self._pixels]

    def invert(self):
        """Inverts colors of pixels in tile"""
        if self._pixels is None:
            self._pixels = [[3]*TILESIZE for _ in range(TILESIZE)]
        else:
            self._pixels = [ [ (3-val) for val in row] for row in self._pixels ]

    def vflip(self):
        """Flips tile vertically"""
        if self._pixels is not None:
            self._pixels.reverse()

    def hflip(self):
        """Flips tile horizontally"""
        if self._pixels is not None:
            for row in self._pixels:
                row.reverse()

    def cwrotate(self):
        """Rotates tile clockwise"""
        if self._pixels is not None:
            self._pixels = [[ self._pixels[y][x] for y in range(TILESIZE-1,-1,-1)]
                            for x in range(TILESIZE)]

    def ccwrotate(self):
        """Rotates tile counter-clockwise"""
        if self._pixels is not None:
            self._pixels = [[ self._pixels[y][x] for y in range(TILESIZE)]
                            for x in range(TILESIZE-1,-1,-1)]

class TileSet:
    """Class holding the tile pixel data for the entire tile set.
    Represents the data in the character ROM
    """
    def __init__(self, rom_size=CROM_INC, filename=None):
        # for pylint data member initialization detection
        self.chr_rom_size = self.tile_data = self.file_format = None
        self.ines_data = self.filename = self.modified = None
        self.reset(rom_size, filename)

    def reset(self, rom_size=None, filename=None):
        """Reinitialize class variables, except data size may be kept."""
        if filename is not None:
            if os.path.isfile(filename):
                self.do_open( filename )
                return
            self.filename = filename
        else:
            self.filename = ''
        if rom_size is not None:
            self.chr_rom_size = rom_size
        self.file_format = 'raw'
        self.modified = False
        # Holds iNES PRG and header data when opening iNES ROM's
        self.ines_data = None
        # Holds the tile bitmaps as 'Tile's
        self.tile_data = [Tile() for _ in range(self.chr_rom_size//BYTES_PER_TILE)]

    def do_save(self, filename: str):
        """Saves the tile data to the file at filename"""
        output_string = b"".join([tile.tobytes() for tile in self.tile_data ])
        with open(filename, 'wb') as fout:
            if self.file_format == 'raw':
                fout.write(output_string)
            elif self.file_format == 'ines':
                fout.write(self.ines_data + output_string)
            self.modified = False
            self.filename = filename

    def do_open(self, filename: str):
        """Reads the tile data from the file at filename"""
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
        """Updates tile at idx to set color of pixel at (x,y)"""
        self.modified = True
        self.tile_data[idx].set(x,y,color)

    def resize(self, new_size):
        """Resize the number of tile data elements"""
        if len(self.tile_data)>new_size:
            self.tile_data = self.tile_data[:new_size]
        else:
            for _ in range(len(self.tile_data),new_size):
                self.tile_data.append(Tile())

    def __getitem__(self, key):
        return self.tile_data[key]

    def __iter__(self):
        return iter(self.tile_data)

    def __len__(self):
        return len(self.tile_data)

    def __repr__(self):
        line = "\n---------------------------------------------------------"
        return f"{type(self).__name__}\n"+"\n".join( repr(tile)+line for tile in self.tile_data)


class TileLayerEntry(namedtuple('TileLayerEntry', ['tile', 'palette'])):
    """Tile and palette of one location"""
    __slots__ = ()


class TileLayout(namedtuple('TileLayout', ['x', 'y', 'palette'])):
    """Location and palette of one tile"""
    __slots__ = ()

class TilePixelUpdate(namedtuple('TilePixelUpdate', ['x', 'y', 'color'])):
    """Location and color of a pixel update"""
    __slots__ = ()

class TileLayerData:
    """Class holding the Tile Layout data in the Tile Layer window"""
    def __init__(self):
        self.modified = False # for pylint initialization detection
        self.filename = None  # for pylint initialization detection
        self.reset()

    def reset(self):
        """Reinitialize class variables"""
        self.filename = ''
        self.modified = False
        # Holds information for drawing tiles on the tile layer
        # Initialize tile map
        self._tile_at_xy = [ TLAYOUT_YSPAN * [None] for _ in range(TLAYOUT_XSPAN) ]

    def tile_layout(self, tile_num: int) -> list('TileLayout'):
        """ Returns a list of tuples containing the x,y positions and
        palettes for a specific tile"""
        return [TileLayout(x, y, data.palette)
                for x, col in enumerate(self._tile_at_xy)
                for y, data in enumerate(col)
                if data is not None and tile_num==data.tile ]

    def lay_tile(self, col: int, row: int, tile_num: int, pal: list[int]):
        '''places tile_num with pal and postion (col, row)'''
        self.modified = True
        self._tile_at_xy[col][row] = TileLayerEntry(tile_num, tuple(pal))

    def tile_at_xy(self, col: int, row: int) -> 'TileLayerEntry':
        '''Returns the tuple of tile number and palette for the tile at positon col,row'''
        tle = self._tile_at_xy[col][row]
        return tle


class NesTileEdit:
    """Class for the NES Tile Editor program"""
    def __init__(self, filename=None):
        # Initialize class variables
        self._tile_set = TileSet(CROM_INC, filename)
        self._tlayer = TileLayerData()
        self._ui = NesTileEditTk(self)
        self.current_pal = list(default_palette)
        # Index into self.current_pal, not nes_palette
        self.current_col = 1
        self.current_tile_num = 0

        # Widget display
        self._ui.tileset_redraw_all(self._tile_set, self.current_tile_num)
        self._ui.edit_redraw_all(self.current_tile_num,
                                self._tile_set[self.current_tile_num],
                                self.current_pal)
        self._ui.colors_redraw_all(self.current_pal, self.current_col)
        self._ui.tlayout_redraw_all(self._tile_set, self._tlayer)

    def _check_to_save_tileset(self ):
        if self._tile_set.modified:
            result = self._ui.askyesnocancel("Save current file?")

            if result is None:
                # Cancel
                return False
            if not result:
                # No
                return True
            # Yes
            if not self.save_as_tileset():
                self._ui.showerror("Unable to save tile set!")
                return False
        return True

    def new_tileset(self):
        '''Callback for New as selected from tileset menu.
        Erases all tile data.
        '''
        if not self._check_to_save_tileset():
            return

        self._tile_set.reset()
        self._tlayer.reset()
        self.current_pal = list(default_palette)
        # Index into self.current_pal, not nes_palette
        self.current_col = 1
        self.current_tile_num = 0
        # Widget display
        self._ui.tileset_redraw_all(self._tile_set, self.current_tile_num)
        self._ui.edit_redraw_all(self.current_tile_num,
                                self._tile_set[self.current_tile_num],
                                self.current_pal)
        self._ui.colors_redraw_all(self.current_pal, self.current_col)
        self._ui.tlayout_redraw_all(self._tile_set, self._tlayer)

    def open_tileset(self):
        '''Callback for Open selected from tileset menu.
        triggers event to load a tileset
        '''
        if not self._check_to_save_tileset():
            return
        filename = filedialog.askopenfilename(filetypes=nes_filetypes)
        if not filename:
            return
        self._tile_set.do_open( filename )
        self._tlayer.reset()
        # redraw the windows
        self.set_current_tile_num(0)
        self._ui.tileset_redraw_all(self._tile_set, self.current_tile_num)
        self._ui.edit_redraw_all(self.current_tile_num,
                                self._tile_set[self.current_tile_num],
                                self.current_pal)
        self._ui.tlayout_redraw_all(self._tile_set, self._tlayer)

    def close_tileset(self):
        '''What does it even mean to Close a tile set?'''
        self.new_tileset()

    def save_as_tileset(self):
        '''Callback for save as selected from tileset menu.
        triggers event to try to save tileset
        '''
        filename = filedialog.asksaveasfilename(
            filetypes=nes_filetypes, initialfile=self._tile_set.filename )
        if not filename:
            return
        self._tile_set.do_save( filename )

    def save_tileset(self):
        '''Callback for save selected from tileset menu.
        triggers event to try to save tileset
        '''
        if not self._tile_set.filename:
            # do save as if there's no filename for now
            self.save_as_tileset()
        else:
            self._tile_set.do_save(self._tile_set.filename)

    def config_tileset(self):
        '''Gets configuration from the user
        Currently only supports changing ROM size
        needs more settings
        '''
        #Open Config dialog
        self._ui.askconfigsettings({"crom_size": 1}, self.process_config)

        #TKOTZ config: CROM Size
        #TKOTZ config: TileSet Scale
        #TKOTZ config: TileSet Palette
        #TKOTZ config: Edit Scale
        #TKOTZ config: Tile Layer Scale
        #TKOTZ config: Tile Layer palette mode

    def process_config(self, config_db: dict ):
        '''Callback that handles updates to the user configurable options
        Args:
            config_db : a dictonary of config items to update
            arg : Descr
        '''
        # Read new Config
        chr_rom_cnt = config_db["crom_size"]
        # Update Settings
        self._tile_set.resize( chr_rom_cnt * CROM_INC // BYTES_PER_TILE )
        if self.current_tile_num > len(self._tile_set):
            self.current_tile_num=0
        # Redraw the windows
        self._ui.tileset_redraw_all(self._tile_set, self.current_tile_num)
        self._ui.edit_redraw_all(self.current_tile_num,
                                self._tile_set[self.current_tile_num],
                                self.current_pal)
        self._ui.colors_redraw_all(self.current_pal, self.current_col)
        self._ui.tlayout_redraw_all(self._tile_set, self._tlayer)

    def palette_update(self, palette_idx, new_nes_color):
        '''Changes one of the colors in the current palette
        Args:
            palette_idx: tile color idx (0-3) to replace
            new_nes_color : an NES pallete color (0-63)
        '''
        self.current_pal[palette_idx] = new_nes_color
        # Redraw the colors bar to show updated palette selection
        self._ui.colors_redraw_all(self.current_pal, self.current_col)
        # Redraw the edit window with updated palette
        self._ui.edit_redraw_all(self.current_tile_num,
                                self._tile_set[self.current_tile_num],
                                self.current_pal)

    def update_current_col(self, new_col):
        '''Updates the tile color the future draws will be in
        Args:
            new_col : the color in the current palette to use (0-3)
        '''
        if new_col != self.current_col:
            self.current_col = new_col
            # Redraw the colors bar to show updated palette selection
            self._ui.colors_redraw_all(self.current_pal, self.current_col)

    def _draw_tile_pixel( self, col, row, tile_color):
        '''Modifies a pixel in the current tile in all windows
        Args:
            col: the x position
            row: the y position
            tile_color: tile pixel color (0-3)
        '''
        self._tile_set.update_tile_pixel(self.current_tile_num,col,row,tile_color)
        self._ui.update_tile_pixel(self._tlayer, self.current_tile_num, self.current_pal,
                                   TilePixelUpdate(col, row, tile_color) )

    def draw_tile_pixel_fg( self, col, row):
        '''Draws a current fg color pixel on the current tile at location (col, row)'''
        self._draw_tile_pixel(col, row, self.current_col)

    def draw_tile_pixel_bg( self, col, row):
        '''Draws a bg color (0) pixel on the current tile at location (col, row)'''
        self._draw_tile_pixel(col, row, 0)

    def lay_tile(self, col, row):
        '''Draw the current tile at the block in location col, row'''
        self._tlayer.lay_tile( col, row, self.current_tile_num, self.current_pal)
        self._ui.lay_tile( col, row, self._tile_set[self.current_tile_num], self.current_pal)

    def set_current_tile_num(self, idx: int ):
        '''Sets by index the current tile that is selected for placing or editing
        Args:
            idx : the tile number
        '''
        if idx != self.current_tile_num and idx < len(self._tile_set):
            self._ui.tileset_updatehighlight(self._tile_set, self.current_tile_num, idx)
            self.current_tile_num = idx
            # Update edit box with new selected tile
            self._ui.edit_redraw_all(self.current_tile_num,
                                    self._tile_set[self.current_tile_num],
                                    self.current_pal)

    def tile_cut(self):
        """Cuts current tile to clipboard"""
        self.tile_copy()
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].frombytes(b"\0" * BYTES_PER_TILE)
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_copy(self):
        """Copies current tile to clipboard"""
        self._ui.clipboard_set( self._tile_set[self.current_tile_num] )

    def tile_paste(self):
        """Pastes clipboard to current tile"""
        try:
            self._tile_set[self.current_tile_num].from_str(self._ui.clipboard_get() )
            self._tile_set.modified=True
        except Exception as err:
            print(err)
            traceback.print_exc()
            self._ui.showerror("Unable to paste as tile")
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_shift_up(self):
        """Shifts current tile up 1 pixel"""
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].shift_up()
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_shift_down(self):
        """Shifts current tile down 1 pixel"""
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].shift_down()
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_shift_left(self):
        """Shifts current tile left 1 pixel"""
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].shift_left()
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_shift_right(self):
        """Shifts current tile right 1 pixel"""
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].shift_right()
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_invert(self):
        """Inverts colors of pixels in current tile"""
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].invert()
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_hflip(self):
        """Flips current tile horizontally"""
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].hflip()
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_vflip(self):
        """Flips current tile vertically"""
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].vflip()
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_cwrotate(self):
        """Rotates current tile clockwise"""
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].cwrotate()
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def tile_ccwrotate(self):
        """Rotates current tile counter-clockwise"""
        self._tile_set.modified=True
        self._tile_set[self.current_tile_num].ccwrotate()
        self._ui.update_tile(self._tlayer, self._tile_set,
                             self.current_tile_num, self.current_pal)

    def destroy(self):
        '''Shutsdown the NesTileEditor'''
        if not self._check_to_save_tileset():
            return False
        self._ui.destroy()
        return True

    def main(self):
        '''The main entry point for the NesTileEditor'''
        self._ui.mainloop()


# Main program loop
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if len(sys.argv) > 2 or '-h' in sys.argv:
            print("Usage: {} [FILE]".format(sys.argv[0]))
            print("\tFILE - sets name of the FILE to open.")
            sys.exit(0)
        else:
            nes_tile_edit = NesTileEdit(sys.argv[1])
    else:
        nes_tile_edit = NesTileEdit()
    nes_tile_edit.main()
