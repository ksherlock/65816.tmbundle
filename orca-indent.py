import sublime
import sublime_plugin

TABS = (9, 15, 40)
QUOTES = "\"'"

# opcodes w/o operands
NOPS = set((
	b'ANOP',

#	b'ASL',
	b'CLC',
	b'CLD',
	b'CLI',
	b'CLV',
#	b'DEC',
	b'DEX',
	b'DEY',
#	b'INC',
	b'INX',
	b'INY',
#	b'LSR',
	b'NOP',
	b'PHA',
	b'PHB',
	b'PHD',
	b'PHK',
	b'PHP',
	b'PHX',
	b'PHY',
	b'PLA',
	b'PLB',
	b'PLD',
	b'PLP',
	b'PLX',
	b'PLY',
#	b'ROL',
#	b'ROR',
	b'RTI',
	b'RTL',
	b'RTS',
	b'SEC',
	b'SED',
	b'SEI',
	b'STP',
	b'TAX',
	b'TAY',
	b'TCD',
	b'TCS',
	b'TDC',
	b'TSC',
	b'TSX',
	b'TXA',
	b'TXS',
	b'TXY',
	b'TYA',
	b'TYX',
	b'WAI',
	b'XBA',
	b'XCE',
))

def tab_to(line, ts):
	pos = TABS[ts-1]
	line.append(0x20)
	while len(line) < pos: line.append(0x20)


def indent(s):

	st = 0
	q = 0
	rv = bytearray()
	opc = bytearray()

	for c in s:
		if c == "\t": c = " "
		cc = ord(c)

		# if c == " ":
		# 	if st in (2,4,6): continue
		# 	if st in (1,3):
		# 		st += 1
		# 		continue

		if st == 0:
			if c == " ":
				st = 2
				continue

			if c in "!*;":
				# leave ; in the first column
				st = 7
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
			continue

		if st == 2:
			# label? ws
			if c == " ": continue
			if c in "*!" and not rv:
				st = 7
			elif c == ";":
				st = 7
				tab_to(rv, 3)
			else:
				st += 1
				tab_to(rv, 1)
				opc.append(cc & ~0x20)
			rv.append(cc)
			continue

		if st == 3:
			# opcode
			if c == " ":
				st += 1
				continue
			rv.append(cc)
			opc.append(cc & ~0x20)
			continue

		if st == 4:
			# opcode ws
			if c == " ": continue

			if c == ";":
				st = 7
				tab_to(rv, 3)
			elif bytes(opc) in NOPS:
				# jump to comment...
				st = 7
				tab_to(rv, 3)
				rv.append(0x3b) # ;
			else:
				st += 1
				tab_to(rv, 2)
				if c in QUOTES: q = cc
			rv.append(cc)
			continue

		if st == 5:
			# operand
			if q:
				rv.append(cc)
				if q == cc: q = 0
				continue
			if c == " ":
				st += 1
				continue
			rv.append(cc)
			if c in QUOTES: q = cc
			continue

		if st == 6:
			# operand ws
			if c == " ": continue
			st += 1
			tab_to(rv, 3)
			if c != ";": rv.append(0x3b) # ;
			rv.append(cc)
			continue

		if st == 7:
			# comment
			rv.append(cc)
			continue


	return rv.decode('ascii')



class OrcaIndent(sublime_plugin.TextCommand):

	def is_enabled(self):
		scope = self.view.scope_name(0)
		lang = scope.split(' ')[0]
		return lang == 'source.asm.65816.orcam'


	def run(self, edit):
		view = self.view
		all = sublime.Region(0, view.size())

		# disable space indentation.
		view.settings().set('translate_tabs_to_spaces', False)

		data = []
		for r in view.lines(all):
			text = view.substr(r).rstrip()

			data.append(indent(text))


		data.append('')
		text = '\n'.join(data)

		view.replace(edit, all, text)
