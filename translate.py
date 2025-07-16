import os
import re
from translations import *

lang = 'en'

def set_lang(_lang):
	global lang
	lang = _lang

def autodetect_lang():
	lang = 'en'
	try:
		if 'LANG' in os.environ:
			lang0 = (os.environ['LANG'])[0:2]
			if lang0 in translations:
				lang = lang0
	except:
		pass
	set_lang(lang)

# translate key like "default-goal" or embedded keys like "{reach-finish} {in-word} 5 {seconds-word}"
def _(str_key, disable_bidi=False):
	if str_key == '' or str_key is None:
		return ''

	def is_rtl(word):
		for ch in word:
			b = bidirectional(ch)
			if b in ('R', 'AL'):
				return True
			if b in ('L', 'EN', 'AN'):
				return False
		return False  # default to LTR if no strong character

	def bidi(str):
		"""BiDi simulation using word-level RTL detection, preserving original whitespace separators."""
		nonlocal disable_bidi
		if disable_bidi or not str or lang != 'he' or not any(bidirectional(ch) in ('R', 'AL') for ch in str):
			return str

		parts = re.findall(r'\S+|\s+', str)
		tokens = []

		for part in parts:
			if part.isspace():
				tokens.append((part, False))  # separator
			else:
				tokens.append((part, is_rtl(part)))

		if is_rtl(str):
			tokens = reversed(tokens)

		return ''.join(
			word[::-1] if is_rtl else word
			for word, is_rtl in tokens
		)

	# replace all {sub-key} occurrences (flat, no nesting)
	str_key = re.sub(r'{([^{}]+)}', lambda m: _(m.group(1), True), str_key)

	str = translations[lang].get(str_key) or translations['en'].get(str_key) or str_key

	return bidi(str)

autodetect_lang()
