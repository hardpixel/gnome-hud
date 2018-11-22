import re
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

from menu import DbusMenu
from fuzzy import FuzzyMatch


class CommandListItem(Gtk.ListBoxRow):

  value = GObject.Property(type=str)
  index = GObject.Property(type=int)
  query = GObject.Property(type=str)

  def __init__(self, *args, **kwargs):
    super(Gtk.ListBoxRow, self).__init__(*args, **kwargs)

    self.set_can_focus(False)

    self.query = self.get_property('query')
    self.value = self.get_property('value')
    self.index = self.get_property('index')
    self.fuzzy = FuzzyMatch(text=self.value)

    self.label = Gtk.Label(margin=6, margin_left=10, margin_right=10)
    self.label.set_justify(Gtk.Justification.LEFT)
    self.label.set_halign(Gtk.Align.START)
    self.label.set_markup(self.value)

    self.connect('notify::query', self.on_query_notify)

    self.add(self.label)
    self.show_all()

  def position(self, query):
    return self.fuzzy.score(query) if bool(query) else 0

  def visibility(self, query):
    self.set_property('query', query)
    return self.fuzzy.score(query) > -1 if bool(query) else True

  def underline_matches(self):
    words = self.query.replace(' ', '|')
    regex = re.compile(words, re.IGNORECASE)
    value = regex.sub(self.format_matched_string, self.value)

    self.label.set_markup(value)

  def format_matched_string(self, match):
    return '<u>%s</u>' % match.group(0)

  def do_label_markup(self):
    if bool(self.query):
      self.underline_matches()

    elif '<u>' in self.label.get_label():
      self.label.set_markup(self.value)

  def on_query_notify(self, *args):
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

  def on_row_selected(self, listbox, item):
    self.select_value = item.value if item else ''

  def on_menu_actions_notify(self, *args):
    self.foreach(lambda item: item.destroy())

    for index, value in enumerate(self.menu_actions):
      command = CommandListItem(value=value, index=index)
      self.add(command)

    self.invalidate_selection()


class CommandWindow(Gtk.ApplicationWindow):

  def __init__(self, *args, **kwargs):
    super(Gtk.ApplicationWindow, self).__init__(*args, **kwargs)

    self.skip_taskbar_hint   = True
    self.destroy_with_parent = True
    self.modal               = True
    self.window_position     = Gtk.WindowPosition.CENTER_ON_PARENT
    self.type_hint           = Gdk.WindowTypeHint.DIALOG

    self.set_default_size(640, 250)
    self.set_size_request(640, 250)

    self.command_list = CommandList()
    self.command_list.invalidate_selection()

    self.search_entry = Gtk.SearchEntry(hexpand=True, margin=2)
    self.search_entry.connect('changed', self.on_search_entry_changed)

    self.scrolled_window = Gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
    self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    self.scrolled_window.add(self.command_list)

    self.header_bar = Gtk.HeaderBar(spacing=0)
    self.header_bar.set_custom_title(self.search_entry)

    self.set_titlebar(self.header_bar)
    self.add(self.scrolled_window)

    self.set_dark_variation()
    self.connect('show', self.on_window_show)

  def set_dark_variation(self):
    settings = Gtk.Settings.get_default()
    settings.set_property('gtk-application-prefer-dark-theme', True)

  def on_window_show(self, window):
    self.search_entry.grab_focus()

  def on_search_entry_changed(self, *args):
    search_value = self.search_entry.get_text()
    GLib.idle_add(self.command_list.set_filter_value, search_value)


class ModalMenu(Gtk.Application):

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
    self.window = CommandWindow(application=self, title='gnomeHUD')
    self.window.show_all()

    self.commands = self.window.command_list
    self.commands.set_property('menu-actions', self.dbus_menu.actions)

  def on_show_window(self, *args):
    self.window.show()

  def on_hide_window(self, *args):
    self.window.hide()
    self.quit()

  def on_prev_command(self, *args):
    self.commands.select_prev_row()

  def on_next_command(self, *args):
    self.commands.select_next_row()

  def on_execute_command(self, *args):
    self.dbus_menu.activate(self.commands.select_value)
    self.quit()


if __name__ == '__main__':
  modal = ModalMenu()
  modal.run()
