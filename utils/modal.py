import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

from menu import DbusMenu


class CommandList(Gtk.TreeView):

  def __init__(self):
    super(CommandList, self).__init__()

    self.selection_value    = None
    self.selection_treeiter = None

    self.set_can_focus(False)
    self.set_headers_visible(False)
    self.set_enable_search(True)
    self.set_search_column(0)
    self.set_search_value()

    self.list_store = Gtk.ListStore(str)
    self.set_model(self.list_store)
    self.set_search_equal_func(self.search_function)

    self.list_filter = self.list_store.filter_new()
    self.list_filter.set_visible_func(self.filter_function, data=None)

    self.dbus_menu = DbusMenu()
    self.append_items(self.dbus_menu.actions)

    self.render = Gtk.CellRendererText()
    self.column = Gtk.TreeViewColumn('Command', self.render, text=0)
    self.append_column(self.column)

    self.select = self.get_selection()
    self.select.connect('changed', self.on_tree_selection_changed)

  def search_function(self, model, column, key, treeiter):
    command = model[treeiter][column]
    return key.lower() not in command.lower()

  def filter_function(self, model, treeiter, user_data):
    command = model[treeiter][0]
    return self.search_value.lower() in command.lower()

  def append_items(self, items):
    for item in items:
      self.list_store.append([item])

  def select_iter(self, treeiter):
    if treeiter:
      self.select.select_iter(treeiter)

  def set_search_value(self, value=None):
    self.search_value = value or ''

  def select_first_item(self):
    treeiter = self.list_store.get_iter_first()
    self.select_iter(treeiter)

  def select_previous_item(self):
    treeiter = self.list_store.iter_previous(self.selection_treeiter)
    self.select_iter(treeiter)

  def select_next_item(self):
    treeiter = self.list_store.iter_next(self.selection_treeiter)
    self.select_iter(treeiter)

  def execute_command(self, callback):
    if self.selection_value:
      self.dbus_menu.activate(self.selection_value)
      callback()

  def on_tree_selection_changed(self, select):
    model, treeiter = select.get_selected()

    if treeiter is not None:
      self.selection_value    = model[treeiter][0]
      self.selection_treeiter = treeiter


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

    self.search_entry = Gtk.SearchEntry(hexpand=True, margin=2)
    self.search_entry.connect_after('changed', self.on_search_entry_changed)
    self.search_entry.connect('activate', self.on_search_entry_activated)

    self.command_list = CommandList()
    self.command_list.set_search_entry(self.search_entry)
    self.command_list.select_first_item()

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

    if event.keyval == Gdk.KEY_Up:
      self.command_list.select_previous_item()
      return True

    if event.keyval == Gdk.KEY_Down:
      self.command_list.select_next_item()
      return True

  def on_search_entry_changed(self, *args):
    search_value = self.search_entry.get_text()
    self.command_list.set_search_value(search_value)

    if not search_value:
      self.command_list.select_first_item()

  def on_search_entry_activated(self, *args):
    self.command_list.execute_command(self.destroy)
