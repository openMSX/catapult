def parseTclValue(value):
	'''Parse a string as a Tcl expression and returns a list containing the
	words in the original string.
	No substitution is done, since this is not a Tcl interpreter, but otherwise
	Tcl parsing rules are followed.
	http://www.tcl.tk/man/tcl8.4/TclCmd/Tcl.htm
	'''
	chars = iter(list(value) + [ None ])
	ch = next(chars)
	words = []
	while True:
		while ch == ' ':
			ch = next(chars)
		if ch is None:
			return words
		quoteType, endChar, keepBackslash = {
			'"':      ( 'quote', '"', False ),
			'{':      ( 'brace', '}', True  ),
			}.get(ch, ( None,    ' ', False ) )
		if quoteType is not None:
			ch = next(chars)
		braceLevel = 0
		buf = []
		while True:
			if ch == endChar:
				if endChar == '}' and braceLevel > 0:
					braceLevel -= 1
				else:
					break
			elif ch == '{':
				braceLevel += 1
			elif ch == '\\':
				if keepBackslash:
					buf.append(ch)
				ch = next(chars)
				# Note: Tcl supports multi-line with backslash; we don't.
				if ch is None:
					raise ValueError('backslash at end of string')
			buf.append(ch)
			ch = next(chars)
			if ch is None:
				break
		words.append(u''.join(buf))
		if quoteType is not None:
			if ch is None:
				raise ValueError('unterminated open-%s' % quoteType)
			ch = next(chars)
			if ch not in (' ', None):
				raise ValueError(
					'extra characters after close-%s: %s'
					% (quoteType, ch)
					)

if __name__ == '__main__':
	# TODO: Make this into a unit test.
	for inp, out in (
		( '', [] ),
		( '""', [ '' ] ),
		( '{}', [ '' ] ),
		( 'abc', [ 'abc' ] ),
		( 'abc def', [ 'abc', 'def' ] ),
		( '"abc def"', [ 'abc def' ] ),
		( '{abc def}', [ 'abc def' ] ),
		( '"{abc def}"', [ '{abc def}' ] ),
		( '{"abc def"}', [ '"abc def"' ] ),
		( '"abc}{def"', [ 'abc}{def' ] ),
		( '{abc"def}', [ 'abc"def' ] ),
		( '"a b" {c d} "e f"',  [ 'a b', 'c d', 'e f' ] ),
		( '"a  b"  {c  d}  "e  f"',  [ 'a  b', 'c  d', 'e  f' ] ),
		( 'ab { } cd " " ef', [ 'ab', ' ', 'cd', ' ', 'ef' ] ),
		( 'abc"def', [ 'abc"def' ] ),
		( 'abc{def', [ 'abc{def' ] ),
		( r'\"abc\"', [ '"abc"' ] ),
		( r'\{abc\}', [ '{abc}' ] ),
		( r'"\{abc\"def\}"', [ '{abc"def}' ] ),
		( r'{ \{ }', [ r' \{ ' ] ),
		( r'\\', [ '\\' ] ),
		( r'abc\ def', [ 'abc def' ] ),
		( r'{abc\}def}', [ r'abc\}def' ] ),
		( r'{abc\{def}', [ r'abc\{def' ] ),
		( r'"abc\"def"', [ 'abc"def' ] ),
		( 'xyz {{a b c} {d e {f}} g {h}}',
		  [ 'xyz', '{a b c} {d e {f}} g {h}' ] ),
		):
		try:
			result = parseTclValue(inp)
		except ValueError as message:
			print('ERROR:', inp, ':', message)
		else:
			if result != out:
				print('ERROR:', inp, '->', result, '!=', out)

def tclEscape(string):
	'''Escape strings so that they don't trigger Tcl functionality.'''
	newString = string.replace('\\', '\\\\')
	newString = newString.replace('\n', '\\r').replace('$', '\$')
	newString = newString.replace('"', '\\"').replace('\'', '\\\'')
	newString = newString.replace('[', '\[').replace(']', '\]')
	return newString

# this class is used to mark a string as being already escaped
class EscapedStr(str):
	pass
