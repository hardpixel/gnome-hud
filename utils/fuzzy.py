from menu import SEPARATOR


def normalize_string(string):
  string = string.replace(SEPARATOR, ' ')
  string = string.replace('\s+', ' ')
  string = string.strip()

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

  def score(self, query):
    value = normalize_string(self.value)
    label = normalize_string(self.label)
    query = normalize_string(query)
    words = query.split(' ')

    score = 0
    if label == query:
      return score

    score += 1
    if label.startswith(query):
      return score

    score += 1
    if query in label:
      return score

    score += 1
    if contains_words(label, words):
      return score

    score += 1
    if contains_words(label, words, False):
      return score

    score += 1
    if contains_words(value, words):
      return score

    score += 1
    if contains_words(value, words, False):
      return score

    return -1
