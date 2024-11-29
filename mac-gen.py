import sublime
import sublime_plugin
import os
import re
import sys
import time

def each_line(file):
	f = open(file, "r", encoding="ascii")
	try:
		while True:
			x = f.readline()
			if not x: break
			x = x.rstrip("\r\n")
			yield x
	except Exception as e:
		raise e
	finally:
		f.close()



def macro_files(dirs, filter):

	rv = []
	for root in dirs:
		try:
			tmp = [x for x in os.listdir(root) if filter(x)]
			tmp.sort(key=str.upper)
			tmp = [os.path.join(root, x) for x in tmp]
			tmp = [x for x in tmp if os.path.isfile(x)]

			rv += tmp

		except Exception as e:
			pass

	return rv



re_pmc = re.compile('^[^.,/\\- ]*')
re_dot_s = re.compile('\\.S$', re.IGNORECASE)
re_ws = re.compile('[\t ]+')
re_comment = re.compile('^[\t ]*[;*]')

class CommonMacGen(sublime_plugin.TextCommand):


	def run(self, edit):

		view = self.view

		missing = set()
		known = set()
		self.build_missing(known, missing)

		if len(missing) == 0: return

		buffer = ""
		files = self.build_file_list()

		for f in files:
			buffer += self.one_macro_file(f, known, missing)
			if len(missing) == 0: break;

		buffer = self.front_matter() + self.missing_matter(missing) + buffer

		self.create_macro_file(buffer)

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

	def create_macro_file(self, buffer):
		view = self.view
		mv = view.window().new_file()
		mv.settings().set("auto_indent", False)
		mv.run_command('insert', {'characters': buffer})


	# override these:
	def build_missing(self, known, missing):
		pass

	def build_file_list(self):
		return []

	def one_macro_file(self, file, known, missing):
		return ""


class MerlinMacGen(CommonMacGen):

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
		'ELSE', # processed as ELS
		''
	}


	def build_file_list(self):
		dirlist = self.view.settings().get('merlin_macro_directories', [])
		files = macro_files(dirlist, lambda x: x[-2:].upper() == ".S")
		return files

	def build_missing(self, known, missing):

		view = self.view
		all = sublime.Region(0, view.size())
		for r in view.lines(all):
			text = view.substr(r).rstrip()

			if text == "" or re_comment.match(text):
				continue

			tokens = re.split(re_ws, text, maxsplit=2)
			if len(tokens) < 2:
				continue

			# _macro args
			# PMC _macro,args << .  /  ,  -  (  Space are separators.
			# >>> _macro

			label = tokens[0].upper()
			opcode = tokens[1].upper()

			if opcode == "" or opcode[0] == ";":
				continue

			if opcode == 'MAC':
				# label MAC
				if label != "":
					known.add(label)
				continue

			if opcode in {'PMC', '>>>'} and len(tokens) > 2:
				tmp = tokens[2].upper()
				opcode = re_pmc.match(tmp).group(0)
				if opcode == "":
					continue


			if opcode in self.opcodes:
				continue
			if opcode in known:
				continue
			missing.add(opcode)

	def one_macro_file(self, file, known, missing):
		inmac = False
		buffer = ""

		for text in each_line(file):

			text = text.rstrip()

			if inmac:
				buffer += text + "\n"

			if text == "": continue
			if re_comment.match(text): continue

			tokens = re.split(re_ws, text, maxsplit=2)

			if len(tokens) < 2: continue

			label = tokens[0].upper()
			opcode = tokens[1].upper()


			if opcode == "" or opcode[0] == ";": continue

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

			if not inmac: continue

			if opcode in {'PMC', '>>>'} and len(tokens) > 2:
				tmp = tokens[2].upper()
				opcode = re_pmc.match(tmp).group(0)
				if opcode == "":
					continue

			if opcode in self.opcodes: continue
			if opcode in known: continue
			missing.add(opcode)

		return buffer


