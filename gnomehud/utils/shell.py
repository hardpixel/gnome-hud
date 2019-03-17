import os
import re
import dbus


def is_wayland():
  disp = os.environ.get('WAYLAND_DISPLAY')
  type = os.environ.get('XDG_SESSION_TYPE')

  return 'wayland' in (disp or type)


def match_findall(pattern, text):
  regex = re.compile(pattern, re.IGNORECASE)
  return regex.findall(text)


def normalize_string(string):
  return str(string or '').replace('"', '')


class DbusShell(object):

  def __init__(self):
    self.session   = dbus.SessionBus()
    self.interface = self.get_interface()

  def get_interface(self):
    bus_name = 'org.gnome.Shell'
    bus_path = '/org/gnome/Shell'

    try:
      object    = self.session.get_object(bus_name, bus_path)
      interface = dbus.Interface(object, bus_name)

      return interface
    except dbus.exceptions.DBusException:
      return None

  def eval_script(self, script):
    return self.interface.Eval(script)

  def eval_object_function(self, object, prop):
    result = self.eval_script('%s.%s()' % (object, prop))
    return result[1] if bool(result[0]) else None

  def get_focus_window_prop(self, prop):
    window = 'global.display.focus_window'
    return self.eval_object_function(window, prop)

  def get_focus_app_prop(self, prop):
    app = 'Shell.WindowTracker.get_default().focus_app'
    return self.eval_object_function(app, prop)


class ShellWindow(object):

  def __init__(self):
    self.matcher = DbusShell()

  def get_utf8_prop(self, property):
    method = 'get%s' % property.lower()
    result = self.matcher.get_focus_window_prop(method)
    result = normalize_string(result)

    return result if result != 'null' else None

  def get_xid(self):
    result = self.matcher.get_focus_window_prop('get_id')
    return int(result) if result else None

  def get_appname(self):
    result = self.matcher.get_focus_app_prop('get_name')
    return normalize_string(result)
