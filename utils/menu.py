import gi
import dbus

gi.require_version('Bamf', '3')

from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import Bamf

SEPARATOR = u'\u0020\u0020\u00BB\u0020\u0020'


class DbusMenu:

  def __init__(self):
    self.session      = dbus.SessionBus()
    self.matcher      = Bamf.Matcher.get_default()
    self.window       = self.matcher.get_active_window()
    self.xid          = self.window.get_xid()
    self.bus_name     = self.window.get_utf8_prop('_GTK_UNIQUE_BUS_NAME')
    self.app_path     = self.window.get_utf8_prop('_GTK_APPLICATION_OBJECT_PATH')
    self.win_path     = self.window.get_utf8_prop('_GTK_WINDOW_OBJECT_PATH')
    self.menubar_path = self.window.get_utf8_prop('_GTK_MENUBAR_OBJECT_PATH')
    self.appmenu_path = self.window.get_utf8_prop('_GTK_APP_MENU_OBJECT_PATH')
    self.menu_items   = dict()
    self.menu_actions = dict()

    self.explore_dbusmenu()
    self.explore_gtkmenu()
    self.handle_empty()

  @property

  def prompt(self):
    application  = self.matcher.get_active_application()
    desktop_file = application.get_desktop_file()
    deskapp_info = Gio.DesktopAppInfo.new_from_filename(desktop_file)

    return deskapp_info.get_string('Name')

  @property

  def actions(self):
    return self.menu_actions.keys()

  def activate(self, selection):
    if selection:
      self.activate_item(selection)

  def activate_item(self, selection):
    if self.dbusmenu:
      self.activate_dbusmenu_item(selection)
    else:
      self.activate_gtkmenu_item(selection)

  def activate_dbusmenu_item(self, selection):
    action = self.menu_actions[selection]
    self.dbusmenu.Event(action, 'clicked', 0, 0)

  def activate_gtkmenu_item(self, selection):
    action = self.menu_actions.get(selection, 'sys.quit')

    if 'sys.' in action:
      self.close_window()

    elif 'app.' in action:
      self.activate_gtkmenu_action(action, 'app.', self.app_path)

    elif 'win.' in action:
      self.activate_gtkmenu_action(action, 'win.', self.win_path)

    elif 'unity.' in action:
      self.activate_gtkmenu_action(action, 'unity.', self.menubar_path)

  def activate_gtkmenu_action(self, action, prefix, path):
    object = self.session.get_object(self.bus_name, path)
    iface  = dbus.Interface(object, dbus_interface='org.gtk.Actions')

    iface.Activate(action.replace(prefix, ''), [], dict())

  def close_window(self):
    screen = Gdk.Screen.get_default()
    window = screen.get_active_window()

    window.destroy()

  def explore_dbusmenu(self):
    name = 'com.canonical.AppMenu.Registrar'
    path = '/com/canonical/AppMenu/Registrar'

    try:
      object     = self.session.get_object(name, path)
      interface  = dbus.Interface(object, name)
      name, path = interface.GetMenuForWindow(self.xid)
      pobject    = self.session.get_object(name, path)
      interface  = dbus.Interface(pobject, 'com.canonical.dbusmenu')
      results    = interface.GetLayout(0, -1, ['label'])

      self.explore_dbusmenu_items(results[1], [])
      self.dbusmenu = interface
    except dbus.exceptions.DBusException:
      self.dbusmenu = None

  def explore_dbusmenu_items(self, item=None, labels=None):
    item_id       = item[0]
    item_props    = item[1]
    item_children = item[2]

    if 'label' in item_props:
      new_labels = labels + [item_props['label']]
    else:
      new_labels = labels

    if len(item_children) == 0:
      if 'label' in item_props:
        form_label = self.format_labels(new_labels)
        self.menu_actions[form_label] = item_id
    else:
      for child in item_children:
        self.explore_dbusmenu_items(child, new_labels)

  def explore_gtkmenu(self):
    paths = [self.appmenu_path, self.menubar_path]

    for path in filter(None, paths):
      pobject   = self.session.get_object(self.bus_name, path)
      interface = dbus.Interface(pobject, dbus_interface='org.gtk.Menus')
      results   = interface.Start([x for x in range(1024)])

      for result in results:
        self.menu_items[(result[0], result[1])] = result[2]

    self.explore_gtkmenu_items()

  def explore_gtkmenu_items(self, menu_id=None, labels=None):
    menu_id = menu_id or (0, 0)
    labels  = labels or list()

    for menu in self.menu_items.get(menu_id, list()):
      if 'label' in menu:
        label      = menu['label']
        new_labels = labels + [label]
        form_label = self.format_labels(new_labels)

        if 'action' in menu:
          menu_action = menu['action']

          if ':section' not in menu and ':submenu' not in menu:
            self.menu_actions[form_label] = menu_action

      if ':section' in menu:
        self.explore_gtkmenu_subitems(menu[':section'], labels)

      if ':submenu' in menu:
        self.explore_gtkmenu_subitems(menu[':submenu'], new_labels)

  def explore_gtkmenu_subitems(self, items, labels):
    menu_id = (items[0], items[1])
    self.explore_gtkmenu_items(menu_id, labels)

  def format_labels(self, labels):
    head, *tail = labels
    result      = head

    for label in tail:
      result = result + SEPARATOR + label

    result = result.replace('Root%s' % SEPARATOR, '')
    result = result.replace('_', '')
    result = result.replace('...', ' ')
    result = result.replace('\s+', ' ')

    return result.strip()

  def handle_empty(self):
    if not len(self.menu_actions):
      self.menu_actions = { 'Quit': 'sys.quit' }

      alert = 'No menu items available! Showing only "Quit" entry.'
      print('gnomeHUD: WARNING: (%s) %s' % (self.prompt, alert))
