'''
Budgie Commander Applet
©2020 lyon21 <nagygyula21@gmail.com>
'''
import gi.repository
import json 
from os.path import abspath, dirname, join
import copy

gi.require_version('Budgie', '1.0')
from gi.repository import Budgie, GObject, Gtk, Gio, GdkPixbuf, GLib, Gdk
from gi.repository.GdkPixbuf import Pixbuf

class BudgieCommander(GObject.GObject, Budgie.Plugin):
    '''
    Budgie Commander Plugin
    '''
    __gtype_name__ = "BudgieCommander"

    def __init__(self):
        GObject.Object.__init__(self)

    def do_get_panel_widget(self, uuid):
        return BudgieCommanderApplet(uuid)

class BudgieCommanderApplet(Budgie.Applet):
    ''' 
    Budgie Commander Applet
    '''
    manager = None

    def __init__(self, uuid):
        Budgie.Applet.__init__(self)

        self.initApplet()
        self.loadConfig()
        self.buildStack()
        self.buildPopover()
        self.buildPage1()
        self.buildPage2()
        
        self.add(self.eventbox)
        self.show_all()

    def initApplet(self):
        self.eventbox = Gtk.EventBox()
        file_path = join(dirname(abspath(__file__)), 'commander.svg')
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(file_path, 18, 18, preserve_aspect_ratio = True)
        icon = Gtk.Image()
        icon.set_from_pixbuf(pixbuf)
        self.eventbox.add(icon)
        self.eventbox.connect('button-press-event', self.launchApplet)

    def loadConfig(self):
        self.config = GLib.KeyFile.new()
        file_path = join(dirname(abspath(__file__)), 'config.ini')
        self.config.load_from_file(file_path, 0)
        self.config_file = self.config.get_string('general', 'command_file')
        self.config_maxcol = int(self.config.get_string('general', 'maxcol'))
        self.config_imagesize = int(self.config.get_string('general', 'imagesize'))
        self.config_bg = self.config.get_string('general', 'bgcolor')
        self.config_bgalpha = float(self.config.get_string('general', 'bgalpha'))
        self.config_textcolor = self.config.get_string('general', 'textcolor')
        systheme = self.config.get_string('general', 'usesystemstyle')
        if systheme == "0":
            self.config_usesystemstyle = False
        else:
            self.config_usesystemstyle = True
        self.color_bg = Gdk.RGBA()
        self.color_bg.parse(self.config_bg)
        self.color_text = Gdk.RGBA()
        self.color_text.parse(self.config_textcolor)

    def buildStack(self):
        self.stack = Gtk.Stack()
        self.stack.set_homogeneous(False)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

    def buildPopover(self):
        self.popover = Budgie.Popover.new(self.eventbox)
        if not self.config_usesystemstyle:
            color = Gdk.RGBA()
            color.red = self.color_bg.red
            color.blue = self.color_bg.blue
            color.green = self.color_bg.green
            color.alpha = self.config_bgalpha
            self.popover.override_background_color(Gtk.StateType.NORMAL, color)
        self.popover.set_position_policy(Budgie.PopoverPositionPolicy.AUTOMATIC)
        self.popover.set_modal(True)
        self.popover.add(self.stack)

    def buildPages(self):
        for w in self.stack.get_children():
            self.stack.remove(w)
        self.buildPage1()
        self.buildPage2()
        self.popover.show_all()
        self.popover.queue_draw()
        self.popover.show_all()

    def buildPage1(self):
        page1 = Gtk.Box()
        page1.set_name("page1")
        page1.border_width = 0
        self.stack.add_named(page1, "page1")

        to_right = Gtk.Alignment.new(100, 0, 0, 0)
        setting_icon = Gtk.Button()
        setting_icon.set_image(Gtk.Image.new_from_stock("gtk-preferences", Gtk.IconSize.DND))
        setting_icon.set_relief(Gtk.ReliefStyle.NONE)
        setting_icon.connect("button-press-event", self.event_settings)
        to_right.add(setting_icon)

        vbox = Gtk.VBox()
        vbox.add(to_right)

        alignment = Gtk.Alignment.new(0, 0, 0, 0)
        alignment.set_padding(10, 10, 10, 10)
        alignment.add(vbox)
        
        page1.pack_start(alignment, True, True, 0)

        try:
            groups = {}
            with open(self.config_file) as json_file:
                data = json.load(json_file)
                for group in data["groups"]:
                    group_data = {}
                    group_data["title"] = group["title"]
                    group_data["commands"] = {}
                    groups[group["id"]] = group_data

                for command in data["commands"]:
                    command_data = groups[command["group"]]["commands"]
                    command_data[command["id"]] = {}
                    command_data[command["id"]]["title"] = command["title"]
                    command_data[command["id"]]["command"] = command["command"]
                    command_data[command["id"]]["image"] = command["image"]

            for group_id in groups:
                group = groups[group_id]
                group_title = group["title"]
                commands = group["commands"]

                padding = Gtk.Alignment()
                padding.set_padding(10, 10, 0, 0)
                label = Gtk.Label()
                label.set_markup("<span weight='bold' font='14'>" + group_title + "</span>")
                if not self.config_usesystemstyle:
                    label.override_color(Gtk.StateType.NORMAL, self.color_text)
                label.set_xalign(0)
                padding.add(label)
                vbox.add(padding)

                listStore = Gtk.ListStore(Pixbuf, str, str)
                iconview = Gtk.IconView.new()
                if not self.config_usesystemstyle:
                    color = Gdk.RGBA()
                    color.alpha = 0
                    iconview.override_background_color(Gtk.StateType.NORMAL, color)
                iconview.set_model(listStore)
                iconview.set_columns(self.config_maxcol)
                iconview.set_pixbuf_column(0)
                iconview.set_markup_column(1)
                iconview.set_column_spacing(0)
                iconview.set_row_spacing(0)
                iconview.set_activate_on_single_click(True)
                iconview.set_item_orientation(Gtk.Orientation.VERTICAL)
                iconview.connect("item-activated", self.event_command)
                for command_id in commands:   
                    command = commands[command_id]

                    px = Pixbuf.new_from_file_at_scale(
                        filename=command["image"],
                        width=self.config_imagesize,
                        height=self.config_imagesize,
                        preserve_aspect_ratio=True
                    )

                    title = command["title"]
                    if not self.config_usesystemstyle:
                        title = "<span weight='bold' color='" + self.config_textcolor + "'>" + command["title"] + "</span>"

                    listStore.append([px, title, command["command"]])
                    

                vbox.add(iconview)

        except:
            error_label = Gtk.Label()
            error_label.set_markup("<span font='11'>" + "Wrong configuration file!" + "</span>")
            error_label.override_color(Gtk.StateType.NORMAL, self.color_text)
            vbox.pack_start(error_label, True, True, 20)

    def buildPage2(self):
        page2 = Gtk.Box()
        page2.border_width = 0
        self.stack.add_named(page2, "page2")

        grid = Gtk.Grid()
        grid.set_column_spacing(15)
        grid.set_row_spacing(15)

        alignment = Gtk.Alignment.new(0, 0, 0, 0)
        alignment.set_padding(10, 10, 10, 10)
        alignment.add(grid)
        page2.pack_start(alignment, True, True, 0)

        vbox = Gtk.VBox()
        vbox.set_size_request(450, 0)

        ''' 
        command 
        '''
        label_command = Gtk.Label()
        label_command.set_markup("<span weight='bold' font='16'>Command file</span>")
        if not self.config_usesystemstyle:
            label_command.override_color(Gtk.StateType.NORMAL, self.color_text)
        label_command.set_xalign(0)
        entry = Gtk.Entry()
        entry.set_text(self.config_file)
        entry.set_editable(False)
        entry.set_placeholder_text('Command file')
        setting_icon = Gtk.Button()
        setting_icon.set_image(Gtk.Image.new_from_stock("gtk-edit", Gtk.IconSize.DND))
        setting_icon.set_relief(Gtk.ReliefStyle.NONE)
        setting_icon.connect("button-press-event", self.event_filechooser, entry)

        hbox = Gtk.HBox()
        hbox.pack_start(entry, True, True, 0)
        hbox.pack_end(setting_icon, False, False, 0)

        vbox_command = Gtk.VBox()
        vbox_command.add(label_command)
        vbox_command.add(hbox)
        vbox.add(vbox_command)

        ''' 
        columns
        '''
        label_cols = Gtk.Label()
        label_cols.set_markup("<span weight='bold' font='16'>Number of columns</span>")
        label_cols.set_xalign(0)
        if not self.config_usesystemstyle:
            label_cols.override_color(Gtk.StateType.NORMAL, self.color_text)
        scale_cols = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 5, 1)
        scale_cols.set_value(self.config_maxcol)
        if not self.config_usesystemstyle:
            scale_cols.override_color(Gtk.StateType.NORMAL, self.color_text)

        vbox_cols = Gtk.VBox()
        padding_cols = Gtk.Alignment()
        padding_cols.set_padding(20, 0, 0, 0) 
        vbox_cols.add(label_cols)
        vbox_cols.add(scale_cols)
        padding_cols.add(vbox_cols)
        vbox.add(padding_cols)

        ''' 
        image size 
        '''
        label_size = Gtk.Label()
        label_size.set_markup("<span weight='bold' font='16'>Image size</span>")
        label_size.set_xalign(0)
        if not self.config_usesystemstyle:
            label_size.override_color(Gtk.StateType.NORMAL, self.color_text)
        scale_size = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 16, 64, 8)
        scale_size.set_value(self.config_imagesize)
        if not self.config_usesystemstyle:
            scale_size.override_color(Gtk.StateType.NORMAL, self.color_text)

        vbox_size = Gtk.VBox()
        padding_size = Gtk.Alignment()
        padding_size.set_padding(20, 0, 0, 0) 
        vbox_size.add(label_size)
        vbox_size.add(scale_size)
        padding_size.add(vbox_size)
        vbox.add(padding_size)
        
        '''
        system theme
        '''
        label_systh = Gtk.Label()
        label_systh.set_markup("<span weight='bold' font='16'>Use system theme</span>")
        label_systh.set_xalign(0)
        if not self.config_usesystemstyle:
            label_systh.override_color(Gtk.StateType.NORMAL, self.color_text)
        sw_systh = Gtk.Switch.new()
        sw_systh.set_state(bool(self.config_usesystemstyle))
        
        vbox_systh = Gtk.VBox()
        padding_systh = Gtk.Alignment()
        padding_systh.set_padding(20, 0, 0, 0)
        hbox_systh = Gtk.HBox()
        hbox_systh.pack_start(label_systh, True, True, 0)
        hbox_systh.pack_end(sw_systh, False, False, 0)
        vbox_systh.add(hbox_systh)
        padding_systh.add(vbox_systh)
        vbox.add(padding_systh)

        '''
        bg color
        '''
        label_bg = Gtk.Label()
        label_bg.set_markup("<span weight='bold' font='16'>Background color</span>")
        label_bg.set_xalign(0)
        if not self.config_usesystemstyle:
            label_bg.override_color(Gtk.StateType.NORMAL, self.color_text)
        button_bg = Gtk.ColorButton.new_with_rgba(self.color_bg)
        button_bg.connect('color-set', self.event_color_set)
        button_bg.connect('clicked', self.event_color_activated)

        vbox_bg = Gtk.VBox()
        padding_bg = Gtk.Alignment()
        padding_bg.set_padding(20, 0, 0, 0) 
        vbox_bg.add(label_bg)
        vbox_bg.add(button_bg)
        padding_bg.add(vbox_bg)
        vbox.add(padding_bg)

        '''
        bg alpha
        '''
        label_alpha = Gtk.Label()
        label_alpha.set_markup("<span weight='bold' font='16'>Background alpha</span>")
        label_alpha.set_xalign(0)
        if not self.config_usesystemstyle:
            label_alpha.override_color(Gtk.StateType.NORMAL, self.color_text)
        scale_alpha = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.3, 1, 0.01)
        scale_alpha.set_value(self.config_bgalpha)
        if not self.config_usesystemstyle:
            scale_alpha.override_color(Gtk.StateType.NORMAL, self.color_text)

        vbox_alpha = Gtk.VBox()
        padding_alpha = Gtk.Alignment()
        padding_alpha.set_padding(20, 0, 0, 0)
        vbox_alpha.add(label_alpha)
        vbox_alpha.add(scale_alpha)
        padding_alpha.add(vbox_alpha)
        vbox.add(padding_alpha)

        '''
        text color 
        '''
        label_tc = Gtk.Label()
        label_tc.set_markup("<span weight='bold' font='16'>Text color</span>")
        label_tc.set_xalign(0)
        if not self.config_usesystemstyle:
            label_tc.override_color(Gtk.StateType.NORMAL, self.color_text)
        button_tc = Gtk.ColorButton.new_with_rgba(self.color_text)
        button_tc.connect('color-set', self.event_color_set)
        button_tc.connect('clicked', self.event_color_activated)
        
        vbox_tc = Gtk.VBox()
        padding_tc = Gtk.Alignment()
        padding_tc.set_padding(20, 0, 0, 0) 
        vbox_tc.add(label_tc)
        vbox_tc.add(button_tc)
        padding_tc.add(vbox_tc)
        vbox.add(padding_tc)

        '''
        copyright
        '''
        label_cr = Gtk.Label()
        label_cr.set_label("Copyright ©2020 Lyon21 <nagygyula21@gmail.com>")
        label_cr.set_xalign(100)
        if not self.config_usesystemstyle:
            label_cr.override_color(Gtk.StateType.NORMAL, self.color_text)

        vbox_cr = Gtk.VBox()
        padding_cr = Gtk.Alignment()
        padding_cr.set_padding(10, 0, 0, 0) 
        vbox_cr.add(label_cr)
        padding_cr.add(vbox_cr)
        vbox.add(padding_cr)
        
        grid.attach(vbox, 0, 0, 2, 1)

        '''
        back button
        '''
        button_back = Gtk.Button.new_with_label("Back")
        button_back.connect("button-press-event", self.event_back)
        grid.attach(button_back, 0, 1, 1, 1)

        '''
        save button
        '''
        button_save = Gtk.Button.new_with_label("Save")
        button_save.connect("button-press-event", self.event_save, entry, scale_cols, scale_size, button_bg, button_tc, sw_systh, scale_alpha)
        grid.attach(button_save, 1, 1, 1, 1)

    def launchApplet(self, widget, event):
        self.popover.show_all()

    def showPage1(self):
        self.stack.set_visible_child_name("page1")

    def showPage2(self):
        self.stack.set_visible_child_name("page2")

    def event_command(self, widget, event):
        widget.unselect_all()
        model = widget.get_model()
        iter = model.get_iter(event)
        command = model.get_value(iter, 2)
        GLib.spawn_command_line_async(command)
        self.popover.hide()

    def event_settings(self, widget, event):
        self.showPage2()

    def event_back(self, widget, event):
        self.buildPages()
        self.showPage1()

    def event_color_activated(self, widget):
        self.popover.set_visible(False)

    def event_color_set(self, widget):
        self.popover.set_visible(True)

    def event_save(self, widget, event, entry, maxcol, imagesize, bg, text, sw, alpha):
        self.config_file = entry.get_text()
        self.config_maxcol = maxcol.get_value()
        self.config_imagesize = imagesize.get_value()
        self.config_bg = bg.get_color().to_string()
        self.config_textcolor = text.get_color().to_string()
        self.config_usesystemstyle = bool(sw.get_state())
        self.config_bgalpha = alpha.get_value()

        self.color_bg.parse(self.config_bg)
        self.color_text.parse(self.config_textcolor)
        if not self.config_usesystemstyle:
            color = Gdk.RGBA()
            color.red = self.color_bg.red
            color.blue = self.color_bg.blue
            color.green = self.color_bg.green
            color.alpha = self.config_bgalpha
            self.popover.override_background_color(Gtk.StateType.NORMAL, color)
        else:
            self.popover.override_background_color(Gtk.StateType.NORMAL, None)

        self.config.set_string("general", "command_file", self.config_file)
        self.config.set_string("general", "maxcol", str(int(self.config_maxcol)))
        self.config.set_string("general", "imagesize", str(int(self.config_imagesize)))
        self.config.set_string("general", "usesystemstyle", str(float(self.config_bgalpha)))
        self.config.set_string("general", "bgcolor", self.config_bg)
        self.config.set_string("general", "bgalpha", str(self.config_bgalpha))
        self.config.set_string("general", "textcolor", self.config_textcolor)
        self.config.set_string("general", "usesystemstyle", str(int(self.config_usesystemstyle)))
        self.config.save_to_file('config.ini')

        self.buildPages()
        self.showPage1()

    def event_filechooser(self, widget, event, entry):
        dialog = Gtk.FileChooserDialog(title=None, parent=None, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON")
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)

        self.popover.set_visible(False)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())

        self.popover.set_visible(True)
        dialog.destroy()
