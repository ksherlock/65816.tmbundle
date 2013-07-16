import sublime, sublime_plugin

class MerlinToTextCommand(sublime_plugin.TextCommand):
	def is_enabled(self):
		scope = self.view.scope_name(0)
		lang = scope.split(' ')[0]
		return lang == 'source.asm.65816.merlin'

	def run(self, edit):
		view = self.view
		all = sublime.Region(0, view.size())
		text = view.substr(all)

		#
		# good idea but the string is treated as utf8 and this blows.
		#

		# create the translation table, stripping high-bytes.
		table = map(lambda x: chr(x & 0x7f), xrange(256))
		#
		# high ' ' is actually a tab.
		table[ord(' ') | 0x80] = '\t'

		# line conversion
		table[ord('\r')] = '\n'
		table[ord('\r') | 0x80] = '\n'
		#
		# convert to a string.
		#table = ''.join(table);
		#
		#text = text.translate(table)

		data = map(lambda x: table[ord(text[x])], xrange(len(text)))

		text = ''.join(data)

		view.replace(edit, all, text)