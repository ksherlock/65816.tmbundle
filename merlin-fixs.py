import sublime
import sublime_plugin


TABS = (10, 15, 28)
STROPS = set((b'ASC', b'DCI', b'FLS', b'INV', b'REV' b'STR', b'STRL'))
XDIGITS = set("0123456789ABCDEFabcdef")
DQ = '"'
SQ = "'"
WS = " \t"
QUOTES = "\"'"

ST_COMMENT = 8

def tab_to(line, ts):
	pos = TABS[ts-1]
	line.append(0x20)
	while len(line) < pos: line.append(0x20)

def fixs(s):
	q = 0
	st = 0
	opc = bytearray()
	rv = bytearray()

	for c in s:
		if c == "\t": c = " "
		cc = ord(c)
		if st == 0:
			if c == " ":
				st = 2
				continue
			if c == "*":
				st = ST_COMMENT
			elif c == ";":
				st = ST_COMMENT
				tab_to(rv, 3)
			else:
				st += 1
			rv.append(cc)
			continue

		if st == 1:
			# label
			if c == " ":
				st += 1
				continue
			rv.append(cc)

		if st == 2:
			# label ws
			if c == " ": continue
			if c == "*" and len(rv) == 0:
				st = ST_COMMENT
			elif c == ";":
				st = ST_COMMENT
				tab_to(rv, 3)
			else:
				tab_to(rv, 1)
				st += 1
				opc.append(cc & ~0x20)
			rv.append(cc)
			continue

		if st == 3:
			# opcode
			if c == " ":
				st += 1;
				continue
			rv.append(cc)
			opc.append(cc & ~0x20)
			continue

		if st == 4:
			# opcode ws
			if c == " ": continue
			if c == ";":
				st = ST_COMMENT
				tab_to(rv, 3)
			else:
				st += 1
				b_opc = bytes(opc)
				if b_opc in STROPS and c not in XDIGITS: q = cc
				if c in QUOTES: q = cc
				if b_opc == b'IF': st += 1
				if b_opc == b'ASC' and c == '#': st += 1
				tab_to(rv, 2)
			rv.append(cc)
			continue

		if st == 5:
			# operand
			if q:
				rv.append(cc)
				if q == cc: q = 0
				continue
			if c == " ":
				st += 2
				continue
			rv.append(cc)
			if c in QUOTES: q = cc
			continue

		if st == 6:
			# operand w/o quoting
			if c == " ":
				st += 1
			else:
				rv.append(cc)

		if st == 7:
			# operand ws
			if c == " ": continue
			# insert ; ????
			st += 1
			tab_to(rv, 3)
			rv.append(cc)
			continue

		if st == 8:
			# comment
			rv.append(cc)
			continue


	#
	return rv.decode('ascii')



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