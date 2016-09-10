"""
PC-BASIC - values.py
Types, values and conversions

(c) 2013, 2014, 2015, 2016 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import math
import string
import struct
import functools

from .. import error
from .. import tokens as tk
from . import numbers
from . import strings


# BASIC type sigils:
# Integer (%) - stored as two's complement, little-endian
# Single (!) - stored as 4-byte Microsoft Binary Format
# Double (#) - stored as 8-byte Microsoft Binary Format
# String ($) - stored as 1-byte length plus 2-byte pointer to string space
INT = '%'
SNG = '!'
DBL = '#'
STR = '$'

# storage size in bytes
TYPE_TO_SIZE = {STR: 3, INT: 2, SNG: 4, DBL: 8}
SIZE_TO_TYPE = {2: INT, 3: STR, 4: SNG, 8: DBL}

SIZE_TO_CLASS = {2: numbers.Integer, 3: strings.String, 4: numbers.Single, 8: numbers.Double}
TYPE_TO_CLASS = {INT: numbers.Integer, STR: strings.String, SNG: numbers.Single, DBL: numbers.Double}

def size_bytes(name):
    """Return the size of a value type, by variable name or type char."""
    return TYPE_TO_SIZE[name[-1]]

###############################################################################
# type checks

def check_value(inp):
    """Check if value is of Value type."""
    if not isinstance(inp, numbers.Value):
        raise TypeError('%s is not of class Value' % type(inp))

def pass_string(inp, err=error.TYPE_MISMATCH):
    """Check if variable is String-valued."""
    if not isinstance(inp, strings.String):
        check_value(inp)
        raise error.RunError(err)
    return inp

def pass_number(inp, err=error.TYPE_MISMATCH):
    """Check if variable is numeric."""
    if not isinstance(inp, numbers.Number):
        check_value(inp)
        raise error.RunError(err)
    return inp


###############################################################################
# type conversions

def match_types(left, right):
    """Check if variables are numeric and convert to highest-precision."""
    if isinstance(left, numbers.Double) or isinstance(right, numbers.Double):
        return left.to_double(), right.to_double()
    elif isinstance(left, numbers.Single) or isinstance(right, numbers.Single):
        return left.to_single(), right.to_single()
    elif isinstance(left, numbers.Integer) or isinstance(right, numbers.Integer):
        return left.to_integer(), right.to_integer()
    elif isinstance(left, strings.String) or isinstance(right, strings.String):
        return pass_string(left), pass_string(right)
    raise TypeError('%s or %s is not of class Value.' % (type(left), type(right)))


###############################################################################
# error handling

def float_safe(fn):
    """Decorator to handle floating point errors."""
    def wrapped_fn(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ValueError, ArithmeticError) as e:
            return args[0].error_handler.handle(e)
    return wrapped_fn

def _call_float_function(fn, *args):
    """Convert to IEEE 754, apply function, convert back."""
    args = list(args)
    floatcls = args[0].__class__
    values = args[0]._values
    feh = args[0].error_handler
    try:
        # to_float can overflow on Double.pos_max
        args = (arg.to_float(arg._values.double_math).to_value() for arg in args)
        return floatcls(None, values).from_value(fn(*args))
    except (ValueError, ArithmeticError) as e:
        # positive infinity of the appropriate class
        return feh.handle(e.__class__(floatcls(None, values).from_bytes(floatcls.pos_max)))


class FloatErrorHandler(object):
    """Handles floating point errors."""

    # types of errors that do not always interrupt execution
    soft_types = (error.OVERFLOW, error.DIVISION_BY_ZERO)

    def __init__(self, screen):
        """Setup handler."""
        self._screen = screen
        self._do_raise = False

    def suspend(self, do_raise):
        """Pause local handling of floating point errors."""
        self._do_raise = do_raise

    def handle(self, e):
        """Handle Overflow or Division by Zero."""
        if isinstance(e, ValueError):
            # math domain errors such as SQR(-1)
            math_error = error.IFC
        elif isinstance(e, OverflowError):
            math_error = error.OVERFLOW
        elif isinstance(e, ZeroDivisionError):
            math_error = error.DIVISION_BY_ZERO
        else:
            raise e
        if (self._do_raise or self._screen is None or
                math_error not in self.soft_types):
            # also raises exception in error_handle_mode!
            # in that case, prints a normal error message
            raise error.RunError(math_error)
        else:
            # write a message & continue as normal
            self._screen.write_line(error.RunError(math_error).message)
        # return max value for the appropriate float type
        if e.args and e.args[0]:
            if isinstance(e.args[0], numbers.Float):
                return e.args[0]
            elif isinstance(e.args[0], numbers.Integer):
                # integer values are not soft-handled
                raise error.RunError(math_error)
        return numbers.Single(None, self).from_bytes(numbers.Single.pos_max)


###############################################################################

class Values(object):
    """Handles BASIC strings and numbers."""

    def __init__(self, screen, string_space, double_math):
        """Setup values."""
        self.error_handler = FloatErrorHandler(screen)
        self.stringspace = string_space
        # double-precision EXP, SIN, COS, TAN, ATN, LOG
        self.double_math = double_math

    def create(self, buf):
        """Create new variable object with buffer provided."""
        # this sets a view, not a copy
        return SIZE_TO_CLASS[len(buf)](buf, self)

    def new(self, sigil):
        """Return newly allocated value of the given type with zeroed buffer."""
        return TYPE_TO_CLASS[sigil](None, self)

    def new_string(self):
        """Return newly allocated null string."""
        return strings.String(None, self)

    def new_integer(self):
        """Return newly allocated zero integer."""
        return numbers.Integer(None, self)

    def new_single(self):
        """Return newly allocated zero single."""
        return numbers.Single(None, self)

    def new_double(self):
        """Return newly allocated zero double."""
        return numbers.Double(None, self)

    ###########################################################################
    # convert between BASIC and Python values

    @float_safe
    def from_value(self, python_val, typechar):
        """Convert Python value to BASIC value."""
        return TYPE_TO_CLASS[typechar](None, self).from_value(python_val)

    def from_str_at(self, python_str, address):
        """Convert str to String at given address."""
        return strings.String(None, self).from_pointer(
            *self.stringspace.store(python_str, address))

    def from_bool(self, boo):
        """Convert Python boolean to Integer."""
        if boo:
            return numbers.Integer(None, self).from_bytes('\xff\xff')
        return numbers.Integer(None, self)

    ###########################################################################
    # convert to and from internal representation

    def from_bytes(self, token_bytes):
        """Convert internal byte representation to BASIC value."""
        # make a copy, not a view
        return SIZE_TO_CLASS[len(token_bytes)](None, self).from_bytes(token_bytes)

    def from_token(self, token):
        """Convert number token to new Number temporary"""
        if not token:
            raise ValueError('Token must not be empty')
        lead = bytes(token)[0]
        if lead == tk.T_SINGLE:
            return numbers.Single(None, self).from_token(token)
        elif lead == tk.T_DOUBLE:
            return numbers.Double(None, self).from_token(token)
        elif lead in tk.NUMBER:
            return numbers.Integer(None, self).from_token(token)
        raise ValueError('%s is not a number token' % repr(token))

    ###########################################################################
    # create value from string representations

    @float_safe
    def from_repr(self, word, allow_nonnum, typechar=None):
        """Convert representation to value."""
        # keep as string if typechar asks for it, ignore typechar otherwise
        if typechar == STR:
            return self.new_string().from_str(word)
        # skip spaces and line feeds (but not NUL).
        word = word.lstrip(' \n').upper()
        if not word:
            return self.new_integer()
        if word[:2] == '&H':
            return self.new_integer().from_hex(word[2:])
        elif word[:1] == '&':
            return self.new_integer().from_oct(word[2:] if word[1:2] == 'O' else word[1:])
        # we need to try to convert to int first,
        # mainly so that the tokeniser can output the right token type
        try:
            return self.new_integer().from_str(word)
        except ValueError as e:
            # non-integer characters, try a float
            pass
        except error.RunError as e:
            if e.err != error.OVERFLOW:
                raise
        # if allow_nonnum == False, raises ValueError for non-numerical characters
        is_double, mantissa, exp10 = numbers.str_to_decimal(word, allow_nonnum)
        if is_double:
            return self.new_double().from_decimal(mantissa, exp10)
        return self.new_single().from_decimal(mantissa, exp10)


@float_safe
def round(x):
    """Round to nearest whole number without converting to int."""
    return x.to_float().iround()


###############################################################################
# conversions

def cint_(inp, unsigned=False):
    """Check if variable is numeric, convert to Int."""
    if isinstance(inp, strings.String):
        raise error.RunError(error.TYPE_MISMATCH)
    return inp.to_integer(unsigned)

@float_safe
def csng_(num):
    """Check if variable is numeric, convert to Single."""
    if isinstance(num, strings.String):
        raise error.RunError(error.TYPE_MISMATCH)
    return num.to_single()

@float_safe
def cdbl_(num):
    """Check if variable is numeric, convert to Double."""
    if isinstance(num, strings.String):
        raise error.RunError(error.TYPE_MISMATCH)
    return num.to_double()

def to_type(typechar, value):
    """Check if variable can be converted to the given type and convert if necessary."""
    if typechar == STR:
        return pass_string(value)
    elif typechar == INT:
        return cint_(value)
    elif typechar == SNG:
        return csng_(value)
    elif typechar == DBL:
        return cdbl_(value)
    raise ValueError('%s is not a valid sigil.' % typechar)

# NOTE that this function will overflow if outside the range of Integer
# whereas Float.to_int will not
def to_int(inp, unsigned=False):
    """Round numeric variable and convert to Python integer."""
    return cint_(inp, unsigned).to_int(unsigned)

def mki_(x):
    """MKI$: return the byte representation of an int."""
    return x._values.new_string().from_str(cint_(x).to_bytes())

def mks_(x):
    """MKS$: return the byte representation of a single."""
    return x._values.new_string().from_str(csng_(x).to_bytes())

def mkd_(x):
    """MKD$: return the byte representation of a double."""
    return x._values.new_string().from_str(cdbl_(x).to_bytes())

def cvi_(x):
    """CVI: return the int value of a byte representation."""
    cstr = pass_string(x).to_str()
    error.throw_if(len(cstr) < 2)
    return x._values.from_bytes(cstr[:2])

def cvs_(x):
    """CVS: return the single-precision value of a byte representation."""
    cstr = pass_string(x).to_str()
    error.throw_if(len(cstr) < 4)
    return x._values.from_bytes(cstr[:4])

def cvd_(x):
    """CVD: return the double-precision value of a byte representation."""
    cstr = pass_string(x).to_str()
    error.throw_if(len(cstr) < 8)
    return x._values.from_bytes(cstr[:8])


###############################################################################
# comparisons

def _bool_eq(left, right):
    """Return true if left == right, false otherwise."""
    left, right = match_types(left, right)
    return left.eq(right)

def _bool_gt(left, right):
    """Ordering: return -1 if left > right, 0 otherwise."""
    left, right = match_types(left, right)
    return left.gt(right)

def eq(left, right):
    """Return -1 if left == right, 0 otherwise."""
    return left._values.from_bool(_bool_eq(left, right))

def neq(left, right):
    """Return -1 if left != right, 0 otherwise."""
    return left._values.from_bool(not _bool_eq(left, right))

def gt(left, right):
    """Ordering: return -1 if left > right, 0 otherwise."""
    return left._values.from_bool(_bool_gt(left, right))

def gte(left, right):
    """Ordering: return -1 if left >= right, 0 otherwise."""
    return left._values.from_bool(not _bool_gt(right, left))

def lte(left, right):
    """Ordering: return -1 if left <= right, 0 otherwise."""
    return left._values.from_bool(not _bool_gt(left, right))

def lt(left, right):
    """Ordering: return -1 if left < right, 0 otherwise."""
    return left._values.from_bool(_bool_gt(right, left))


###############################################################################
# bitwise operators

def not_(num):
    """Bitwise NOT, -x-1."""
    return num._values.new_integer().from_int(~num.to_int())

def and_(left, right):
    """Bitwise AND."""
    return left._values.new_integer().from_int(
        left.to_integer().to_int(unsigned=True) & right.to_integer().to_int(unsigned=True),
        unsigned=True)

def or_(left, right):
    """Bitwise OR."""
    return left._values.new_integer().from_int(
        left.to_integer().to_int(unsigned=True) | right.to_integer().to_int(unsigned=True),
        unsigned=True)

def xor_(left, right):
    """Bitwise XOR."""
    return left._values.new_integer().from_int(
        left.to_integer().to_int(unsigned=True) ^ right.to_integer().to_int(unsigned=True),
        unsigned=True)

def eqv_(left, right):
    """Bitwise equivalence."""
    return left._values.new_integer().from_int(
        ~(left.to_integer().to_int(unsigned=True) ^ right.to_integer().to_int(unsigned=True)),
        unsigned=True)

def imp_(left, right):
    """Bitwise implication."""
    return left._values.new_integer().from_int(
        (~left.to_integer().to_int(unsigned=True)) | right.to_integer().to_int(unsigned=True),
        unsigned=True)


##############################################################################
# unary operations

def abs_(inp):
    """Return the absolute value of a number. No-op for strings."""
    if isinstance(inp, strings.String):
        # strings pass unchanged
        return inp
    # promote Integer to Single to avoid integer overflow on -32768
    return inp.to_float().clone().iabs()

def neg(inp):
    """Negation (unary -). No-op for strings."""
    if isinstance(inp, strings.String):
        # strings pass unchanged
        return inp
    # promote Integer to Single to avoid integer overflow on -32768
    return inp.to_float().clone().ineg()

def sgn_(x):
    """Sign."""
    return numbers.Integer(None, x._values).from_int(pass_number(x).sign())

def int_(inp):
    """Truncate towards negative infinity (INT)."""
    return pass_number(inp).clone().ifloor()

def fix_(inp):
    """Truncate towards zero."""
    return pass_number(inp).clone().itrunc()

def sqr_(x):
    """Square root."""
    return _call_float_function(math.sqrt, x)

def exp_(x):
    """Exponential."""
    return _call_float_function(math.exp, x)

def sin_(x):
    """Sine."""
    return _call_float_function(math.sin, x)

def cos_(x):
    """Cosine."""
    return _call_float_function(math.cos, x)

def tan_(x):
    """Tangent."""
    return _call_float_function(math.tan, x)

def atn_(x):
    """Inverse tangent."""
    return _call_float_function(math.atan, x)

def log_(x):
    """Logarithm."""
    return _call_float_function(math.log, x)


######################################################################
# string representations and characteristics

def to_repr(inp, leading_space, type_sign):
    """Convert BASIC number to Python str representation."""
    # PRINT, STR$ - yes leading space, no type sign
    # WRITE - no leading space, no type sign
    # LIST - no loading space, yes type sign
    if isinstance(inp, numbers.Number):
        return inp.to_str(leading_space, type_sign)
    elif isinstance(inp, strings.String):
        raise error.RunError(error.TYPE_MISMATCH)
    raise TypeError('%s is not of class Value' % type(inp))

def str_(x):
    """STR$: string representation of a number."""
    return x._values.new_string().from_str(
                to_repr(pass_number(x), leading_space=True, type_sign=False))

def val_(x):
    """VAL: number value of a string."""
    return x._values.from_repr(pass_string(x).to_str(), allow_nonnum=True)

def len_(s):
    """LEN: length of string."""
    return pass_string(s).len()

def space_(num):
    """SPACE$: repeat spaces."""
    return num._values.new_string().space(num)

def asc_(s):
    """ASC: ordinal ASCII value of a character."""
    return pass_string(s).asc()

def chr_(x):
    """CHR$: character for ASCII value."""
    val = x.to_integer().to_int()
    error.range_check(0, 255, val)
    return x._values.new_string().from_str(chr(val))

def oct_(x):
    """OCT$: octal representation of int."""
    # allow range -32768 to 65535
    val = cint_(x, unsigned=True)
    return x._values.new_string().from_str(val.to_oct())

def hex_(x):
    """HEX$: hexadecimal representation of int."""
    # allow range -32768 to 65535
    val = cint_(x, unsigned=True)
    return x._values.new_string().from_str(val.to_hex())


##############################################################################
# binary operations

@float_safe
def pow(left, right):
    """Left^right."""
    if left._values.double_math and (
            isinstance(left, numbers.Double) or isinstance(right, numbers.Double)):
        return _call_float_function(lambda a, b: a**b, left.to_double(), right.to_double())
    elif isinstance(right, numbers.Integer):
        return left.to_single().ipow_int(right)
    else:
        return _call_float_function(lambda a, b: a**b, left.to_single(), right.to_single())

@float_safe
def add(left, right):
    """Add two numbers or concatenate two strings."""
    if isinstance(left, numbers.Number):
        # promote Integer to Single to avoid integer overflow
        left = left.to_float()
    left, right = match_types(left, right)
    # note that we can't call iadd here, as it breaks with strings
    # since between copy and dereference the address may change due to garbage collection
    # it may be better to define non-in-place operators for everything
    return left.add(right)

@float_safe
def sub(left, right):
    """Subtract two numbers."""
    if isinstance(left, strings.String) or isinstance(right, strings.String):
        raise error.RunError(error.TYPE_MISMATCH)
    # promote Integer to Single to avoid integer overflow
    left, right = match_types(left.to_float(), right)
    return left.clone().isub(right)


@float_safe
def mul(left, right):
    """Left*right."""
    if isinstance(left, numbers.Double) or isinstance(right, numbers.Double):
        return left.to_double().clone().imul(right.to_double())
    else:
        return left.to_single().clone().imul(right.to_single())

@float_safe
def div(left, right):
    """Left/right."""
    if isinstance(left, numbers.Double) or isinstance(right, numbers.Double):
        return left.to_double().clone().idiv(right.to_double())
    else:
        return left.to_single().clone().idiv(right.to_single())

@float_safe
def intdiv(left, right):
    """Left\\right."""
    return left.to_integer().clone().idiv_int(right.to_integer())

@float_safe
def mod_(left, right):
    """Left modulo right."""
    return left.to_integer().clone().imod(right.to_integer())