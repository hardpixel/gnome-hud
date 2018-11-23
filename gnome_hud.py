#! /usr/bin/python3

import os
import threading


def relative_path(filepath):
  root = os.path.dirname(os.path.realpath(__file__))
  return os.path.join(root, filepath)


def in_thread(**kwargs):
  thread = threading.Thread(**kwargs)
  thread.start()


def run_script(path):
  path = relative_path(path)
  in_thread(target=os.system, args=['python3 %s' % path])


if __name__ == "__main__":
  run_script('appmenu.py')
  run_script('keybinder.py')
