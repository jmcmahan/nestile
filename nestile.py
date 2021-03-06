#!/usr/bin/env python

# NES Tile Editor
# A program for creating and editing graphics for NES programs
# Author: Jerry McMahan Jr.
# Version: 0.2.0
# See changes.txt for changes and version info


import os
import pygtk
pygtk.require('2.0')
import gtk


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

               

class NesTileEdit:
    """Class for the NES Tile Editor program

    """


    main_ui = """<ui>
                  <menubar name="MenuBar">
                   <menu action="File">
                    <menuitem action="New"/>
                    <menuitem action="Open"/>
                    <menuitem action="Save"/>
                    <menuitem action="Quit"/>
                   </menu>
                   <menu action="Edit">
                    <menuitem action="Config"/>
                   </menu>
                  </menubar>
                 </ui>
              """


    def __init__(self):

        # Initialize class variables
        self.current_pal = [15, 2, 10, 6]
        # Index into self.current_pal, not nes_palette
        self.current_col = 0
        self.current_tile_num = 0
        self.chr_rom_size = 8192
        self.filename = ''
        self.format = 'raw'
        self.modified = False
        # Holds information for drawing tiles on the tile layer 
        self.tile_layout = self.chr_rom_size / 2 * [None]
        self.quitting = False

        # Don't know why the bottom doesn't work, but it seems to make the 
        # lists all tie in to one another - the list comprehension given fixes
        # it (seems to)
        # self.tile_at_xy = 32 * [30 * [None]]
        self.tile_at_xy = [ 30*[None] for x in range(32) ]
        # Holds iNES PRG and header data when opening iNES ROM's
        self.ines_data = None


        # Create widgets
        self.main_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.main_vbox = gtk.VBox()
        self.main_tileset = gtk.DrawingArea()
        self.main_scrolled = gtk.ScrolledWindow()
        self.main_uimanager = gtk.UIManager()

        self.edit_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.edit_vbox = gtk.VBox()
        self.edit_canvas = gtk.DrawingArea()
        self.edit_colors = gtk.DrawingArea()

        self.layer_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.layer_vbox = gtk.VBox()
        self.layer_grid = gtk.DrawingArea()


        # Create backup pixmaps for drawingareas
        self.tileset_pixmap = gtk.gdk.Pixmap(None, 256, 
                                        16 * self.chr_rom_size / 128, 16)
        self.edit_pixmap = gtk.gdk.Pixmap(None, 128, 128, 16)
        self.colors_pixmap = gtk.gdk.Pixmap(None, 128, 128, 16)
        self.layer_pixmap = gtk.gdk.Pixmap(None, 512, 480, 16)
        self.palette_pixmap = gtk.gdk.Pixmap(None, 512, 480, 16)

        
        # Setup user interface
        self.main_accel_group = self.main_uimanager.get_accel_group()
        self.main_action_group = gtk.ActionGroup('NesTileEdit')
        self.main_action_group.add_actions(
           [('File', None, '_File'),
            ('New', None, '_New', None, None, self.new_tileset),
            ('Open', None, '_Open', None, None, self.open_tileset),
            ('Save', None, '_Save', None, None, self.save_tileset),
            ('Quit', gtk.STOCK_QUIT, '_Quit', None, None, self.destroy),
            ('Edit', None, '_Edit'),
            ('Config', None, '_Config', None, None, self.config_tileset)])

        self.main_uimanager.insert_action_group(self.main_action_group, 0)
        self.main_uimanager.add_ui_from_string(self.main_ui)
        self.main_menubar = self.main_uimanager.get_widget('/MenuBar')


        # Set widget properties
        self.main_win.set_title('Tile Set')
        self.main_win.set_size_request(280, 16 * self.chr_rom_size / 256 )
        self.main_win.set_resizable(False)
        self.main_tileset.set_size_request(256, 16 * self.chr_rom_size / 256)
        self.main_scrolled.set_policy(gtk.POLICY_AUTOMATIC, 
                                      gtk.POLICY_AUTOMATIC)
        
        self.edit_win.set_title('Tile #' + str(self.current_tile_num))
        self.edit_win.set_size_request(128, 192)
        self.edit_win.set_resizable(False)
        self.edit_canvas.set_size_request(128, 128)
        self.edit_colors.set_size_request(128, 32)

        self.layer_win.set_title('Tile Layer')
        self.layer_grid.set_size_request(512, 480)
        self.layer_win.set_resizable(False)


        # Setup events / signals
        self.main_win.connect('delete_event', self.delete, 'main')
        self.main_win.connect('destroy', self.destroy)
        self.main_tileset.connect('configure_event', self.tileset_configure)
        self.main_tileset.connect('expose_event', self.tileset_expose)
        self.main_tileset.connect('button_press_event', self.tileset_click)
        self.main_tileset.set_events(gtk.gdk.EXPOSURE_MASK |
                                    gtk.gdk.BUTTON_PRESS_MASK |
                                    gtk.gdk.LEAVE_NOTIFY_MASK |
                                    gtk.gdk._2BUTTON_PRESS)

        self.edit_win.connect('delete_event', self.delete, 'edit')
        self.edit_canvas.connect('configure_event', self.edit_configure)
        self.edit_canvas.connect('expose_event', self.edit_expose)
        self.edit_canvas.connect('button_press_event', self.edit_click)
        self.edit_canvas.connect('motion_notify_event', self.edit_motion)
        self.edit_canvas.set_events(gtk.gdk.EXPOSURE_MASK |
                                    gtk.gdk.BUTTON_PRESS_MASK |
                                    gtk.gdk.LEAVE_NOTIFY_MASK |
                                    gtk.gdk.POINTER_MOTION_MASK |
                                    gtk.gdk.POINTER_MOTION_HINT_MASK)
        self.edit_colors.connect('configure_event', self.colors_configure)
        self.edit_colors.connect('expose_event', self.colors_expose)
        self.edit_colors.connect('button_press_event', self.colors_click)
        self.edit_colors.set_events(gtk.gdk.EXPOSURE_MASK |
                                    gtk.gdk.BUTTON_PRESS_MASK |
                                    gtk.gdk.LEAVE_NOTIFY_MASK |
                                    gtk.gdk._2BUTTON_PRESS)

        self.layer_win.connect('delete_event', self.delete, 'layer')
        self.layer_grid.connect('configure_event', self.layer_configure)
        self.layer_grid.connect('expose_event', self.layer_expose)
        self.layer_grid.connect('button_press_event', self.layer_click)
        self.layer_grid.set_events(gtk.gdk.EXPOSURE_MASK |
                                    gtk.gdk.BUTTON_PRESS_MASK |
                                    gtk.gdk.LEAVE_NOTIFY_MASK |
                                    gtk.gdk._2BUTTON_PRESS)


        # Widget arrangement and display
        self.main_scrolled.add_with_viewport(self.main_tileset)
        self.main_vbox.pack_start(self.main_menubar, False)
        self.main_vbox.pack_end(self.main_scrolled, True, True, 0)
        self.main_win.add(self.main_vbox)
        self.main_win.add_accel_group(self.main_accel_group)

        self.edit_vbox.pack_start(self.edit_canvas, False)
        self.edit_vbox.pack_end(self.edit_colors, False)
        self.edit_win.add(self.edit_vbox)

        self.layer_vbox.pack_start(self.layer_grid, False)
        self.layer_win.add(self.layer_vbox)

        self.main_win.show_all()
        self.edit_win.show_all()
        self.layer_win.show_all()

        # Clear out draw window (done in configure before, but trying to avoid 
        # having my graphics drawn over.

        self.tileset_pixmap.draw_rectangle(
                                self.main_tileset.get_style().black_gc, 
                                True, 0, 0, 256, 16 * self.chr_rom_size / 256)

    # Generic callbacks


    def destroy(self, widget, data=None):
        # don't like this "self.quitting" business, but whatever, it works
        if self.modified and not self.quitting:
            msg = "Save before quitting?"
            dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_QUESTION,
                                       gtk.BUTTONS_YES_NO, msg) 
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            result = dialog.run()
            dialog.destroy()
            if result == gtk.RESPONSE_YES:
                if self.filename:
                    # do same as if there's no filename for now
                    if self.save_tileset(None):
                        self.quitting = True
                        gtk.main_quit()
                    else:
                        return False
                     
                else:
                    if self.save_tileset(None):
                        self.quitting = True
                        gtk.main_quit()
                    else:
                        return False

            elif result == gtk.RESPONSE_CANCEL:
                return False
            else:
                self.quitting = True
                gtk.main_quit()
                    
        else:
            self.quitting = True
            gtk.main_quit()


    def delete(self, widget, event, data=None):
        if data == 'noquit':
            return False

        if self.destroy(self.main_win):
            return False
        else:
            return True


    # Menubar callbacks


    def new_tileset(self, widget):
        if self.modified:
            msg = "Save current file?"
            dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_QUESTION,
                                       gtk.BUTTONS_YES_NO, msg) 
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            result = dialog.run()
            dialog.destroy()
            if result == gtk.RESPONSE_YES:
                if self.filename:
                    # do same as if there's no filename for now
                    if not self.save_tileset(None):
                        return False

            elif result == gtk.RESPONSE_CANCEL:
                return False

        self.chr_rom_size = 8192
                    
        self.main_tileset.set_size_request(256, 16 * self.chr_rom_size / 256)
        self.tileset_pixmap = gtk.gdk.Pixmap(None, 256, 
                                             16 * self.chr_rom_size / 128, 16)

        self.tileset_pixmap.draw_rectangle(
                                self.main_tileset.get_style().black_gc, 
                                True, 0, 0, 256, 16 * self.chr_rom_size / 256)
        self.main_tileset.queue_draw() 
        self.modified = False
        self.current_tile_num = 0
        self.update_tile_edit()
        

    def open_tileset(self, widget):
        if self.modified:
            msg = "Save current file?"
            dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_QUESTION,
                                       gtk.BUTTONS_YES_NO, msg) 
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            result = dialog.run()
            dialog.destroy()
            if result == gtk.RESPONSE_YES:
                if self.filename:
                    # do same as if there's no filename for now
                    if not self.save_tileset(None):
                        return False

            elif result == gtk.RESPONSE_CANCEL:
                return False

        self.file_win = gtk.FileSelection("Open")
        self.file_win.ok_button.connect("clicked", self.do_open)
        self.file_win.cancel_button.connect("clicked", 
                                    lambda w: self.file_win.destroy())
        self.file_win.show()
        return True



    def close_tileset(self, widget):
        pass


    def save_tileset(self, widget, data=None):
        # Bad
        self.save_success = False
        while not self.save_success:
            self.file_win = gtk.FileSelection("Save As")
            self.file_win.ok_button.connect("clicked", self.do_save)
            self.file_win.cancel_button.connect("clicked", 
                                    lambda w: self.file_win.destroy())

            self.file_win.set_modal(True)
            result = self.file_win.run()
            if result == gtk.RESPONSE_CANCEL:
                return False
            else:
                self.file_win.destroy()
                return True

    def config_tileset(self, widget):
        dialog = gtk.Dialog('Configuration', self.main_win, 
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        label = gtk.Label("Size (Bytes)")
        entry = gtk.Entry(6)
        entry.set_text('%d' % self.chr_rom_size)
        dialog.vbox.pack_start(entry, True, True, 0)
        dialog.vbox.pack_start(label, True, True, 0)
        label.show()
        entry.show()
        result = None
        while not result == gtk.RESPONSE_CANCEL:
            result = dialog.run()
            if result == gtk.RESPONSE_OK and self.format == 'raw':
                try:
                    self.chr_rom_size = int(entry.get_text()) 
                    if (self.chr_rom_size % 8192):
                        self.chr_rom_size = 8192 + self.chr_rom_size - \
                                            (self.chr_rom_size % 8192)
                    if not self.chr_rom_size:
                        self.chr_rom_size = 8192
                    dialog.destroy()
                    
                    self.main_tileset.set_size_request(256, 
                                                16 * self.chr_rom_size / 256)
                    pmap = gtk.gdk.Pixmap(None, 256, 
                                          16 * self.chr_rom_size / 128, 16)

                    pmap.draw_rectangle(
                                self.main_tileset.get_style().black_gc, 
                                True, 0, 0, 256, 16 * self.chr_rom_size / 256)
                    gc = self.main_tileset.get_style().fg_gc[gtk.STATE_NORMAL]

                    pmap.draw_drawable(gc, self.tileset_pixmap, 0, 0, 0, 0, 
                                       -1, -1)
                    self.tileset_pixmap = pmap
                    self.main_tileset.queue_draw() 
                    self.current_tile_num = 0
                    self.update_tile_edit()
                    break

                except:
                    msg = "Invalid size specified."
                    err_dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                              gtk.MESSAGE_ERROR,
                                              gtk.BUTTONS_CLOSE, msg)
                    err_dialog.run()
                    err_dialog.destroy()
            elif result == gtk.RESPONSE_OK:
                break

        dialog.destroy()

        return True


    # Tile set callbacks

    def tileset_configure(self, widget, event, data=None):
    # Maybe find something useful to do here - doesn't seem to hurt leaving it 
    # blank

        return True


    def tileset_expose(self, widget, event, data=None):
        x, y, width, height = event.area
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                    self.tileset_pixmap, x, y, x, y, 
                                    width, height)
        return False


    def tileset_click(self, widget, event, data=None):
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.current_tile_num = self.box_number(event.x, event.y, 
                                                    16, 16, 256)
            # add thing to update edit box with selected tile
            self.update_tile_edit()
            return True
        else:
            return False


    # Tile edit area callbacks

    
    def edit_configure(self, widget, event, data=None):
        self.edit_pixmap.draw_rectangle(self.edit_canvas.get_style().black_gc,
                                        True, 0, 0, 128, 128)

        return True


    def edit_expose(self, widget, event, data=None):
        x, y, width, height = event.area
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                    self.edit_pixmap, x, y, x, y, 
                                    width, height)
        return False


    def edit_click(self, widget, event, data=None):
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.modified = True
            self.draw_box(event.x, event.y, 16, 16, 128)
            self.draw_box_tileset(event.x, event.y, 16, 16, 128)
            self.draw_box_layer(event.x, event.y, 16, 16, 128)


    def edit_motion(self, widget, event, data=None):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state

        if state & gtk.gdk.BUTTON1_MASK:
            self.modified = True
            self.draw_box(event.x, event.y, 16, 16, 128)
            self.draw_box_tileset(event.x, event.y, 16, 16, 128)
            self.draw_box_layer(event.x, event.y, 16, 16, 128)

    # Tile edit color selection callbacks


    def colors_configure(self, widget, event, data=None):
        gc = event.window.new_gc()

        for i in range(4):
            x = (i * 32)
            y = 0
            color = self.edit_colors.get_colormap().alloc_color(
                               256 * nes_palette[self.current_pal[i]][0],
                               256 * nes_palette[self.current_pal[i]][1],
                               256 * nes_palette[self.current_pal[i]][2])

            gc.foreground = color
            self.colors_pixmap.draw_rectangle(gc, True, x, y, 32, 32)

        return True


    def colors_expose(self, widget, event, data=None):
        x, y, width, height = event.area
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                    self.colors_pixmap, x, y, x, y, 
                                    width, height)
        return False

    
    def colors_click(self, widget, event, data=None):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.create_palette_win()
        elif event.type == gtk.gdk.BUTTON_PRESS:
            self.current_col = self.box_number(event.x, event.y, 32, 32, 128)
            

    # Tile layer area callbacks


    def layer_configure(self, widget, event, data=None):
        self.layer_pixmap.draw_rectangle(self.layer_grid.get_style().black_gc,
                                        True, 0, 0, 512, 480)
        return True


    def layer_expose(self, widget, event, data=None):
        x, y, width, height = event.area
        widget.window.draw_drawable(
                                widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                self.layer_pixmap, x, y, x, y, width, height)

        return False


    def layer_click(self, widget, event, data=None):
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.lay_tile(event.x, event.y, 16, 16)
            pass


    # Palette selection window functions and callbacks


    def create_palette_win(self):
    
        # Create window for selecting color palette
        self.palette_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.palette_vbox = gtk.VBox()
        self.palette_pick = gtk.DrawingArea()
        self.palette_close = gtk.Button('Close')

        self.palette_win.set_title('Color Chooser')
        self.palette_win.set_resizable(False)
        self.palette_pick.set_size_request(256, 64)

        self.palette_win.connect('delete_event', self.delete, 'noquit')
        self.palette_pick.connect('configure_event', self.palette_configure)
        self.palette_pick.connect('expose_event', self.palette_expose)
        self.palette_pick.connect('button_press_event', self.palette_click)
        self.palette_close.connect('clicked', self.palette_close_click)

        self.palette_pick.set_events(gtk.gdk.EXPOSURE_MASK |
                                     gtk.gdk.BUTTON_PRESS_MASK |
                                     gtk.gdk.LEAVE_NOTIFY_MASK |
                                     gtk.gdk._2BUTTON_PRESS)

        self.palette_vbox.pack_start(self.palette_pick, False)
        self.palette_vbox.pack_end(self.palette_close, False)
        self.palette_win.add(self.palette_vbox)

        self.palette_win.show_all()
        

    def palette_configure(self, widget, event, data=None):

        gc = event.window.new_gc()

        # Draws the colors blocks for selecting from the NES palette
        for i in range(64):
            x = (i * 16) % 256 
            y = (i / 16) * 16
            color = self.palette_pick.get_colormap().alloc_color(
                            nes_palette[i][0] * 256, nes_palette[i][1] * 256,
                            nes_palette[i][2] * 256)
            gc.foreground = color

            self.palette_pixmap.draw_rectangle(gc, True, x, y, 16, 16)

        return True


    def palette_expose(self, widget, event, data=None):
        x, y, width, height = event.area
        widget.window.draw_drawable(
                                widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                self.palette_pixmap, x, y, x, y, width, height)

        return False


    def palette_click(self, widget, event, data=None):
        if event.type == gtk.gdk.BUTTON_PRESS:
            new_color = self.box_number(event.x, event.y, 16, 16, 256)
            if new_color == self.current_pal[0] or \
             new_color == self.current_pal[1] or \
             new_color == self.current_pal[2] or \
             new_color == self.current_pal[3]:
                return
            else:
                self.update_pal(new_color)


    def palette_close_click(self, widget, data=None):
        self.palette_win.destroy()
        return True


    # Other functions


    def update_pal(self, new_color):
        # Handle change in palette changing displayed colors to reflect it

        # FIX ME!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # This code is terrible. It probably causes bugs, is dependent
        # on the color depth chosen, and is way too inefficient. However, 
        # it works for the moment, so it will be fixed later, if at all
        pbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 128, 128)
        pbuf.get_from_drawable(self.edit_pixmap, 
                               self.edit_pixmap.get_colormap(), 0, 0, 0, 0,
                               128, 128)

        old_pix = pbuf.get_pixels()
        new_pix_list = 128*128*3*["\0"]

        

        r_new = chr(nes_palette[new_color][0])
        g_new = chr(nes_palette[new_color][1])
        b_new = chr(nes_palette[new_color][2])

        r_old = nes_palette[self.current_pal[self.current_col]][0]
        g_old = nes_palette[self.current_pal[self.current_col]][1]
        b_old = nes_palette[self.current_pal[self.current_col]][2]



        for i in range(0, len(old_pix), 3):
            if abs(ord(old_pix[i]) - r_old) < 8 and \
             abs(ord(old_pix[i+1]) - g_old) < 8 and \
             abs(ord(old_pix[i+2]) - b_old) < 8:
                new_pix_list[i] = r_new
                new_pix_list[i+1] = g_new
                new_pix_list[i+2] = b_new
            else:
                new_pix_list[i] = old_pix[i]
                new_pix_list[i+1] = old_pix[i+1]
                new_pix_list[i+2] = old_pix[i+2]
                
                
        new_pix = ''.join(new_pix_list)

        gc = self.edit_canvas.get_style().fg_gc[gtk.STATE_NORMAL]
        self.edit_pixmap.draw_rgb_image(gc, 0, 0, 128, 128, 
                                    gtk.gdk.RGB_DITHER_NONE, new_pix, 128*3)


        gc = self.edit_colors.window.new_gc()

        color = self.edit_colors.get_colormap().alloc_color(
                    256 * nes_palette[new_color][0], 
                    256 * nes_palette[new_color][1],
                    256 * nes_palette[new_color][2])

        gc.foreground = color
        self.colors_pixmap.draw_rectangle(gc, True, self.current_col * 32, 0, 
                                                    32, 32)

        # Current palette info updated when old info no longer needed
        self.current_pal[self.current_col] = new_color

        # Redraw the colors bar to show updated palette selection
        self.edit_colors.queue_draw_area(0, 0, 128, 32)
        self.edit_canvas.queue_draw_area(0, 0, 128, 128)




    def box_number(self, x, y, x_len, y_len, rowspan):
        # If a square is split up into boxes each of size x_len by 
        # y_len, the boxes are numbered 0 through box_num starting at the
        # upper left corner of the square, and the square's horizontal size is
        # rowspan, then this function returns the box number which contains 
        # the coordinates x, y.

        #return int(x / x_len) % rowspan + y_len * int(y / y_len)
        return int(x / x_len) % rowspan + int(rowspan / x_len) * int(y / y_len)


    def draw_box(self, x, y, x_len, y_len, rowspan):
        # Given the x,y coordinates, x and y length of the pixels in the tile, 
        # and the number of pixels the drawing area is across, draw a box at 
        # the tile with the currently selected color
        gc = self.edit_canvas.window.new_gc()

        color = self.edit_canvas.get_colormap().alloc_color(
                    256 * nes_palette[self.current_pal[self.current_col]][0],
                    256 * nes_palette[self.current_pal[self.current_col]][1],
                    256 * nes_palette[self.current_pal[self.current_col]][2])
        gc.foreground = color

        x_int = (int(x / x_len) * x_len) % rowspan
        y_int = int(y / y_len) * y_len
        self.edit_pixmap.draw_rectangle(gc, True, x_int, y_int, x_len, x_len)
        self.edit_canvas.queue_draw_area(x_int, y_int, x_len, y_len)


    def draw_box_tileset(self, x, y, x_len, y_len, rowspan):
        # Same as above, but does it for the tileset window
        gc = self.main_tileset.window.new_gc()
        color = self.main_tileset.get_colormap().alloc_color(
                    self.current_col * 21845, 
                    self.current_col * 21845,
                    self.current_col * 21845)
        gc.foreground = color

        x_int = (int(x / x_len) * 2) % rowspan + \
                16 * (self.current_tile_num % 16)
        y_int = int(y / y_len) * 2 + 16 * int(self.current_tile_num / 16)

        self.tileset_pixmap.draw_rectangle(gc, True, x_int, y_int, 2, 2)
        self.main_tileset.queue_draw_area(x_int, y_int, 2, 2)


    def draw_box_layer(self, x, y, x_len, y_len, rowspan):
        # Updates all the tiles laid on the tile layer of the same kind


        if int(x) > rowspan:
            return

        t_info = self.tile_layout[self.current_tile_num]
        if t_info == None:
            return

        for c in t_info:
            
            if self.tile_at_xy[c[0] / 16][c[1] / 16] == self.current_tile_num:
                

                gc = self.layer_grid.window.new_gc()
                color = self.layer_grid.get_colormap().alloc_color(
                        nes_palette[c[2][self.current_col]][0] * 256,
                        nes_palette[c[2][self.current_col]][1] * 256,
                        nes_palette[c[2][self.current_col]][2] * 256)
                gc.foreground = color

                x_int = int(x / x_len) * 2 + c[0]
                y_int = int(y / y_len) * 2 + c[1]

                self.layer_pixmap.draw_rectangle(gc, True, x_int, y_int, 2, 2)
                self.layer_grid.queue_draw_area(x_int, y_int, 2, 2)

            


    def update_tile_edit(self):
        self.edit_win.set_title('Tile #' + str(self.current_tile_num))

        pbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 16, 16)
        pbuf.get_from_drawable(self.tileset_pixmap, 
                    self.main_tileset.get_colormap(), 
                    (self.current_tile_num % 16) * 16,
                    int(self.current_tile_num / 16) * 16,
                    0, 0, 16, 16)
        pbuf_scaled = pbuf.scale_simple(128, 128, gtk.gdk.INTERP_NEAREST)

        old_pix = pbuf_scaled.get_pixels()
        new_pix_l = 128*128*3*["\0"]

        r = []
        g = []
        b = []
        for i in range(4):
            r.append(chr(nes_palette[self.current_pal[i]][0]))
            g.append(chr(nes_palette[self.current_pal[i]][1]))
            b.append(chr(nes_palette[self.current_pal[i]][2]))
             
        # Convert black and white to current palette
        
        for i in range(0, len(old_pix), 3):
            if abs(ord(old_pix[i]) - 0) < 8 and \
             abs(ord(old_pix[i+1]) - 0) < 8 and \
             abs(ord(old_pix[i+1]) - 0) < 8:
                new_pix_l[i] = r[0]
                new_pix_l[i+1] = g[0]
                new_pix_l[i+2] = b[0]

            elif abs(ord(old_pix[i]) - 85) < 8 and \
             abs(ord(old_pix[i+1]) - 85) < 8 and \
             abs(ord(old_pix[i+1]) - 85) < 8:
                new_pix_l[i] = r[1]
                new_pix_l[i+1] = g[1]
                new_pix_l[i+2] = b[1]

            elif abs(ord(old_pix[i]) - 170) < 8 and \
             abs(ord(old_pix[i+1]) - 170) < 8 and \
             abs(ord(old_pix[i+1]) - 170) < 8:
                new_pix_l[i] = r[2]
                new_pix_l[i+1] = g[2]
                new_pix_l[i+2] = b[2]

            else: 
                new_pix_l[i] = r[3]
                new_pix_l[i+1] = g[3]
                new_pix_l[i+2] = b[3]


        new_pix = ''.join(new_pix_l)

        gc = self.edit_canvas.get_style().fg_gc[gtk.STATE_NORMAL]
        self.edit_pixmap.draw_rgb_image(gc, 0, 0, 128, 128,
                                    gtk.gdk.RGB_DITHER_NONE, new_pix, 128*3)

        self.edit_canvas.queue_draw_area(0, 0, 128, 128) 


    def do_save(self, widget, data=None):
        # Later, try to differentiate between different file formats here
        # but just treat everything like a raw binary file for now
        current = self.filename
        self.filename = self.file_win.get_filename()
        if self.filename != current:
            if os.path.exists(self.filename):
                dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                           gtk.MESSAGE_QUESTION,
                                           gtk.BUTTONS_YES_NO, 
                                           "Overwrite %s?" % self.filename)
                result = dialog.run()
                dialog.destroy()
                if result != gtk.RESPONSE_YES:
                    self.save_success = False
                    self.filename = current
                    return False

        pbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 
                            self.tileset_pixmap.get_size()[0],
                            self.tileset_pixmap.get_size()[1])
        pbuf.get_from_drawable(self.tileset_pixmap, 
                            self.main_tileset.get_colormap(),
                            0, 0, 0, 0, -1, -1)
        pixels = pbuf.get_pixels()

        pix_list = len(pixels) / 12 * [0]
        for i in range(len(pix_list)):
            pix_list[i] = ord(pixels[i * 6]) / 64


        for i in range(len(pix_list) / 128):
            for j in range(128):
                pix_list[i*128 + j] = ord(pixels[i*12*128 + j*6]) / 64
            
        output_list = [self.tile_string_from_list(pix_list, x, 128) for \
                        x in range(len(pix_list) / 128)]

        output_string = ''.join(output_list)
            
        f = open(self.filename, 'wb')
        if self.format == 'raw':
            f.write(output_string)
        elif self.format == 'ines':
            f.write(self.ines_data + output_string)
        f.close()
        self.modified = False
        self.save_success = True
        return True
            

    def tile_string_from_list(self, list, tile_num, rowspan):
        # Returns a string representing the tile, 'tile_num', for         
        # the list 'rowspan' pixels wide.
        # The string is the binary data of the tile in NES graphics format

        x_len = 8
        y_len = 8
        x = x_len * (tile_num % int(rowspan / x_len))
        y = y_len * int(tile_num / int(rowspan / x_len))
        offset = x + y * rowspan
        
        return_string = 16*['0']
        
        for j in range(8):
            low = 0
            high = 0
            for i in range(8):
                low = low + ((list[offset + j * rowspan + i] % 2) << (7 - i))
                high = high + (int(list[offset + 
                               j * rowspan + i] / 2) << (7 - i))

            return_string[j] = chr(low)
            return_string[j + 8] = chr(high)

        return ''.join(return_string)
        

    def do_open(self, widget, data=None):
        self.filename = self.file_win.get_filename()
        self.file_win.destroy()
        f = open(self.filename, 'rb')
        fdata = f.read()
        f.close()

        if self.filename.split('.')[-1] == 'nes':
            self.format = 'ines'
        else:
            self.format = 'raw'

        if self.format == 'ines':
            proms = ord(fdata[4])
            croms = ord(fdata[5])
            self.ines_data = fdata[0: 16 + 16384 * proms]
            tmp = fdata[16 + 16384 * proms: 16 + 16384 * proms + 8192 * croms]
            fdata = tmp
            self.chr_rom_size = 8192 * croms 
        else:
            # if not iNES, make sure data length is a multiple of 8192
            if len(fdata) % 8192 == 0:
                self.chr_rom_size = len(fdata)
            else:
                fdata = fdata + (8192 - (len(fdata) % 8192)) * '\0'
                self.chr_rom_size = 8192 * (int(len(fdata) / 8192) + 1)
            

        if len(fdata) < self.chr_rom_size:
            self.chr_rom_size = len(fdata)

        self.main_tileset.set_size_request(256, 16 * self.chr_rom_size / 256)
        self.tileset_pixmap = gtk.gdk.Pixmap(None, 256, 
                                        16 * self.chr_rom_size / 128, 16)

        self.tile_layout = self.chr_rom_size / 2 * [None]
    
        pix_list = 128 * 8 * self.chr_rom_size / 256 * 3 * ["\0"]

        for i in range(self.chr_rom_size / 16):
            self.tile_list_from_string(fdata, pix_list, i, 128)
        
        self.tile_list_from_string(fdata, pix_list, 0, 128)
        pix_string = ''.join(pix_list)


        # Terrible...
        pmap = gtk.gdk.Pixmap(None, 128, 8 * self.chr_rom_size / 256, 16)
        gc = self.main_tileset.get_style().fg_gc[gtk.STATE_NORMAL]
        pmap.draw_rgb_image(gc, 0, 0, 128, 8 * self.chr_rom_size / 256,
                            gtk.gdk.RGB_DITHER_NONE, pix_string, 128*3)

        pbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 128, 
                              8 * self.chr_rom_size / 256)

        pbuf.get_from_drawable(pmap, self.main_tileset.get_colormap(),
                                0, 0, 0, 0, -1, -1)

        pbuf_scaled = pbuf.scale_simple(256, 16 * self.chr_rom_size / 256,
                                        gtk.gdk.INTERP_NEAREST)

        self.tileset_pixmap.draw_pixbuf(gc, pbuf_scaled, 0, 0, 0, 0,
                            256, 16 * self.chr_rom_size / 256,
                            gtk.gdk.RGB_DITHER_NONE)

        self.current_tile_num = 0
        self.update_tile_edit()

        self.main_tileset.queue_draw()
        self.modified = False


    def tile_list_from_string(self, string, list, tile_num, rowspan):
        # Given a string containing NES graphics data (in binary), a
        # list representing the RGB data for an image to be displayed, 
        # and a tile number, add the tile to the list

        x_len = 8
        y_len = 8
        x = x_len * (tile_num % int(rowspan / x_len))
        y = y_len * int(tile_num / int(rowspan / x_len))

        tiles = [ord(a) for a in string[tile_num * 16 : tile_num * 16 + 16]]

        offset = (x + y * rowspan) * 3

        for j in range(8):

            for i in range(8):
                # Add twice to multiply by 2 (supposedly faster)
                v = (((tiles[j] >> (7 - i)) & 1) + \
                    ((tiles[j+8] >> (7 - i)) & 1) + \
                    ((tiles[j+8] >> (7 - i)) & 1)) * 85

                list[offset + (i + rowspan * j) * 3] = chr(v)
                list[offset + (i + rowspan * j) * 3 + 1] = chr(v)
                list[offset + (i + rowspan * j) * 3 + 2] = chr(v)


    def lay_tile(self, x, y, x_len, y_len):
        # Draw the current tile at the block in location x, y with a x and y
        # size of x_len and y_len

        x_box = int(x) - (int(x) % 16)
        y_box = int(y) - (int(y) % 16)


        pbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 128, 128)
        pbuf.get_from_drawable(self.edit_pixmap, 
                               self.edit_canvas.get_colormap(), 0, 0, 0, 0, 
                               -1, -1)
        pbuf_scaled = pbuf.scale_simple(16, 16, gtk.gdk.INTERP_NEAREST)
        self.layer_pixmap.draw_pixbuf(None, pbuf_scaled, 0, 0, x_box, y_box, 
                                    -1, -1, gtk.gdk.RGB_DITHER_NONE)

        self.layer_grid.queue_draw_area(x_box, y_box, 16, 16)

        self.tile_at_xy[x_box / 16][y_box / 16] = self.current_tile_num
        
        t_info = self.tile_layout[self.current_tile_num]

        cur_pal = [self.current_pal[i] for i in range(4)]
        
        if t_info == None:
            self.tile_layout[self.current_tile_num] = [[x_box, y_box, 
                    cur_pal]]
            return

        not_found = True

        for i in range(len(t_info)):
            if t_info[i][0:2] == [x_box, y_box]:
                self.tile_layout[self.current_tile_num][i] = [x_box, y_box, 
                    cur_pal]
                not_found = False
        
        if not_found:
            self.tile_layout[self.current_tile_num].append([x_box, y_box, 
                    cur_pal])
            

    def main(self):
        gtk.main()



# Main program loop

if __name__ == "__main__":
    nes_tile_edit = NesTileEdit()
    nes_tile_edit.main()

                        
