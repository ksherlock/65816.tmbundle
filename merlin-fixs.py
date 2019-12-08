import sublime
import sublime_plugin

SPACE = [" ", "\t"]
QUOTES = ["'", '"']


#
# need to do something clever for ; comments to put in comment field?
#
def fixs(s):

	f = 0
	q = None
	sp = False
	comment = False

	rv = ''
	if not len(s): return s
	if s[0] == "*": comment = True
	if s[0] == ";": comment = True ; rv = "\t\t\t"
	for c in s:

		if comment:
			if c == "\t": c = " "
			rv += c
			continue

		if q:
			rv += c
			if c == q: q = None
			continue

		if c in QUOTES:
			rv += c
			q = c
			sp = False
			continue

		if c in SPACE:
			if sp: continue
			f += 1
			c = "\t"
			sp = True
			rv += c
			continue

		if sp:
			if c == ';':
				comment = True
				rv += "\t" * (3-f)
			elif f == 3:
				comment = True
				rv += "; "
		sp = False
		rv += c

	return rv;


class MerlinFixs(sublime_plugin.TextCommand):

	def is_enabled(self):
		scope = self.view.scope_name(0)
		lang = scope.split(' ')[0]
		return lang == 'source.asm.65816.merlin' or lang == "source.linker.merlin"


	def run(self, edit):
		view = self.view
		all = sublime.Region(0, view.size())

		# disable space indentation.
		view.settings().set('translate_tabs_to_spaces', False)

		data = []
		for r in view.lines(all):
			text = view.substr(r).rstrip()

			data.append(fixs(text))


		data.append('')
		text = '\n'.join(data)

		view.replace(edit, all, text)