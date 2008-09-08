import unittest
import tempfile
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

from bdflib import model, reader

# This comes from the X11 BDF spec.
SAMPLE_FONT = """
STARTFONT 2.1
COMMENT This is a sample font in 2.1 format.
FONT -Adobe-Helvetica-Bold-R-Normal--24-240-75-75-P-65-ISO8859-1
SIZE 24 75 75
FONTBOUNDINGBOX 9 24 -2 -6
STARTPROPERTIES 19
FOUNDRY "Adobe"
FAMILY "Helvetica"
WEIGHT_NAME "Bold"
SLANT "R"
SETWIDTH_NAME "Normal"
ADD_STYLE_NAME ""
PIXEL_SIZE 24
POINT_SIZE 240
RESOLUTION_X 75
RESOLUTION_Y 75
SPACING "P"
AVERAGE_WIDTH 65
CHARSET_REGISTRY "ISO8859"
CHARSET_ENCODING "1"
MIN_SPACE 4
FONT_ASCENT 21
FONT_DESCENT 7
COPYRIGHT "Copyright (c) 1987 Adobe Systems, Inc."
NOTICE "Helvetica is a registered trademark of Linotype Inc."
ENDPROPERTIES
CHARS 2
STARTCHAR j
ENCODING 106
SWIDTH 355 0
DWIDTH 8 0
BBX 9 22 -2 -6
BITMAP
0380
0380
0380
0380
0000
0700
0700
0700
0700
0E00
0E00
0E00
0E00
0E00
1C00
1C00
1C00
1C00
3C00
7800
F000
E000
ENDCHAR
STARTCHAR quoteright
ENCODING 39
SWIDTH 223 0
DWIDTH 5 0
BBX 4 6 2 12
ATTRIBUTES 01C0
BITMAP
70
70
70
60
E0
C0
ENDCHAR
ENDFONT
""".strip()


class TestGlyph(unittest.TestCase):

	def test_basic_operation(self):
		testFont = model.Font("Adobe Helvetica", 24, 75, 75)
		testGlyphData = iter(SAMPLE_FONT.split('\n')[27:56])

		reader._read_glyph(testGlyphData, testFont)

		# The font should now have an entry for j.
		testGlyph = testFont[106]

		# The glyph should have the correct header data.
		self.failUnlessEqual(testGlyph.name, 'j')
		self.failUnlessEqual(testGlyph.codepoint, 106)
		self.failUnlessEqual(testGlyph.advance, 8)
		self.failUnlessEqual(testGlyph.bbX, -2)
		self.failUnlessEqual(testGlyph.bbY, -6)
		self.failUnlessEqual(testGlyph.bbW,  9)
		self.failUnlessEqual(testGlyph.bbH, 22)

		# Make sure we got the correct glyph bitmap.
		self.failUnlessEqual(str(testGlyph),
				'..|...###\n'
				'..|...###\n'
				'..|...###\n'
				'..|...###\n'
				'..|......\n'
				'..|..###.\n'
				'..|..###.\n'
				'..|..###.\n'
				'..|..###.\n'
				'..|.###..\n'
				'..|.###..\n'
				'..|.###..\n'
				'..|.###..\n'
				'..|.###..\n'
				'..|###...\n'
				'--+###---\n'
				'..|###...\n'
				'..|###...\n'
				'..####...\n'
				'.####....\n'
				'####.....\n'
				'###......'
			)

		# The iterator should have nothing left in it.
		self.failUnlessRaises(StopIteration, testGlyphData.next)


class TestReadProperty(unittest.TestCase):

	def test_basic_operation(self):
		testFont = model.Font("Adobe Helvetica", 24, 75, 75)
		testProperties = iter(SAMPLE_FONT.split('\n')[6:26])

		for i in range(19):
			reader._read_property(testProperties, testFont)

		# After reading the properties, the iterator should be just up to the
		# ENDPROPERTIES line.
		self.failUnlessEqual(testProperties.next(), "ENDPROPERTIES")

		# Test that the properties were read correctly.
		self.failUnlessEqual(testFont['FOUNDRY'], "Adobe")
		self.failUnlessEqual(testFont['FAMILY'], "Helvetica")
		self.failUnlessEqual(testFont['WEIGHT_NAME'], "Bold")
		self.failUnlessEqual(testFont['SLANT'], "R")
		self.failUnlessEqual(testFont['SETWIDTH_NAME'], "Normal")
		self.failUnlessEqual(testFont['ADD_STYLE_NAME'], "")
		self.failUnlessEqual(testFont['PIXEL_SIZE'], 24)
		self.failUnlessEqual(testFont['POINT_SIZE'], 240)
		self.failUnlessEqual(testFont['RESOLUTION_X'], 75)
		self.failUnlessEqual(testFont['RESOLUTION_Y'], 75)
		self.failUnlessEqual(testFont['SPACING'], "P")
		self.failUnlessEqual(testFont['AVERAGE_WIDTH'], 65)
		self.failUnlessEqual(testFont['CHARSET_REGISTRY'], "ISO8859")
		self.failUnlessEqual(testFont['CHARSET_ENCODING'], "1")
		self.failUnlessEqual(testFont['MIN_SPACE'], 4)
		self.failUnlessEqual(testFont['FONT_ASCENT'], 21)
		self.failUnlessEqual(testFont['FONT_DESCENT'], 7)
		self.failUnlessEqual(testFont['COPYRIGHT'],
				"Copyright (c) 1987 Adobe Systems, Inc.")
		self.failUnlessEqual(testFont['NOTICE'],
				"Helvetica is a registered trademark of Linotype Inc.")


class TestReadFont(unittest.TestCase):

	def _check_font(self, font):
		"""
		Checks that the given font is a representation of the sample font.
		"""
		self.failUnlessEqual(font["FACE_NAME"],
				"-Adobe-Helvetica-Bold-R-Normal--24-240-75-75-P-65-ISO8859-1")
		self.failUnlessEqual(font["POINT_SIZE"], 240)
		self.failUnlessEqual(font["RESOLUTION_X"], 75)
		self.failUnlessEqual(font["RESOLUTION_Y"], 75)
		self.failUnlessEqual(font.get_comments(), [
				"This is a sample font in 2.1 format."
			])
		self.failUnlessEqual(len(font.glyphs), 2)
		self.failUnlessEqual(len(font.properties), 20)

	def test_basic_operation(self):
		testFontData = iter(SAMPLE_FONT.split('\n'))
		testFont = reader._read_font(testFontData)

		self._check_font(testFont)

	def test_read_from_string(self):
		testFont = reader.read_from_string(SAMPLE_FONT)
		self._check_font(testFont)

	def test_read_from_iterable(self):
		testFont = reader.read_from_iterable(SAMPLE_FONT.split('\n'))
		self._check_font(testFont)

	def test_read_from_file(self):
		handle = tempfile.NamedTemporaryFile()
		handle.write(SAMPLE_FONT)
		handle.seek(0)
		testFont = reader.read_from_file(handle.name)
		self._check_font(testFont)
		handle.close()

