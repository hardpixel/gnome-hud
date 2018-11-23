import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from subprocess import Popen
from subprocess import PIPE

from gnomehud.utils.menu import DbusMenu


def rgba_to_hex(color):
  red   = int(color.red * 255)
  green = int(color.green * 255)
  blue  = int(color.blue * 255)

  return "#{0:02x}{1:02x}{2:02x}".format(red, green, blue)


class RofiMenu:

  def __init__(self):
    self.settings  = Gtk.Settings.get_default()
    self.context   = Gtk.StyleContext()
    self.dbus_menu = DbusMenu()

    self.settings.set_property('gtk-application-prefer-dark-theme', True)

  @property

  def selection(self):
    selection = self.menu_proc.communicate()[0].decode('utf8').rstrip()
    self.menu_proc.stdin.close()

    return selection

  @property

  def prompt(self):
    return self.dbus_menu.prompt.strip()

  @property

  def items(self):
    string, *menu_items = self.dbus_menu.actions

    for menu_item in menu_items:
      string += '\n' + menu_item

    return string.encode('utf-8')

  @property

  def font_name(self):
    return self.settings.get_property('gtk-font-name')

  @property

  def gtk_theme_colors(self):
    colors = {
      'bg':           self.lookup_color('theme_bg_color'),
      'fg':           self.lookup_color('theme_fg_color'),
      'selected_bg':  self.lookup_color('theme_selected_bg_color'),
      'selected_fg':  self.lookup_color('theme_selected_fg_color'),
      'selected_br':  self.lookup_color('theme_selected_border_color'),
      'error_bg':     self.lookup_color('error_bg_color'),
      'error_fg':     self.lookup_color('error_fg_color'),
      'info_bg':      self.lookup_color('info_bg_color'),
      'unfocused_fg': self.lookup_color('theme_unfocused_fg_color'),
      'unfocused_bg': self.lookup_color('theme_unfocused_bg_color'),
      'unfocused_br': self.lookup_color('theme_unfocused_border_color')
    }

    for name, color in colors.items():
      colors[name] = rgba_to_hex(color)

    return colors

  @property

  def theme_colors(self):
    colors = {
      'window': [
        self.gtk_theme_colors['bg'],
        self.gtk_theme_colors['selected_br'],
        self.gtk_theme_colors['unfocused_br']
      ],
      'normal': [
        self.gtk_theme_colors['bg'],
        self.gtk_theme_colors['fg'],
        self.gtk_theme_colors['bg'],
        self.gtk_theme_colors['selected_bg'],
        self.gtk_theme_colors['selected_fg']
      ],
      'urgent': [
        self.gtk_theme_colors['bg'],
        self.gtk_theme_colors['fg'],
        self.gtk_theme_colors['bg'],
        self.gtk_theme_colors['error_bg'],
        self.gtk_theme_colors['error_fg']
      ]
    }

    for name, color in colors.items():
      colors[name] = ', '.join(color)

    return colors

  @property

  def theme_string(self):
    style = """
      #window { location: north; anchor: north; border: 1px;
        width: 800px; padding: 0; margin: 32px 0 0; }

      #listview { border: 1px 0 0; spacing: 0;
        scrollbar: false; padding: 0; lines: 6; }

      #inputbar { padding: 10px; }
      #element { border: 0; padding: 6px 10px; }
    """

    return style

  def lookup_color(self, key):
    return self.context.lookup_color(key)[1]

  def open_menu(self):
    options = [
      'rofi',
      '-i',
      '-dmenu',
      '-theme-str', self.theme_string,
      '-p', self.prompt,
      '-font', self.font_name,
      '-color-window', self.theme_colors['window'],
      '-color-normal', self.theme_colors['normal'],
      '-color-urgent', self.theme_colors['urgent']
    ]

    self.menu_proc = Popen(options, stdout=PIPE, stdin=PIPE)
    self.menu_proc.stdin.write(self.items)

  def run(self):
    self.open_menu()
    self.dbus_menu.activate(self.selection)
