"""
PC-BASIC - mlparser.py
DRAW and PLAY macro language stream utilities

(c) 2013, 2014, 2015, 2016 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import string

from . import error
from . import values
from . import codestream


class MLParser(codestream.CodeStream):
    """Macro Language parser."""

    # whitespace character for both macro languages is only space
    blanks = ' '

    def __init__(self, gml, data_memory, values):
        """Initialise macro-language parser."""
        codestream.CodeStream.__init__(self, gml)
        self.memory = data_memory
        self.values = values

    def parse_number(self, default=None):
        """Parse a value in a macro-language string."""
        c = self.skip_blank()
        sgn = -1 if c == '-' else 1
        if c in ('+', '-'):
            self.read(1)
            c = self.peek()
            # don't allow default if sign is given
            default = None
        if c == '=':
            self.read(1)
            c = self.peek()
            if len(c) == 0:
                raise error.RunError(error.IFC)
            elif ord(c) > 8:
                name = self.read_name()
                error.throw_if(not name)
                indices = self._parse_indices()
                step = self.memory.get_variable(name, indices).to_int()
                self.require_read((';',), err=error.IFC)
            else:
                # varptr$
                step = self.memory.get_value_for_varptrstr(self.read(3)).to_int()
        elif c and c in string.digits:
            step = self._parse_const()
        elif default is not None:
            step = default
        else:
            raise error.RunError(error.IFC)
        if sgn == -1:
            step = -step
        return step

    def parse_string(self):
        """Parse a string value in a macro-language string."""
        c = self.skip_blank()
        if len(c) == 0:
            raise error.RunError(error.IFC)
        elif ord(c) > 8:
            name = self.read_name()
            error.throw_if(not name)
            indices = self._parse_indices()
            sub = self.memory.get_variable(name, indices)
            self.require_read((';',), err=error.IFC)
            return values.pass_string(sub, err=error.IFC).to_str()
        else:
            # varptr$
            ptr = self.memory.get_value_for_varptrstr(self.read(3))
            return values.pass_string(ptr).to_str()

    def _parse_const(self):
        """Parse and return a constant value in a macro-language string."""
        numstr = ''
        while self.skip_blank() in set(string.digits):
            numstr += self.read(1)
        try:
            return int(numstr)
        except ValueError:
            raise error.RunError(error.IFC)

    def _parse_indices(self):
        """Parse constant array indices."""
        indices = []
        if self.skip_blank_read_if(('[', '(')):
            while True:
                indices.append(self._parse_const())
                if not self.skip_blank_read_if((',',)):
                    break
            self.require_read((']', ')'))
        return indices