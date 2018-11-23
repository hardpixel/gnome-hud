import re
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

from gnomehud.utils.menu import DbusMenu
from gnomehud.utils.fuzzy import FuzzyMatch


def normalize_label(text):
  return text.replace('&', '&amp;')


def run_generator(function):
  priority  = GLib.PRIORITY_LOW
  generator = function()

  GLib.idle_add(lambda: next(generator, False), priority=priority)


def inject_custom_style(widget, style_string):
  provider = Gtk.CssProvider()
  provider.load_from_data(style_string.encode())

  screen   = Gdk.Screen.get_default()
  priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
  Gtk.StyleContext.add_provider_for_screen(screen, provider, priority)


def add_style_class(widget, class_string):
  context = widget.get_style_context()
  context.add_class('tiled')


class CommandListItem(Gtk.ListBoxRow):

  value = GObject.Property(type=str)
  index = GObject.Property(type=int)
  query = GObject.Property(type=str)

  def __init__(self, *args, **kwargs):
    super(Gtk.ListBoxRow, self).__init__(*args, **kwargs)

    self.visible = True

    self.set_can_focus(False)

    self.query = self.get_property('query')
    self.value = self.get_property('value')
    self.index = self.get_property('index')
    self.fuzzy = FuzzyMatch(text=self.value)

    self.label = Gtk.Label(margin=6, margin_left=10, margin_right=10)
    self.label.set_justify(Gtk.Justification.LEFT)
    self.label.set_halign(Gtk.Align.START)
    self.label.set_label(normalize_label(self.value))

    self.connect('notify::query', self.on_query_notify)

    self.add(self.label)
    self.show_all()

  def position(self, query):
    return self.fuzzy.score(query) if bool(query) else 0

  def visibility(self, query):
    self.visible = self.fuzzy.score(query) > -1 if bool(query) else True
    self.set_property('query', query)

    return self.visible

  def underline_matches(self):
    words = self.query.replace(' ', '|')
    regex = re.compile(words, re.IGNORECASE)
    value = regex.sub(self.format_matched_string, self.value)

    self.label.set_markup(normalize_label(value))

  def format_matched_string(self, match):
    return '<u>%s</u>' % match.group(0)

  def do_label_markup(self):
    if bool(self.query):
      self.underline_matches()

    elif '<u>' in self.label.get_label():
      self.label.set_label(normalize_label(self.value))

  def on_query_notify(self, *args):
    if self.visible:
      GLib.idle_add(self.do_label_markup)


class CommandList(Gtk.ListBox):

  menu_actions = GObject.Property(type=object)

  def __init__(self, *args, **kwargs):
    super(Gtk.ListBox, self).__init__(*args, **kwargs)

    self.menu_actions = self.get_property('menu-actions')
    self.select_value = ''
    self.filter_value = ''
    self.visible_rows = []
    self.selected_row = 0
    self.selected_obj = None

    self.set_sort_func(self.sort_function)
    self.set_filter_func(self.filter_function)

    self.connect('row-selected', self.on_row_selected)
    self.connect('notify::menu-actions', self.on_menu_actions_notify)

  def set_filter_value(self, value=None):
    self.visible_rows = []
    self.filter_value = value

    self.invalidate_filter()
    self.invalidate_sort()

    GLib.idle_add(self.invalidate_selection)

  def invalidate_selection(self):
    adjust = self.get_adjustment()

    self.reset_scroll_position(adjust)
    self.select_row_by_index(0)

  def reset_scroll_position(self, adjustment):
    if adjustment:
      adjustment.set_value(0)
      return True

  def append_visible_row(self, row, visibility):
    if visibility:
      self.visible_rows.append(row)
      return True

  def select_row_by_index(self, index):
    if index in range(0, len(self.visible_rows)):
      self.selected_row = index
      self.selected_obj = self.visible_rows[index]

      self.selected_obj.activate()

  def select_prev_row(self):
    self.select_row_by_index(self.selected_row - 1)

  def select_next_row(self):
    self.select_row_by_index(self.selected_row + 1)

  def sort_function(self, prev_item, next_item):
    prev_score = prev_item.position(self.filter_value)
    next_score = next_item.position(self.filter_value)

    score_diff = prev_score - next_score
    index_diff = prev_item.index - next_item.index

    return index_diff if score_diff == 0 else index_diff

  def filter_function(self, item):
    visible = item.visibility(self.filter_value)
    return self.append_visible_row(item, visible)

  def do_list_items(self):
    for index, value in enumerate(self.menu_actions):
      command = CommandListItem(value=value, index=index)
      self.add(command)
      yield True

    self.invalidate_selection()

  def on_row_selected(self, listbox, item):
    self.select_value = item.value if item else ''

  def on_menu_actions_notify(self, *args):
    self.foreach(lambda item: item.destroy())
    run_generator(self.do_list_items)


