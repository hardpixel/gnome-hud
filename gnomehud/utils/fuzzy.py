from gnomehud.utils.menu import SEPARATOR


def normalize_string(string):
  string = string.replace('[^\w]', '')
  return string.lower()


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

    score = 0
    if self.label == query:
      return score

    score += 1
    if self.label.startswith(query):
      return score

    score += 1
    if query in self.label:
      return score

    score += 1
    if contains_words(self.label, words):
      return score

    score += 1
    if contains_words(self.label, words, False):
      return score

    score += 1
    if contains_words(self.vpath, words):
      return score

    score += 1
    if contains_words(self.vpath, words, False):
      return score

    return -1