class OrcaMacGen(CommonMacGen):


	opcodes = {
		'ADC', 'AND', 'CMP', 'EOR', 'LDA', 'ORA', 'SBC', 'ASL', 'LSR',
		'ROR', 'ROL', 'BIT', 'CPX', 'CPY', 'DEC', 'INC', 'LDX', 'LDY',
		'STA', 'STX', 'STY', 'JMP', 'JSR', 'STZ', 'TRB', 'TSB', 'JSL',
		'JML', 'COP', 'MVN', 'MVP', 'PEA', 'PEI', 'REP', 'SEP', 'PER',
		'BRL', 'BRA', 'BEQ', 'BMI', 'BNE', 'BPL', 'BVC', 'BVS', 'BCC',
		'BCS', 'CLI', 'CLV', 'DEX', 'DEY', 'INX', 'INY', 'NOP', 'PHA',
		'PLA', 'PHP', 'PLP', 'RTI', 'RTS', 'SEC', 'SED', 'SEI', 'TAX',
		'TAY', 'TSX', 'TXA', 'TXS', 'TYA', 'BRK', 'CLC', 'CLD', 'PHX',
		'PHY', 'PLX', 'PLY', 'DEA', 'INA', 'PHB', 'PHD', 'PHK', 'PLB',
		'PLD', 'WDM', 'RTL', 'STP', 'TCD', 'TCS', 'TDC', 'TSC', 'TXY',
		'TYX', 'WAI', 'XBA', 'XCE', 'CPA', 'BLT', 'BGE', 'GBLA', 'GBLB',
		'GBLC', 'LCLA', 'LCLB', 'LCLC', 'SETA', 'SETB', 'SETC', 'AMID',
		'ASEARCH', 'AINPUT', 'AIF', 'AGO', 'ACTR', 'MNOTE', 'ANOP', 'DS',
		'ORG', 'OBJ', 'EQU', 'GEQU', 'MERR', 'DIRECT', 'KIND', 'SETCOM',
		'EJECT', 'ERR', 'GEN', 'MSB', 'LIST', 'SYMBOL', 'PRINTER',
		'65C02', '65816', 'LONGA', 'LONGI', 'DATACHK', 'CODECHK',
		'DYNCHK', 'IEEE', 'NUMSEX', 'CASE', 'OBJCASE', 'ABSADDR',
		'INSTIME', 'TRACE', 'EXPAND', 'DC', 'USING', 'ENTRY', 'OBJEND',
		'DATA', 'PRIVDATA', 'END', 'ALIGN', 'START', 'PRIVATE', 'MEM',
		'TITLE', 'RENAME', 'KEEP', 'COPY', 'APPEND', 'MCOPY', 'MDROP',
		'MLOAD', 'MACRO', 'MEXIT', 'MEND'
		}


	def build_file_list(self):
		dirlist = self.view.settings().get('orca_macro_directories', [])
		files = macro_files(dirlist, lambda x: x[:4].upper() == "M16.")
		return files

	def build_missing(self, known, missing):

		view = self.view
		all = sublime.Region(0, view.size())
		for r in view.lines(all):
			text = view.substr(r).rstrip()

			if text == "": continue
			if text[0] in "!*": continue
			if re_comment.match(text): continue
			tokens = re.split(re_ws, text, maxsplit=2)
			if len(tokens) < 2: continue

			label = tokens[0].upper()
			opcode = tokens[1].upper()

			if opcode in self.opcodes: continue
			missing.add(opcode)


	def one_macro_file(self, file, known, missing):
		buffer = ""
		state = 0

		for text in each_line(file):

			if state == 2:
				buffer += text + "\n"

			if text == "": continue
			if re_comment.match(text): continue


			tokens = re.split(re_ws, text, maxsplit=2)
			if len(tokens) < 2: continue

			label = tokens[0].upper()
			opcode = tokens[1].upper()

			if state == 0:
				if opcode == 'MACRO': state = 1
			elif state == 1:
				if opcode in missing:
					known.add(opcode)
					missing.discard(opcode)
					buffer += "\tMACRO\n"
					buffer += text + "\n"
					state = 2
				else:
					state = 0

			elif state == 2:
				if opcode == 'MEND': state = 0
				if opcode not in self.opcodes and opcode not in known:
					missing.add(opcode)


		return buffer


