import re

from gnomehud.utils.menu import SEPARATOR


def normalize_string(string):
  string = string.replace(SEPARATOR, ' ')
  string = string.replace('\s+', ' ')
  string = string.strip()

  return string.lower()


def matched_words(text, words):
  pattern = re.compile('|'.join(words), re.IGNORECASE)
  return pattern.findall(text)


def contains_matches(matches, words=None):
  return len(matches) == len(words) if words else len(matches)


class FuzzyMatch(object):

  def __init__(self, text):
    self.value = text
    self.parts = self.value.split(SEPARATOR)
    self.label = self.parts.pop(-1)
    self.vpath = ' '.join(self.parts)

    self.label = normalize_string(self.label)
    self.vpath = normalize_string(self.vpath)

  def score(self, query):
    query = normalize_string(query)
    words = query.split(' ')

    score = 0
    if self.label == query:
      return score

    score += 1
    if self.label.startswith(query):
      return score

    score += 1
    if query in self.label:
      return score

    matches = matched_words(self.label, words)

    score += 1
    if contains_matches(matches, words):
      return score

    score += 1
    if contains_matches(matches):
      return score

    matches = matched_words(self.vpath, words)

    score += 1
    if contains_matches(matches, words):
      return score

    score += 1
    if contains_matches(matches):
      return score

    return -1