class CommandWindow(Gtk.ApplicationWindow):

  def __init__(self, *args, **kwargs):
    super(Gtk.ApplicationWindow, self).__init__(*args, **kwargs)

    self.set_modal(True)
    self.set_resizable(False)

    self.set_position(Gtk.WindowPosition.NONE)
    self.set_custom_position()

    self.set_default_size(800, 309)
    self.set_size_request(800, 309)

    self.set_skip_pager_hint(True)
    self.set_skip_taskbar_hint(True)
    self.set_destroy_with_parent(True)

    self.command_list = CommandList()
    self.command_list.invalidate_selection()

    self.search_entry = Gtk.SearchEntry(hexpand=True, margin=2)
    self.search_entry.connect('search-changed', self.on_search_entry_changed)
    self.search_entry.set_has_frame(False)

    self.scrolled_window = Gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
    self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    self.scrolled_window.add(self.command_list)

    self.header_bar = Gtk.HeaderBar(spacing=0)
    self.header_bar.set_custom_title(self.search_entry)

    self.set_titlebar(self.header_bar)
    self.add(self.scrolled_window)

    self.set_dark_variation()
    self.set_custom_styles()

    self.connect('show', self.on_window_show)

  def set_custom_position(self):
    width = self.get_screen().width()
    self.move((width - 800) / 2, 10)

  def set_dark_variation(self):
    settings = Gtk.Settings.get_default()
    settings.set_property('gtk-application-prefer-dark-theme', True)

  def set_custom_styles(self):
    styles = """entry.search.flat { border: 0; outline: 0;
      border-image: none; box-shadow: none; }
    """

    inject_custom_style(self, styles)
    add_style_class(self, 'tiled')

  def on_window_show(self, window):
    self.search_entry.grab_focus()

  def on_search_entry_changed(self, *args):
    search_value = self.search_entry.get_text()
    self.command_list.set_filter_value(search_value)


class HudMenu(Gtk.Application):

  def __init__(self, *args, **kwargs):
    kwargs['application_id'] = 'org.hardpixel.gnomeHUD'
    super(Gtk.Application, self).__init__(*args, **kwargs)

    self.dbus_menu = DbusMenu()

    self.set_accels_for_action('app.start', ['<Ctrl><Alt>space'])
    self.set_accels_for_action('app.quit', ['Escape'])
    self.set_accels_for_action('app.prev', ['Up'])
    self.set_accels_for_action('app.next', ['Down'])
    self.set_accels_for_action('app.execute', ['Return'])

  def add_simple_action(self, name, callback):
    action = Gio.SimpleAction.new(name, None)

    action.connect('activate', callback)
    self.add_action(action)

  def do_startup(self):
    Gtk.Application.do_startup(self)

    self.add_simple_action('start', self.on_show_window)
    self.add_simple_action('quit', self.on_hide_window)
    self.add_simple_action('prev', self.on_prev_command)
    self.add_simple_action('next', self.on_next_command)
    self.add_simple_action('execute', self.on_execute_command)

  def do_activate(self):
    self.screen = Gdk.Screen.get_default()
    self.active = self.screen.get_active_window()

    self.window = CommandWindow(application=self, title='gnomeHUD')
    self.window.connect('focus-out-event', self.on_hide_window)
    self.window.show_all()

    self.commands = self.window.command_list
    self.commands.set_property('menu-actions', self.dbus_menu.actions)
    self.commands.connect_after('button-press-event', self.on_commands_click)

    self.attached = self.window.get_window()
    self.attached.set_transient_for(self.active)
    self.attached.focus(Gdk.CURRENT_TIME)

  def on_show_window(self, *args):
    self.window.show()

  def on_hide_window(self, *args):
    self.window.destroy()
    self.quit()

  def on_prev_command(self, *args):
    self.commands.select_prev_row()

  def on_next_command(self, *args):
    self.commands.select_next_row()

  def on_commands_click(self, widget, event):
    if event.type == Gdk.EventType._2BUTTON_PRESS:
      self.on_execute_command()

  def on_execute_command(self, *args):
    self.on_hide_window()
    self.dbus_menu.activate(self.commands.select_value)
