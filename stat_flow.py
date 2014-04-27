#
# PC-BASIC 3.23 - stat_flow.py
#
# Flow-control statements
# 
# (c) 2013, 2014 Rob Hagemans 
#
# This file is released under the GNU GPL version 3. 
# please see text file COPYING for licence terms.
#

import error
import program

import fp
import vartypes
import util
import expressions
import fileio
import state

def exec_end(ins):
    util.require(ins, util.end_statement)
    state.basic_state.stop = state.basic_state.bytecode.tell()
    program.set_runmode(False)
    # avoid NO RESUME
    state.basic_state.error_handle_mode = False
    state.basic_state.error_resume = None
    fileio.close_all()
    
def exec_stop(ins):
    util.require(ins, util.end_statement)
    raise error.Break()
    
def exec_cont(ins):
    if state.basic_state.stop == None:
        raise error.RunError(17)
    else: 
        program.set_runmode(True, state.basic_state.stop)   
    # IN GW-BASIC, weird things happen if you do GOSUB nn :PRINT "x"
    # and there's a STOP in the subroutine. 
    # CONT then continues and the rest of the original line is executed, printing x
    # However, CONT:PRINT triggers a bug - a syntax error in a nonexistant line number is reported.
    # CONT:PRINT "y" results in neither x nor y being printed.
    # if a command is executed before CONT, x is not printed.
    # in this implementation, the CONT command will overwrite the line buffer so x is not printed.

def exec_for(ins): 
    # read variable  
    varname = util.get_var_name(ins)
    vartype = varname[-1]
    if vartype == '$':
        raise error.RunError(13)
    util.require_read(ins, ('\xE7',)) # =
    start = expressions.parse_expression(ins)
    util.require_read(ins, ('\xCC',))  # TO    
    stop = vartypes.pass_type_keep(vartype, expressions.parse_expression(ins))
    if util.skip_white_read_if(ins, ('\xCF',)): # STEP
        step = vartypes.pass_type_keep(vartype, expressions.parse_expression(ins))
    else:
        # convert 1 to vartype
        step = vartypes.pass_type_keep(vartype, vartypes.pack_int(1))
    util.require(ins, util.end_statement)
    endforpos = ins.tell()
    # find NEXT
    nextpos = find_next(ins, varname)
    # apply initial condition and jump to nextpos
    program.loop_init(ins, endforpos, nextpos, varname, start, stop, step)
    exec_next(ins)
        
def skip_to_next(ins, for_char, next_char, allow_comma=False):
    stack = 0
    while True:
        c = util.skip_to_read(ins, util.end_statement + ('\xCD', '\xA1')) # THEN, ELSE
        # skip line number, if there
        if c == '\0' and util.parse_line_number(ins) == -1:
            break
        # get first keyword in statement    
        d = util.skip_white(ins)  
        if d == '':
            break
        elif d == for_char:
            ins.read(1)
            stack += 1
        elif d == next_char:
            if stack <= 0:
                break
            else:    
                ins.read(1)
                stack -= 1
                # NEXT I, J
                if allow_comma: 
                    while (util.skip_white(ins) not in util.end_statement):
                        util.skip_to(ins, util.end_statement + (',',))
                        if util.peek(ins) == ',':
                            if stack > 0:
                                ins.read(1)
                                stack -= 1
                            else:
                                return
                                
def find_next(ins, varname):
    current = ins.tell()
    skip_to_next(ins, '\x82', '\x83', allow_comma=True)  # FOR, NEXT
    # FOR without NEXT
    util.require(ins, ('\x83', ','), err=26)
    comma = (ins.read(1)==',')
    # get position and line number just after the NEXT
    nextpos = ins.tell()
    # check var name for NEXT
    varname2 = util.get_var_name(ins, allow_empty=True)
    # no-var only allowed in standalone NEXT   
    if varname2 == '':
        util.require(ins, util.end_statement)
    if (comma or varname2) and varname2 != varname:
        # NEXT without FOR 
        errline = program.get_line_number(nextpos-1) if state.basic_state.run_mode else -1
        raise error.RunError(1, errline)    
    ins.seek(current)
    return nextpos 

def exec_next(ins):
    # JUMP to end of FOR statement, increment counter, check condition
    if program.loop_iterate(ins):
        util.skip_to(ins, util.end_statement+(',',))
        if util.skip_white_read_if(ins, (',')):
            # we're jumping into a comma'ed NEXT, call exec_next
            return exec_next(ins)
    
def exec_goto(ins):    
    # parse line number, ignore rest of line and jump
    program.jump(util.parse_jumpnum(ins))
    
def exec_run(ins):
    comma = util.skip_white_read_if(ins, (',',))
    if comma:
        util.require_read(ins, 'R')
    c = util.skip_white(ins)
    jumpnum = None
    if c == '\x0e':   
        # parse line number, ignore rest of line and jump
        jumpnum = util.parse_jumpnum(ins)
    elif c not in util.end_statement:
        name = vartypes.pass_string_unpack(expressions.parse_expression(ins))
        util.require(ins, util.end_statement)
        program.load(fileio.open_file_or_device(0, name, mode='L', defext='BAS'))
    program.init_program()
    program.clear_all(close_files=not comma)
    program.jump(jumpnum)
    state.basic_state.error_handle_mode = False
                
