import re
import dbus


def match_findall(pattern, text):
  regex = re.compile(pattern, re.IGNORECASE)
  return regex.findall(text)


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

  def get_focus_window_prop(self, prop):
    window = 'global.display.focus_window'
    result = self.eval_script('%s.%s()' % (window, prop))

    return result[1] if bool(result[0]) else None

  def get_utf8_prop(self, property):
    method = 'get%s' % property.lower()
    result = self.get_focus_window_prop(method)
    result = str(result or '').replace('"', '')

    return result if result != 'null' else None

  def get_xid(self):
    result = self.get_focus_window_prop('get_description')
    result = str(result or '').replace('"', '')
    result = match_findall('0x[0-9a-f]+', result)

    return int(result[0], 16) if result else None
