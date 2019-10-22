#!/usr/bin/python3

"""Reads email and WhatsApp conversation export files and writes a HTML file."""

import argparse
import email
from email import policy
import html
import dateutil.parser
import itertools
import jinja2
import os.path
import re
from collections import namedtuple


DEFAULT_CSS = "default.css"
DUPLICATE_TOLERANCE = 60    # seconds

# Format of the standard WhatsApp export line. This is likely to change in the
# future and so this application will need to be updated.
WA_TIME_RE = '(?P<time>[\d:]+( [AP]M)?)'
WA_MESSAGE_RE = ('(?P<date>[.\d/-]+)'
               ',? ' +
               WA_TIME_RE +
               '( -|:) '
               '(?P<name>[^:]+)'
               ': '
               '(?P<body>.*$)')

WA_FIRSTLINE_RE = ('(?P<date>[.\d/-]+)'
               ',? ' +
               WA_TIME_RE +
               '( -|:) '
               '(?P<body>.*$)')



class Error(Exception):
    """Something bad happened."""
    pass


class Users:
    def __init__(self):
        self.users = {}
        self.id_gen = itertools.count(1)
    
    def id(self, name):
        if name and name not in self.users:
            self.users[name] = next(self.id_gen)
        
        return self.users.get(name, '')


users = Users()
Message = namedtuple('Message', 'date user body id type')


def ParseWALine(line):
    """Parses a single line of WhatsApp export file."""
    
    # Try normal chat message
    m = re.match(WA_MESSAGE_RE, line)
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, m.group('name'), m.group('body')
    
    # Maybe it's the first line which doesn't contain a person's name.
    m = re.match(WA_FIRSTLINE_RE, line)
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, "", m.group('body')
    
    return None


def IdentifyWAMessages(lines):
    """Input text can contain multi-line messages. If there's a line that
    doesn't start with a date and a name, that's probably a continuation of the
    previous message and should be appended to it.
    """
    messages = []
    
    def append_message(msg_date, msg_user, msg_body):
        msg = Message(msg_date, msg_user, msg_body, users.id(msg_user), 'whatsapp')
        messages.append(msg)

    
    msg_date = None
    msg_user = None
    msg_body = None
    
    for line in lines:
        m = ParseWALine(line)
        if m is not None:
            if msg_date is not None:
                # We have a new message, so there will be no more lines for the
                # one we've seen previously -- it's complete. Let's add it to
                # the list.
                append_message(msg_date, msg_user, msg_body)
            msg_date, msg_user, msg_body = m
        else:
            if msg_date is None:
                raise Error("Can't parse the first line: " + repr(line) +
                        ', regexes are ' + repr(WA_FIRSTLINE_RE) + 
                        ' and ' + repr(WA_MESSAGE_RE))
            msg_body += '\n' + line.strip()
    
    # The last message remains. Let's add it, if it exists.
    if msg_date is not None:
        append_message(msg_date, msg_user, msg_body)
    
    return messages


def IdentifyEmailMessage(text):
    m = email.message_from_string(text, policy=policy.default)
    
    if 'From' in m:
        
        ### # debug
        ### print("TYPE:", type(m))
        ### for k in m.keys():
        ###     print("ATTR: {}={}".format(k, m[k]))
        ### print("MESSAGE MULTIPART:", m.is_multipart())
        ### for part in m.walk():
        ###     print("PART MULTIPART:", 
        ###         part.get_content_maintype() == 'multipart', 
        ###         part.is_multipart())

        msg_date = dateutil.parser.parse(m.get('Date'), ignoretz=True)
        msg_user = html.escape(m.get('From'))
        msg_body = jinja2.Markup(
            m.get_body(preferencelist=('plain', 'html')).get_content())
        
        return Message(msg_date, msg_user, msg_body, users.id(msg_user), 'email')
    
    return None


def IdentifyMessages(text):
    message = IdentifyEmailMessage(text)
    if message is not None:
        return [ message ]
        
    return IdentifyWAMessages(text.splitlines(True))


def ProcessInputFiles(input_files):
    messages = []
    
    def is_duplicate(msg_date, msg_user, msg_body):
        for m in messages:
            if (msg_user == m[1] and msg_body == m[2]):
                delta = msg_date - m[0]  
                if abs(delta.total_seconds()) <= DUPLICATE_TOLERANCE:
                   return True
        
        return False
    
    
    def append_message(msg):
        if is_duplicate(msg[0], msg[1], msg[2]):
            return
        
        messages.append(msg)
    
    
    for input_file in input_files:
        with open(input_file, 'rt', encoding='utf-8-sig') as fd:
            for msg in IdentifyMessages(fd.read()):
                append_message(msg)
    
    messages.sort(key=lambda m: m.date)
            
    return messages


def TemplateData(messages, input_filenames, collate=True):
    """Create a struct suitable for procesing in a template.
    Returns:
        A dictionary of values.
    """
    by_user = []
    file_basenames = [os.path.splitext(os.path.basename(f))[0]
                      for f in input_filenames]
    
    if collate:
        for user, msgs_of_user in itertools.groupby(messages, lambda m: m.user):
            by_user.append((user, list(msgs_of_user)))
    else:
        for msg in messages:
            by_user.append((msg.user, [msg]))
    
    return dict(by_user=by_user, input_basenames=file_basenames,
                input_full_paths=input_filenames)


def FormatHTML(data, css):    
    tmpl = """<!DOCTYPE html>
    <html>
    <head>
        <title>{{ ", ".join(input_basenames) }}</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>""" + css + """</style>
    </head>
    <body>
        {% for input_file in input_basenames %}
        <h1 class="input_file">{{ input_file }}</h1>
        {% endfor %}
        <div class="speech-wrapper">
        {% for user, messages in by_user %}
            <div class="bubble">
                <div class="txt">
                    <p class="name"><span class="user{{ messages[0].id }}">{{ user }}</span></p>
                    {% for message in messages %}
                    <div class="message">
                        <p>
                        {% for line in message.body.split("\n") %}
                            {{ line | e }}<br>
                        {% endfor %}
                            <span class="timestamp">{{ message.date }}</span>
                        </p>
                    </div>
                    {% endfor %}
                </div>
                <div class="bubble-arrow"></div>
            </div>
        {% endfor %}
        </div>
    </body>
    </html>
    """
    
    return jinja2.Environment().from_string(tmpl).render(**data)


def ParseArguments():   
    parser = argparse.ArgumentParser(
        description='Produce a browsable history of a email '
                    'and WhatsApp conversation')
    parser.add_argument('-c', dest='collate', action='store_true',
                        help='if subsequent messages of same user '
                             'should be combined')
    parser.add_argument('-s', dest='style_file', required=False, 
                        default=DEFAULT_CSS,
                        help='optional style file other than '
                             '"' + DEFAULT_CSS + '"')
    parser.add_argument('-i', dest='input_file', nargs='*', required=True)
    parser.add_argument('-o', dest='output_file', required=True)
    
    return parser.parse_args()


def main(): 
    args = ParseArguments()
    
    messages = ProcessInputFiles(args.input_file)
    template_data = TemplateData(messages, args.input_file, args.collate)
    with open(args.style_file, 'rt', encoding='utf-8-sig') as fd:
        css = fd.read()
    html = FormatHTML(template_data, css)
    with open(args.output_file, 'w', encoding='utf-8') as fd:
        fd.write(html)


if __name__ == '__main__':
    main()
