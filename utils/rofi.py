import re
import gi
import subprocess

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

class RofiMenu:

  def __init__(self, menu_keys, prompt):
    self.menu_items = self.parse_items(menu_keys)
    self.prompt = self.parse_prompt(prompt)
    self.menu = self.open_menu()

  def rgba_to_hex(self, color):
    red = int(color.red * 255)
    green = int(color.green * 255)
    blue = int(color.blue * 255)

    return "#{0:02x}{1:02x}{2:02x}".format(red, green, blue)

  def parse_items(self, menu_keys):
    try:
      string, *menu_items = menu_keys

      for menu_item in menu_items:
        string += '\n' + menu_item
    except ValueError:
      string = 'Quit'

    return string.encode('utf-8')

  def parse_prompt(self, prompt):
    prompt = prompt.split('.')[0]

    if len(prompt) < 2:
      prompt = ''
    else:
      prompt = re.sub(r'_|-', ' ', prompt).strip()

    return prompt.title()

  def gtk_theme_colors(self):
    window = Gtk.Window()
    style_context = window.get_style_context()
    gtk_theme_colors = {
      'bg': style_context.lookup_color('theme_bg_color')[1],
      'fg': style_context.lookup_color('theme_fg_color')[1],
      'selected_bg': style_context.lookup_color('theme_selected_bg_color')[1],
      'selected_fg': style_context.lookup_color('theme_selected_fg_color')[1],
      'error_bg': style_context.lookup_color('error_bg_color')[1],
      'error_fg': style_context.lookup_color('error_fg_color')[1],
      'info_bg': style_context.lookup_color('info_bg_color')[1],
      'unfocused_fg': style_context.lookup_color('theme_unfocused_fg_color')[1],
      'unfocused_bg': style_context.lookup_color('theme_unfocused_bg_color')[1]
    }

    for name, color in gtk_theme_colors.items():
      gtk_theme_colors[name] = self.rgba_to_hex(color)

    return gtk_theme_colors

  def theme_colors(self):
    gtk_colors = self.gtk_theme_colors()
    theme_colors = {
      'window': [
        gtk_colors['bg'],
        gtk_colors['unfocused_fg'],
        gtk_colors['unfocused_fg']
      ],
      'normal': [
        gtk_colors['bg'],
        gtk_colors['fg'],
        gtk_colors['bg'],
        gtk_colors['selected_bg'],
        gtk_colors['selected_fg']
      ],
      'urgent': [
        gtk_colors['bg'],
        gtk_colors['fg'],
        gtk_colors['bg'],
        gtk_colors['error_bg'],
        gtk_colors['error_fg']
      ]
    }

    for name, colors in theme_colors.items():
      theme_colors[name] = ', '.join(colors)

    return theme_colors

  def open_menu(self):
    settings = Gtk.Settings.get_default()
    font_name = settings.get_property('gtk-font-name')
    theme_colors = self.theme_colors()

    settings = [
      'rofi', '-dmenu', '-i', '-location', '2', '-width', '100',
      '-hide-scrollbar', '-lines', '6', '-color-enabled', '-bw', '0',
      '-p', self.prompt, '-font', font_name,
      '-color-window', theme_colors['window'],
      '-color-normal', theme_colors['normal'],
      '-color-urgent', theme_colors['urgent']
    ]

    menu = subprocess.Popen(settings, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    menu.stdin.write(self.menu_items)

    return menu

  def get_selection(self):
    selection = self.menu.communicate()[0].decode('utf8').rstrip()
    self.menu.stdin.close()

    return selection
