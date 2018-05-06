import gi
import dbus

gi.require_version('Bamf', '3')

from gi.repository import Gdk, Gio, Bamf

class DbusMenu:

  def __init__(self):
    self.session      = dbus.SessionBus()
    self.matcher      = Bamf.Matcher.get_default()
    self.window       = self.matcher.get_active_window()
    self.bus_name     = self.window.get_utf8_prop('_GTK_UNIQUE_BUS_NAME')
    self.app_path     = self.window.get_utf8_prop('_GTK_APPLICATION_OBJECT_PATH')
    self.win_path     = self.window.get_utf8_prop('_GTK_WINDOW_OBJECT_PATH')
    self.menubar_path = self.window.get_utf8_prop('_GTK_MENUBAR_OBJECT_PATH')
    self.appmenu_path = self.window.get_utf8_prop('_GTK_APP_MENU_OBJECT_PATH')
    self.menu_items   = dict()
    self.menu_actions = dict()

    self.explore_paths()
    self.explore_items()

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
    action = self.menu_actions.get(selection, 'sys.quit')

    if 'sys.' in action:
      screen = Gdk.Screen.get_default()
      window = screen.get_active_window()
      window.destroy()

    elif 'app.' in action:
      app_object = self.session.get_object(self.bus_name, self.app_path)
      app_iface  = dbus.Interface(app_object, dbus_interface='org.gtk.Actions')

      app_iface.Activate(action.replace('app.', ''), [], dict())

    elif 'win.' in action:
      win_object = self.session.get_object(self.bus_name, self.win_path)
      win_iface  = dbus.Interface(win_object, dbus_interface='org.gtk.Actions')

      win_iface.Activate(action.replace('win.', ''), [], dict())

    elif 'unity.' in action:
      mnb_object = self.session.get_object(self.bus_name, self.menubar_path)
      mnb_iface  = dbus.Interface(mnb_object, dbus_interface='org.gtk.Actions')

      mnb_iface.Activate(action.replace('unity.', ''), [], dict())

  def explore_paths(self):
    paths = [self.appmenu_path, self.menubar_path]

    for path in filter(None, paths):
      pobject   = self.session.get_object(self.bus_name, path)
      interface = dbus.Interface(pobject, dbus_interface='org.gtk.Menus')
      results   = interface.Start([x for x in range(1024)])

      for result in results:
        self.menu_items[(result[0], result[1])] = result[2]

  def explore_items(self, menu_id=None, labels=None):
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
        section    = menu[':section']
        section_id = (section[0], section[1])

        self.explore_items(section_id, labels)

      if ':submenu' in menu:
        submenu    = menu[':submenu']
        submenu_id = (submenu[0], submenu[1])

        self.explore_items(submenu_id, new_labels)

  def format_labels(self, labels):
    separator   = u'\u0020\u0020\u00BB\u0020\u0020'
    head, *tail = labels
    result      = head

    for label in tail:
      result = result + separator + label

    result = result.replace('Root >', '')
    result = result.replace('_', '')

    return result.strip()
