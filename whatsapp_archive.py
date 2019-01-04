#!/usr/bin/python3

"""Reads a WhatsApp conversation export file and writes a HTML file."""

import argparse
import datetime
import dateutil.parser
import itertools
import jinja2
import os.path
import re


DEFAULT_CSS = "default.css"

# Format of the standard WhatsApp export line. This is likely to change in the
# future and so this application will need to be updated.
TIME_RE = '(?P<time>[\d:]+( [AP]M)?)'
WHATSAPP_RE = ('(?P<date>[.\d/-]+)'
               ',? ' +
               TIME_RE +
               '( -|:) '
               '(?P<name>[^:]+)'
               ': '
               '(?P<body>.*$)')

FIRSTLINE_RE = ('(?P<date>[.\d/-]+)'
               ',? ' +
               TIME_RE +
               '( -|:) '
               '(?P<body>.*$)')


class Error(Exception):
    """Something bad happened."""


def ParseLine(line):
    """Parses a single line of WhatsApp export file."""
    
    # Try normal chat message
    m = re.match(WHATSAPP_RE, line)
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, m.group('name'), m.group('body')
    
    # Maybe it's the first line which doesn't contain a person's name.
    m = re.match(FIRSTLINE_RE, line)
    if m:
        d = dateutil.parser.parse("%s %s" % (m.group('date'),
            m.group('time')), dayfirst=True)
        return d, "", m.group('body')
    return None


def IdentifyMessages(lines):
    """Input text can contain multi-line messages. If there's a line that
    doesn't start with a date and a name, that's probably a continuation of the
    previous message and should be appended to it.
    """
    messages = []
    users = {}
    ids = itertools.count(1)
    
    def append_message(msg_date, msg_user, msg_body):
        # assign user id
        if msg_user and msg_user not in users:
            users[msg_user] = next(ids)
        
        data = (msg_date, msg_user, msg_body, users.get(msg_user, ""))
        
        # check duplicate
        if data not in messages:
            messages.append(data)
    
    msg_date = None
    msg_user = None
    msg_body = None
    
    for line in lines:
        m = ParseLine(line)
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
                        ', regexes are ' + repr(FIRSTLINE_RE) + ' and ' + repr(WHATSAPP_RE))
            msg_body += '\n' + line.strip()
    
    # The last message remains. Let's add it, if it exists.
    if msg_date is not None:
        append_message(msg_date, msg_user, msg_body)
    
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
        for user, msgs_of_user in itertools.groupby(messages, lambda x: x[1]):
            by_user.append((user, list(msgs_of_user)))
    else:
        for msg in messages:
            by_user.append((msg[1], [msg]))
    
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
                    <p class="name"><span class="user{{ messages[0][3] }}">{{ user }}</span></p>
                    {% for message in messages %}
                    <div class="message">
                        <p>
                        {% for line in message[2].split("\n") %}
                            {{ line | e }}<br>
                        {% endfor %}
                            <span class="timestamp">{{ message[0] }}</span>
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


def main():    
    parser = argparse.ArgumentParser(description='Produce a browsable history '
            'of a WhatsApp conversation')
    parser.add_argument('-c', dest='collate', action='store_true',
                        help='if subsequent messages of same user should be combined')
    parser.add_argument('-s', dest='style_file', required=False, 
                        default=DEFAULT_CSS,
                        help='optional style file other than "' + DEFAULT_CSS + '"')
    parser.add_argument('-i', dest='input_file', nargs='*', required=True)
    parser.add_argument('-o', dest='output_file', required=True)
    args = parser.parse_args()
    
    lines = []
    for input_file in args.input_file:
        with open(input_file, 'rt', encoding='utf-8-sig') as fd:
            lines += fd.readlines()
    messages = IdentifyMessages(lines)
    
    with open(args.style_file, 'rt', encoding='utf-8-sig') as fd:
        css = fd.read()
    
    template_data = TemplateData(messages, args.input_file, args.collate)
    HTML = FormatHTML(template_data, css)
    
    with open(args.output_file, 'w', encoding='utf-8') as fd:
        fd.write(HTML)


if __name__ == '__main__':
    main()
