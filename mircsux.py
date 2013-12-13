# Copyright (c) 2011, David Beerman
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import sys

CHANNEL = ''

def strip_stuff(line):
    line = line.replace('[', '', 1)
    line = line.replace(']', '', 1)
    return line[:-1]

def finalize(line):
    if line.startswith('\x03'):
        line = line [3:]
    if line != '':
        line = line + '\n'
    return line

def session(line):
    if line.startswith('Session Start:'):
        split = line.split('t:')
        line = '--- Log opened%s' % split[1]
    elif line.startswith('Session Ident:'):
        split = line.split(':')
        global CHANNEL
        CHANNEL = split[1][1:]
        line = ''
    elif line.startswith('Session Time:'):
        split = line.split(' ')
        date = split[2:5] + [split[6]]
        line = 'Day changed %s %s %s %s' % (date[0], date[1], date[2], date[3])
    return line

def nick_change(line):
    line = line.replace('*', '-!-', 1)
    return line

def join(line):
    line = line.replace('*', '-!-', 1)
    line = line.replace('(', '[', 1)
    line = line.replace(')', ']', 1)
    return line

def quit(line):
    line = line.replace('*', '-!-', 1)
    line = line.replace('(', '[', 2)
    line = line.replace(')', ']', 1)
    if line.endswith('Quit'):
        line = line + ' []'
    else:
        line = line[:-1] + ']'
    line = line.replace('Quit', 'has quit', 1)
    return line

def part(line):
    line = line.replace('*', '-!-', 1)
    line = line.replace('(', '[', 2)
    line = line.replace(')', ']', 1)
    if line.endswith(CHANNEL):
        line = line + ' []'
    else:
        line = line[:-1] + ']'
    return line

def mode(line):
    time = line[0:8]
    line = line[8:]
    split = line.split(':')
    nick = split[0].replace(' sets mode', '')[3:]
    action = split[1][1:]
    line = '%s -!- mode/%s [%s] by %s' % (time, CHANNEL, action, nick)
    return line

def kick(line):
    line = line.replace('*', '-!-', 1)
    line = line.replace('was kicked by', 'was kicked from %s by' % CHANNEL, 1)
    line = line.replace('(', '[', 1)
    line = line[:-1] + ']'
    return line

def topic_change(line):
    line.replace('changes topic to', 'changed the topic of %s to:' % CHANNEL, 1)
    return line

def action(line):
    split = line.split('*')
    if (split[1].startswith(' +') or split[1].startswith(' %') or split[1].startswith(' @') or split[1].startswith(' ~')):
        split[1] = ' ' + split[1][2:]
    split[0] = split[0] + ' '
    line = '*'.join(split)
    return line

def chat(line):
    if line == '':
        return line
    else:
        split = line.split('<')
        if not (split[1].startswith('+') or split[1].startswith('%') or split[1].startswith('@') or split[1].startswith('~')):
            split[1] = ' ' + split[1]
            line = '<'.join(split)
        return line

def doitall(mirclog, irssilog):
    for line in mirclog:
        output = ''
        line = strip_stuff(line)
        # Time, date and channel info
        if line.startswith('Session'):
            output = session(line)
        # Nick changes
        elif (line.startswith('\x0303') and 'is now known as' in line):
            output = nick_change(line)
        # Joins
        elif (line.startswith('\x0303') and 'has joined' in line):
            output = join(line)
        # Quits
        elif (line.startswith('\x0302') and 'Quit' in line):
            output = quit(line)
        # Parts
        elif (line.startswith('\x0303') and 'left' in line):
            output = part(line)
        # Mode sets (+v, +b, etc.)
        elif (line.startswith('\x0303') and 'sets mode:' in line):
            output = mode(line)
        # Kicks
        elif (line.startswith('\x0303') and 'was kicked by' in line):
            output = kick(line)
        # Topic changes
        elif (line.startswith('\x0303') and 'changes topic to' in line):            
            output = topic_change(line)
        # Actions (/me does something)
        elif line.startswith('\x0306'):
            output = action(line)
        # Lines by the user logging
        elif line.startswith('\x0301'):
            output = line
        # Catch statement for lines with ctrl-char which are not the above.
        # Generally means those lines are useless for constructing an equivalent irssi log.
        elif line.startswith('\x03'):
            print 'Following line was not used/converted:'
            print line
            print ''
        # Final catch, for at least one odd line defying all categorization <_<;
        elif line[6:].startswith('%s created on' % CHANNEL):
            pass # Which we'll just drop, because srsly
        # All the rest, which _should_ be just normal chat. (And empty lines)
        else:
            output = chat(line)
        output = finalize(output)
        irssilog.write(output)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        mirclog = open(sys.argv[1], 'rU')
        irssilog = open(sys.argv[2], 'w')
        doitall(mirclog, irssilog)
    else:
        print "Usage: mircsux.py [input] [output]"
        print "Example: mircsux.py mirc.log irssi.log"
