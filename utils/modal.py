import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gio', '2.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GObject

from menu import DbusMenu
from fuzzywuzzy import fuzz


class CommandItem(GObject.GObject):

  text  = GObject.Property(type=str)
  index = GObject.Property(type=int)

  def __init__(self, *args, **kwargs):
    super(CommandItem, self).__init__()

  def ratio(self, comparable, reverse=False):
    ratio = fuzz.ratio(self.text.lower(), comparable.lower())
    return (ratio - 100) if reverse else ratio

  def position(self, comparable):
    return self.ratio(comparable, True) if bool(comparable) else self.index

  def visibility(self, comparable):
    return self.string_matches(comparable) if bool(comparable) else True

  def string_matches(self, comparable):
    ratio = self.ratio(comparable)
    match = comparable.lower() in self.text.lower()

    return match or ratio > 30


class CommandRow(Gtk.ListBoxRow):

  command = GObject.Property(type=object)

  def __init__(self, *args, **kwargs):
    super(CommandRow, self).__init__()

    self.label = Gtk.Label(margin=6, margin_left=10, margin_right=10)
    self.label.set_justify(Gtk.Justification.LEFT)
    self.label.set_halign(Gtk.Align.START)

    self.add(self.label)
    self.set_can_focus(False)
    self.show_all()

    self.connect('notify::command', self.on_command_changed)

  def on_command_changed(self, list_row, param):
    command = self.get_property('command')
    self.label.set_label(command.text)


class CommandList(Gtk.ListBox):

  def __init__(self):
    super(CommandList, self).__init__()

    self.selection_value  = ''
    self.selection_filter = ''

    self.set_filter_func(self.filter_function)
    self.add_events(Gdk.EventMask.KEY_PRESS_MASK)

    self.list_store = Gio.ListStore()
    self.bind_model(self.list_store, self.create_function)
    self.connect('row-selected', self.on_selection_selected)

    # self.list_store.set_sort_func(self.sort_function)

    self.dbus_menu = DbusMenu()
    self.append_row_items(self.dbus_menu.actions)

  @property

  def selected_row_index(self):
    selected = self.get_selected_row()
    return selected.get_index() if selected else 0

  def set_filter_value(self, value=None):
    self.selection_filter = value or ''

    self.invalidate_sort()
    self.invalidate_filter()
    self.select_first_item()

  def execute_command(self, callback):
    if self.selection_value:
      self.dbus_menu.activate(self.selection_value)
      callback()

  def create_function(self, object):
    item = CommandRow()
    item.set_property('command', object)

    return item

  def sort_function(self, prev_item, next_item):
    prev_value = prev_item.position(self.selection_value)
    next_value = next_item.position(self.selection_value)

    return prev_value > next_value

  def filter_function(self, item):
    return item.command.visibility(self.selection_filter)

  def append_row_items(self, items):
    for index, item in enumerate(items):
      object = CommandItem()
      object.set_property('text', item)
      object.set_property('index', index)

      self.list_store.insert_sorted(object, self.sort_function)

  def select_row_index(self, index):
    children = self.get_children()
    maxindex = len(children)

    if index > -1 and index < maxindex:
      self.select_row(children[index])

  def select_first_item(self):
    self.select_row_index(0)

  def select_previous_item(self):
    self.select_row_index(self.selected_row_index - 1)

  def select_next_item(self):
    self.select_row_index(self.selected_row_index + 1)

  def on_selection_selected(self, listbox, listbox_row):
    if listbox_row:
      self.selection_value = listbox_row.command.text


class ModalMenu(Gtk.Window):

  def __init__(self):
    super(ModalMenu, self).__init__()

    self.skip_taskbar_hint   = True
    self.destroy_with_parent = True
    self.modal               = True
    self.window_position     = Gtk.WindowPosition.CENTER_ON_PARENT
    self.type_hint           = Gdk.WindowTypeHint.DIALOG

    self.set_default_size(640, 250)
    self.set_size_request(640, 250)

    self.command_list = CommandList()
    self.command_list.select_first_item()

    self.search_entry = Gtk.SearchEntry(hexpand=True, margin=2)
    self.search_entry.connect_after('changed', self.on_search_entry_changed)
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
      self.destroy()
      return True

    if event.keyval == Gdk.KEY_Tab or event.keyval == Gdk.KEY_ISO_Left_Tab:
      return True

    if event.keyval == Gdk.KEY_Up or event.keyval == Gdk.KEY_Down:
      return self.command_list.event(event)

  def on_search_entry_changed(self, *args):
    search_value = self.search_entry.get_text()
    self.command_list.set_filter_value(search_value)

  def on_search_entry_activated(self, *args):
    self.command_list.execute_command(self.destroy)


if __name__ == '__main__':
  modal = ModalMenu()
  modal.open()
