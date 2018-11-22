import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from menu import DbusMenu
from menu import SEPARATOR


def normalize_string(string):
  string = string.replace(SEPARATOR, ' ')
  string = string.replace('...', ' ')
  string = string.replace('\s+', ' ')
  string = string.strip()

  return string.lower()


def contains_words(text, words, require_all=True):
  for word in words:
    if word in text:
      if not require_all:
        return True
    elif require_all:
      return False

  return require_all


class Command(object):

  def __init__(self, index, value):
    self.index = index
    self.value = value
    self.parts = self.value.split(SEPARATOR)
    self.label = self.parts[-1]

  def score(self, comparable):
    value = normalize_string(self.value)
    query = normalize_string(comparable)
    words = query.split(' ')
    label = self.label.lower()

    score = 0
    if label == query:
      return score

    score = score + 1
    if label.startswith(query):
      return score

    score = score + 1
    if query in label:
      return score

    score = score + 1
    if contains_words(label, words):
      return score

    score = score + 1
    if contains_words(label, words, False):
      return score

    score = score + 1
    if contains_words(value, words):
      return score

    score = score + 1
    if contains_words(value, words, False):
      return score

    return -1

  def position(self, comparable):
    return self.score(comparable) if bool(comparable) else 0

  def visibility(self, comparable):
    return self.score(comparable) > -1 if bool(comparable) else True


class CommandListItem(Gtk.ListBoxRow):

  command = GObject.Property(type=object)

  def __init__(self, *args, **kwargs):
    super(Gtk.ListBoxRow, self).__init__(*args, **kwargs)

    self.label = Gtk.Label(margin=6, margin_left=10, margin_right=10)
    self.label.set_justify(Gtk.Justification.LEFT)
    self.label.set_halign(Gtk.Align.START)
    self.add(self.label)

    self.set_can_focus(False)
    self.show_all()

    self.connect('notify::command', self.on_command_changed)
    self.on_command_changed()

  def on_command_changed(self, *args):
    command = self.get_property('command')
    self.label.set_label(command.value)


class CommandList(Gtk.ListBox):

  def __init__(self, *args, **kwargs):
    super(Gtk.ListBox, self).__init__(*args, **kwargs)

    self.select_value = ''
    self.filter_value = ''
    self.visible_rows = []
    self.selected_row = 0
    self.selected_obj = None

    self.set_sort_func(self.sort_function)
    self.set_filter_func(self.filter_function)

    self.connect('row-selected', self.on_row_selected)

    self.dbus_menu = DbusMenu()
    self.append_row_items(self.dbus_menu.actions)

  def set_filter_value(self, value=None):
    self.visible_rows = []
    self.filter_value = value

    self.unselect_all()
    self.invalidate_filter()
    self.invalidate_sort()
    self.invalidate_selection()

  def invalidate_selection(self):
    adjust = self.get_adjustment()
    self.select_row_by_index(0)

    return adjust.set_value(0) if adjust else False

  def execute_command(self, callback):
    if self.select_value:
      self.dbus_menu.activate(self.select_value)
      callback()

  def sort_function(self, prev_item, next_item):
    prev_score = prev_item.command.position(self.select_value)
    next_score = next_item.command.position(self.select_value)

    score_diff = prev_score - next_score
    index_diff = prev_item.command.index - next_item.command.index

    return index_diff if score_diff == 0 else index_diff

  def filter_function(self, item):
    visible = item.command.visibility(self.filter_value)
    self.append_visible_row(item, visible)

    return visible

  def append_row_items(self, items):
    for index, value in enumerate(items):
      object = Command(value=value, index=index)
      objrow = CommandListItem(command=object)

      self.add(objrow)

  def append_visible_row(self, row, visibility):
    if visibility:
      self.visible_rows.append(row)

  def select_row_by_index(self, index):
    index_range = range(0, len(self.visible_rows))

    if index in index_range:
      self.selected_row = index
      self.selected_obj = self.visible_rows[index]

      self.selected_obj.activate()

  def select_previous_row(self):
    self.select_row_by_index(self.selected_row - 1)

  def select_next_row(self):
    self.select_row_by_index(self.selected_row + 1)

  def on_row_selected(self, listbox, item):
    self.select_value = item.command.value if item else ''


class ModalMenu(Gtk.Window):

  def __init__(self, *args, **kwargs):
    super(Gtk.Window, self).__init__(*args, **kwargs)

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
    self.search_entry.connect('activate', self.on_search_entry_activated)

    self.scrolled_window = Gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
    self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    self.scrolled_window.add(self.command_list)

    self.header_bar = Gtk.HeaderBar(spacing=0)
    self.header_bar.set_custom_title(self.search_entry)

    self.set_titlebar(self.header_bar)
    self.add(self.scrolled_window)

    self.set_dark_variation()
    self.add_events(Gdk.EventMask.KEY_PRESS_MASK)

    self.connect('show', self.on_window_shown)
    self.connect('destroy', self.on_window_destroyed)
    self.connect('key-press-event', self.on_window_key_pressed)

  def open(self):
    self.show_all()
    Gtk.main()

  def set_dark_variation(self):
    settings = Gtk.Settings.get_default()
    settings.set_property('gtk-application-prefer-dark-theme', True)

  def on_window_shown(self, window):
    self.search_entry.grab_focus()

  def on_window_destroyed(self, window):
    Gtk.main_quit()

  def on_window_key_pressed(self, window, event):
    if event.keyval == Gdk.KEY_Escape:
      return self.destroy()

    if event.keyval == Gdk.KEY_Tab or event.keyval == Gdk.KEY_ISO_Left_Tab:
      return True

    if event.keyval == Gdk.KEY_Up:
      return self.command_list.select_previous_row()

    if event.keyval == Gdk.KEY_Down:
      return self.command_list.select_next_row()

  def on_search_entry_changed(self, *args):
    search_value = self.search_entry.get_text()
    self.command_list.set_filter_value(search_value)

  def on_search_entry_activated(self, *args):
    self.command_list.execute_command(self.destroy)


if __name__ == '__main__':
  modal = ModalMenu()
  modal.open()