class MpwMacGen(CommonMacGen):


	opcodes = {
		'ACTR', 'ADC', 'AERROR', 'ALIGN', 'AND', 'ANOP', 'ASL',
		'BBC0', 'BBC1', 'BBC2', 'BBC3', 'BBC4', 'BBC5', 'BBC6', 'BBC7',
		'BBR0', 'BBR1', 'BBR2', 'BBR3', 'BBR4', 'BBR5', 'BBR6', 'BBR7',
		'BBS0', 'BBS1', 'BBS2', 'BBS3', 'BBS4', 'BBS5', 'BBS6', 'BBS7',
		'BCC', 'BCS', 'BEQ', 'BGE', 'BIT', 'BLANKS', 'BLT', 'BMI', 'BNE',
		'BPL', 'BRA', 'BRK', 'BRL', 'BVC', 'BVS', 'CASE',
		'CLB0', 'CLB1', 'CLB2', 'CLB3', 'CLB4', 'CLB5', 'CLB6', 'CLB7',
		'CLC', 'CLD', 'CLI', 'CLT', 'CLV', 'CMP', 'CODECHK', 'COM', 'COP', 'CPA',
		'CPX', 'CPY', 'CYCLE', 'DATACHK', 'DC', 'DCB', 'DS', 'DEA', 'DEC', 'DEX', 'DEY',
		'DIRECT', 'DUMP', 'EJECT', 'ELSE', 'ELSEIF', 'END', 'ENDF', 'ENDFUNC',
		'ENDI', 'ENDIF', 'ENDINIT', 'ENDM', 'ENDMACRO', 'ENDP', 'ENDPROC',
		'ENDR', 'ENDS', 'ENDSTACK', 'ENDW', 'ENDWHILE', 'ENDWITH', 'ENTRY',
		'EOR', 'EQU', 'EXITM', 'EXPORT', 'FUNC', 'GBLA', 'GBLC', 'GOTO',
	 	'IF', 'IMPORT', 'INA', 'INC', 'INCLUDE', 'INIT', 'INX', 'INY', 'JML', 'JMP',
		'JSL', 'JSR', 'LCLA', 'LCLC', 'LDA', 'LDM', 'LDX', 'LDY', 'LEAVE',
		'LOAD', 'LONGA', 'LONGI', 'LSR', 'MACHINE', 'MACRO', 'MEND', 'MEXIT',
		'MSB', 'MVN', 'MVP', 'NOP', 'ORA', 'ORG', 'PAGESIZE', 'PEA', 'PEI',
		'PER', 'PHA', 'PHB', 'PHD', 'PHK', 'PHP', 'PHX', 'PHY', 'PLA', 'PLB',
		'PLD', 'PLP', 'PLX', 'PLY', 'PRINT', 'PROC', 'RECORD', 'REP', 'RMB0',
		'RMB1', 'RMB2', 'RMB3', 'RMB4', 'RMB5', 'RMB6', 'RMB7', 'ROL', 'ROR',
		'RRF', 'RTI', 'RTL', 'RTS', 'SBC', 'SEB0', 'SEB1', 'SEB2', 'SEB3',
		'SEB4', 'SEB5', 'SEB6', 'SEB7', 'SEC', 'SED', 'SEG', 'SEGATTR', 'SEI',
		'SEP', 'SET', 'SETA', 'SETC', 'SETT', 'SMB0', 'SMB1', 'SMB2', 'SMB3',
		'SMB4', 'SMB5', 'SMB6', 'SMB7', 'SPACE', 'STA', 'STACKDP', 'STP',
		'STRING', 'STX', 'STY', 'STZ', 'SWA', 'TAD', 'TAS', 'TAX', 'TAY', 'TCD',
		'TCS', 'TDA', 'TDC', 'TITLE', 'TRB', 'TSA', 'TSB', 'TSC', 'TST', 'TSX',
		'TXA', 'TXS', 'TXY', 'TYA', 'TYX', 'WAI', 'WHILE', 'WITH', 'WRITE',
		'WRITELN', 'XBA', 'XCE'
		}


	def build_file_list(self):
		dirlist = self.view.settings().get('mpw_macro_directories', [])
		files = macro_files(dirlist, lambda x: x[:4].upper() == "M16.")
		return files

	def build_missing(self, known, missing):

		state = 0
		view = self.view
		all = sublime.Region(0, view.size())
		for r in view.lines(all):
			text = view.substr(r).rstrip()

			if text == "": continue
			if re_comment.match(text): continue
			tokens = re.split(re_ws, text, maxsplit=2)
			if len(tokens) < 2: continue

			label = tokens[0].upper()
			opcode = tokens[1].upper()
			ix = opcode.find('.')
			if ix >= 0: opcode = opcode[:ix]

			if opcode == "MACRO":
				state = 1
				continue
			if opcode == "MEND":
				state = 0
				continue
			if state == 1:
				known.add(opcode)
				missing.discard(opcode)
				state = 0
				continue

			if opcode in self.opcodes: continue
			if opcode in known: continue
			missing.add(opcode)


	def one_macro_file(self, file, known, missing):
		buffer = ""
		state = 0

		for text in each_line(file):

			if state == 2:
				buffer += text + "\n"

			if text == "": continue
			if re_comment.match(text): continue


			tokens = re.split(re_ws, text, maxsplit=2)
			if len(tokens) < 2: continue

			label = tokens[0].upper()
			opcode = tokens[1].upper()


			if state == 0:
				if opcode == 'MACRO': state = 1
			elif state == 1:
				if opcode in missing:
					known.add(opcode)
					missing.discard(opcode)
					buffer += "\tMACRO\n"
					buffer += text + "\n"
					state = 2
				else:
					state = 0

			elif state == 2:
				if opcode == 'MEND': state = 0
				if opcode not in self.opcodes and opcode not in known:
					missing.add(opcode)


		return buffer