def exec_if(ins):
    # ovoid overflow: don't use bools.
    val = vartypes.pass_single_keep(expressions.parse_expression(ins))
    util.skip_white_read_if(ins, (',',)) # optional comma
    util.require_read(ins, ('\xCD', '\x89')) # THEN, GOTO
    if not fp.unpack(val).is_zero(): 
        # TRUE: continue after THEN. line number or statement is implied GOTO
        if util.skip_white(ins) in ('\x0e',):  
            program.jump(util.parse_jumpnum(ins))    
        # continue parsing as normal, :ELSE will be ignored anyway
    else:
        # FALSE: find ELSE block or end of line; ELSEs are nesting on the line
        nesting_level = 0
        while True:    
            d = util.skip_to_read(ins, util.end_statement + ('\x8B',)) # IF 
            if d == '\x8B': # IF
                # nexting step on IF. (it's less convenient to count THENs because they could be THEN, GOTO or THEN GOTO.)
                nesting_level += 1            
            elif d == ':':
                if util.skip_white_read_if(ins, '\xa1'): # :ELSE is ELSE; may be whitespace in between. no : means it's ignored.
                    if nesting_level > 0:
                        nesting_level -= 1
                    else:    
                        # line number: jump
                        if util.skip_white(ins) in ('\x0e',):
                            program.jump(util.parse_jumpnum(ins))
                        # continue execution from here    
                        break
            else:
                ins.seek(-len(d), 1)
                break
              
def exec_else(ins):
    # any else statement by itself means the THEN has already been executed, so it's really like a REM.
    util.skip_to(ins, util.end_line)  
    
def exec_while(ins, first=True):
    # just after WHILE opcode
    whilepos = ins.tell()
    # evaluate the 'boolean' expression 
    # use double to avoid overflows  
    if first:
        # find matching WEND
        skip_to_next(ins, '\xB1', '\xB2')  # WHILE, WEND
        if ins.read(1) == '\xB2':
            util.skip_to(ins, util.end_statement)
            wendpos = ins.tell()
            state.basic_state.while_wend_stack.append((whilepos, wendpos)) 
        else: 
            # WHILE without WEND
            raise error.RunError(29)
        ins.seek(whilepos)   
    boolvar = vartypes.pass_double_keep(expressions.parse_expression(ins))   
    # condition is zero?
    if fp.unpack(boolvar).is_zero():
        # jump to WEND
        whilepos, wendpos = state.basic_state.while_wend_stack.pop()
        ins.seek(wendpos)   

def exec_wend(ins):
    # while will actually syntax error on the first run if anything is in the way.
    util.require(ins, util.end_statement)
    pos = ins.tell()
    while True:
        if not state.basic_state.while_wend_stack:
            # WEND without WHILE
            raise error.RunError(30) #1  
        whilepos, wendpos = state.basic_state.while_wend_stack[-1]
        if pos != wendpos:
            # not the expected WEND, we must have jumped out
            state.basic_state.while_wend_stack.pop()
        else:
            # found it
            break
    ins.seek(whilepos)    
    return exec_while(ins, False)

def exec_on_jump(ins):    
    onvar = vartypes.pass_int_unpack(expressions.parse_expression(ins))
    util.range_check(0, 255, onvar)
    command = util.skip_white_read(ins)
    jumps = []
    while True:
        d = util.skip_white_read(ins)
        if d in util.end_statement:
            ins.seek(-len(d), 1)
            break
        elif d in ('\x0e',):
            jumps.append( ins.tell()-1 ) 
            ins.read(2)
        elif d == ',':
            pass    
        else:  
            raise error.RunError(2)
    if jumps == []:
        raise error.RunError(2)
    elif onvar > 0 and onvar <= len(jumps):
        ins.seek(jumps[onvar-1])        
        if command == '\x89': # GOTO
            program.jump(util.parse_jumpnum(ins))
        elif command == '\x8d': # GOSUB
            exec_gosub(ins)
    util.skip_to(ins, util.end_statement)    

def exec_on_error(ins):
    util.require_read(ins, ('\x89',))  # GOTO
    linenum = util.parse_jumpnum(ins)
    if linenum != 0 and linenum not in state.basic_state.line_numbers:
        # undefined line number
        raise error.RunError(8)
    error.on_error = linenum
    # ON ERROR GOTO 0 in error handler
    if error.on_error == 0 and state.basic_state.error_handle_mode:
        # re-raise the error so that execution stops
        raise error.RunError(state.basic_state.errn, state.basic_state.erl)
    # this will be caught by the trapping routine just set
    util.require(ins, util.end_statement)

def exec_resume(ins):
    if state.basic_state.error_resume == None: 
        # unset error handler
        error.on_error = 0
        # resume without error
        raise error.RunError(20)
    c = util.skip_white(ins)
    if c == '\x83': # NEXT
        ins.read(1)
        jumpnum = -1
    elif c not in util.end_statement:
        jumpnum = util.parse_jumpnum(ins)
    else:
        jumpnum = 0    
    util.require(ins, util.end_statement)
    error.resume(jumpnum)

def exec_error(ins):
    errn = vartypes.pass_int_unpack(expressions.parse_expression(ins))
    util.range_check(1, 255, errn)
    raise error.RunError(errn)                

def exec_gosub(ins):
    jumpnum = util.parse_jumpnum(ins)
    # ignore rest of statement ('GOSUB 100 LAH' works just fine..); we need to be able to RETURN
    util.skip_to(ins, util.end_statement)
    program.jump_gosub(jumpnum)

def exec_return(ins):
    # return *can* have a line number
    if util.skip_white(ins) not in util.end_statement:    
        jumpnum = util.parse_jumpnum(ins)    
        # rest of line is ignored
        util.skip_to(ins, util.end_statement)    
    else:
        jumpnum = None
    program.jump_return(jumpnum)
        
