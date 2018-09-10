import sublime
import sublime_plugin
import os
import re
import sys
import time

class MerlinMacGen(sublime_plugin.TextCommand):

	opcodes = {
		'BRL', 'COP', 'JML', 'JMPL', 'JSL', 'MVN', 'MVP', 'MX', 'PEA',
		'PEI', 'PER', 'REP', 'SEP', 'WDM', 'XCE', 'ADR', 'ADRL', 'ASC',
		'AST', 'BRK', 'CHK', 'CYC', 'DA', 'DAT', 'DB', 'DCI', 'DDB', 'DEND',
		'DFB', 'DL', 'DS', 'DSK', 'DUM', 'DW', 'END', 'ENT', 'EQU', 'ERR', 'EXP',
		'EXT', 'FLS', 'HEX', 'INV', 'KBD', 'LST', 'LSTL', 'LUP', 'OBJ',
		'ORG', 'PAG', 'PAU', 'PMC', 'PUT', 'REL', 'REV', 'SAV', 'SKP',
		'STR', 'TR', 'TTL', 'TYP', 'USE', 'USR', 'VAR', 'XC', 'XREF','=',
		'>>>', 'DO', 'ELS', 'EOM', 'FIN', 'IF', 'MAC', '--^', '<<<',
		'CLC', 'CLD', 'CLI', 'CLV', 'DEX', 'DEY', 'INX', 'INY', 'NOP',
		'PHA', 'PHB', 'PHD', 'PHK', 'PHX', 'PHY', 'PLA', 'PLB', 'PLD',
		'PLP', 'PLX', 'PLY', 'RTI', 'RTL', 'RTS', 'SEC', 'SED', 'SEI',
		'STP', 'SWA', 'TAD', 'TAS', 'TAX', 'TAY', 'TCD', 'TCS', 'TDA',
		'TDC', 'TSA', 'TSC', 'TSX', 'TXA', 'TXS', 'TXY', 'TYA', 'TYX',
		'WAI', 'XBA', 'BCC', 'BCS', 'BEQ', 'BGE', 'BLT', 'BMI', 'BNE',
		'BPL', 'BRA', 'BVC', 'BVS', 'ADCL', 'ANDL', 'CMPL', 'EORL',
		'LDAL', 'ORAL', 'SBCL', 'STAL', 'ADC', 'AND', 'ASL', 'BIT',
		'CMP', 'CPX', 'CPY', 'DEC', 'EOR', 'INC', 'JMP', 'JSR', 'LDA',
		'LDX', 'LDY', 'LSR', 'ORA', 'ROL', 'ROR', 'SBC', 'STA', 'STX',
		'STY', 'STZ', 'TRB', 'TSB', 'PHP', 'STRL', 'FLO', 'EXD', 'CAS',
		''
	}
	re_pmc = re.compile('^[^.,/\\- ]*')
	re_dot_s = re.compile('\\.S$', re.IGNORECASE)
	re_ws = re.compile('[\t ]+')
	re_comment = re.compile('^[\t ]*[;*]')

	def front_matter(self):
		buffer = ""
		name = self.view.file_name()
		if name:
			buffer += "* Generated from " + os.path.basename(name) + " on " + time.asctime() + "\n"
		else:
			buffer += "* Generated on " + time.asctime() + "\n"
		buffer += "\n"
		return buffer

	def missing_matter(self, missing):
		buffer = ""
		if len(missing) == 0:
			return ""

		buffer = "* Missing Macros\n"

		missing = list(missing)
		missing.sort
		for macro in missing:
			buffer += "* " + macro + "\n"

		buffer += "\n"
		return buffer


	def run(self, edit):


		missing = set()
		known = set()

		view = self.view
		all = sublime.Region(0, view.size())
		for r in view.lines(all):
			text = view.substr(r).rstrip()

			if text == "" or self.re_comment.match(text):
				continue

			line = re.split(self.re_ws, text, maxsplit=2)
			if len(line) < 2:
				continue

			# _macro args
			# PMC _macro,args << .  /  ,  -  (  Space are separtors.
			# >>> _macro

			label = line[0].upper()
			opcode = line[1].upper()

			if opcode == "" or opcode[0] == ";":
				continue

			if opcode == 'MAC':
				# label MAC
				if label != "":
					known.add(label)
				continue

			if opcode in {'PMC', '>>>'} and len(line) > 2:
				tmp = line[2].upper()
				opcode = self.re_pmc.match(tmp).group(0)
				if opcode == "":
					continue


			if opcode in self.opcodes:
				continue
			if opcode in known:
				continue
			missing.add(opcode)


		if len(missing) == 0:
			return

		#
		buffer = ""
		root = "/tmp/supermacs"
		for e in os.listdir(root):

			if not self.re_dot_s.search(e):
				continue

			path = os.path.join(root, e)
			if not os.path.isfile(path):
				continue
			with open(path,'r') as file:
				# print(e + "\n",file=sys.stderr)
				buffer += self.one_macro_file(file, known, missing)

			if len(missing) == 0:
				break

		buffer = self.front_matter() + self.missing_matter(missing) + buffer


		view = view.window().new_file()
		view.insert(edit, 0, buffer)
		# p = 0
		# for m in missing:
		# 	p = p + view.insert(edit, p, str(m) + "\n")


	def one_macro_file(self, file, known, missing):
		inmac = False
		buffer = ""

		while True:
			text = file.readline()
			if not text:
				return buffer

			text = text.rstrip()

			if inmac:
				buffer += text + "\n"

			if text == "" or self.re_comment.match(text):
				continue

			line = re.split(self.re_ws, text, maxsplit=2)


			if len(line) < 2:
				continue

			# if line[0] == "_MMStartUp":
			# 	print(line, file=sys.stderr)

			label = line[0].upper()
			opcode = line[1].upper()



			if opcode == "" or opcode[0] == ";":
				continue

			if opcode == "MAC" and label != "":
				# print(label,file=sys.stderr)
				# print(label in missing, file=sys.stderr)

				if inmac:
					known.add(label)
					missing.discard(label)
				elif label in missing:
					inmac = True
					known.add(label)
					missing.discard(label)
					buffer += text + "\n"
				continue

			if opcode in { '<<<', 'EOM' }:
				inmac = False
				continue

			if not inmac:
				continue

			if opcode in {'PMC', '>>>'} and len(line) > 2:
				tmp = line[2].upper()
				opcode = self.re_pmc.match(tmp).group(0)
				if opcode == "":
					continue

			if opcode in self.opcodes:
				continue
			if opcode in known:
				continue
			missing.add(opcode)

