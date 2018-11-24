import re

from fuzzysearch import find_near_matches
from gnomehud.utils.menu import SEPARATOR


def match_replace(pattern, replacement, text):
  regex = re.compile(pattern, re.IGNORECASE)
  return regex.sub(replacement, text)


def normalize_string(string):
  string = match_replace('[^\w]', ' ', string)
  string = match_replace('\s+', ' ', string)

  return string.lower().strip()


def contains_words(text, words, require_all=True):
  for word in words:
    if word in text:
      if not require_all:
        return True
    elif require_all:
      return False

  return require_all


class FuzzyMatch(object):

  def __init__(self, text):
    self.value = text
    self.parts = self.value.split(SEPARATOR)
    self.label = self.parts[-1]
    self.vpath = ' '.join(self.parts)

    self.label = normalize_string(self.label)
    self.vpath = normalize_string(self.vpath)

  def score(self, query):
    query = normalize_string(query)
    words = query.split(' ')

    if not contains_words(self.vpath, words):
      return -1

    fuzzy = find_near_matches(query, self.vpath, max_l_dist=1)
    score = sum(map(lambda m: m.dist, fuzzy))

    return score
