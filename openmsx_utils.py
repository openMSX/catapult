# $Id$

def parseTclValue(value):
	'''Parse a string as a Tcl expression and returns a list containing the
	words in the original string.
	No substitution is done, since this is not a Tcl interpreter, but otherwise
	Tcl parsing rules are followed.
	http://www.tcl.tk/man/tcl8.4/TclCmd/Tcl.htm
	'''
	chars = iter(list(value) + [ None ])
	ch = chars.next()
	words = []
	while True:
		while ch == ' ':
			ch = chars.next()
		if ch is None:
			return words
		quoteType, endChar, keepBackslash = {
			'"':      ( 'quote', '"', False ),
			'{':      ( 'brace', '}', True  ),
			}.get(ch, ( None,    ' ', False ) )
		if quoteType is not None:
			ch = chars.next()
		buf = []
		while ch != endChar and ch is not None:
			if ch == '\\':
				if keepBackslash:
					buf.append(ch)
				ch = chars.next()
				# Note: Tcl supports multi-line with backslash; we don't.
				if ch is None:
					raise ValueError, 'backslash at end of string'
			buf.append(ch)
			ch = chars.next()
		words.append(u''.join(buf))
		if quoteType is not None:
			if ch is None:
				raise ValueError, 'unterminated open-%s' % quoteType
			ch = chars.next()
			if ch not in (' ', None):
				raise ValueError, \
					'extra characters after close-%s' % quoteType

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
		( r'"abc\"def"', [ 'abc"def' ] ),
		):
		try:
			result = parseTclValue(inp)
		except ValueError, message:
			print 'ERROR:', inp, ':', message
		else:
			if result != out:
				print 'ERROR:', inp, '->', result, '!=', out

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

	
