#! /usr/bin/python3

import os
import threading

def relative_path(filepath):
  root = os.path.dirname(os.path.realpath(__file__))
  return os.path.join(root, filepath)

def in_thread(**kwargs):
  thread = threading.Thread(**kwargs)
  thread.start()


if __name__ == "__main__":
  service = relative_path('utils/service.py')
  in_thread(target=os.system, args=[service])

  hud = relative_path('utils/hud.py')
  in_thread(target=os.system, args=[hud])
