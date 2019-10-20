#!/usr/bin/python3

import unittest
import datetime
import comm_history

INPUT_1 = ["13/01/18, 01:23 - Fake Name: line1\n", "line2\n"]
INPUT_2 = ["13/01/18, 01:23 - Fake Name: line1\n", "line2\n",
        "13/01/18, 01:24 - Name Two: single line\n"]
INPUT_3 = ["13/01/18, 01:23 - Fake Name: line1\n", "line2\n",
        "13/01/18, 01:24 - Fake Name: line3\n",
        "13/01/18, 01:25 - Name Two: single line\n"]
INPUT_4 = ["14/04/18, 22:08 - Nesta conversa, (…)\n",
           "14/04/18, 22:08 - Alguém: Olá!\n"]
# Format from a different locale setting.
INPUT_5 = ["19-02-18 17:02 - Los mensajes y llamadas en este chat ahora están "
           "protegidos con cifrado de extremo a extremo. Toca para más "
           "información.\n",
           "19-02-18 17:02 - human1: Hola\n",
           "19.02.18 17:14 - human2: como estás?\n"]
# Based on https://github.com/automatthias/whatsapp-archive/issues/1
# 12-hour format.
INPUT_6 = ["2016-06-27, 8:04:08 AM: Neil: Hi\n",]

class IdentifyWAMessagesTest(unittest.TestCase):

    def test1_InputMultiline(self):
        self.assertEqual(comm_history.IdentifyWAMessages(INPUT_1), [
            (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2', 1),
        ])

    def test2_InputTwoMultiline(self):
        self.assertEqual(comm_history.IdentifyWAMessages(INPUT_2), [
            (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2', 1),
            (datetime.datetime(2018, 1, 13, 1, 24), 'Name Two', 'single line', 2),
        ])

    def test3_TemplateData(self):
        messages = comm_history.IdentifyWAMessages(INPUT_3)
        template_data = comm_history.TemplateData(messages, ["fake_filename"])
        self.assertEqual(template_data, {
            'by_user': [
                ('Fake Name', [
                    (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2', 1),
                    (datetime.datetime(2018, 1, 13, 1, 24), 'Fake Name', 'line3', 1)
                ]),
                ('Name Two', [
                    (datetime.datetime(2018, 1, 13, 1, 25), 'Name Two', 'single line', 2)
                ])
            ],
            'input_basenames': ['fake_filename'],
            'input_full_paths': ['fake_filename']})

    def testTemplateDataNoCollate(self):
        messages = comm_history.IdentifyWAMessages(INPUT_3)
        template_data = comm_history.TemplateData(messages, ["fake_filename"], False)
        self.assertEqual(template_data, {
            'by_user': [
                ('Fake Name', [
                    (datetime.datetime(2018, 1, 13, 1, 23), 'Fake Name', 'line1\nline2', 1)
                ]),
                ('Fake Name', [
                    (datetime.datetime(2018, 1, 13, 1, 24), 'Fake Name', 'line3', 1)
                ]),
                ('Name Two', [
                    (datetime.datetime(2018, 1, 13, 1, 25), 'Name Two', 'single line', 2)
                ])
            ],
            'input_basenames': ['fake_filename'],
            'input_full_paths': ['fake_filename']})

    def test4_FirstLineNoColon(self):
        messages = comm_history.IdentifyWAMessages(INPUT_4)
        template_data = comm_history.TemplateData(messages, ["fake_filename"])
        self.assertEqual(template_data, {
            'by_user': [
                ('', [
                    (datetime.datetime(2018, 4, 14, 22, 8), '', 'Nesta conversa, (…)', ''),
                ]),
                ('Alguém', [
                    (datetime.datetime(2018, 4, 14, 22, 8), 'Alguém', 'Olá!', 3),
                ]),
              ],
              'input_basenames': ['fake_filename'],
              'input_full_paths': ['fake_filename']})

    def test5_DifferentFormat(self):
        self.maxDiff = None
        messages = comm_history.IdentifyWAMessages(INPUT_5)
        template_data = comm_history.TemplateData(messages, ["fake_filename"])
        self.assertEqual(template_data, {
            'by_user': [
                ('', [
                    (datetime.datetime(2018, 2, 19, 17, 2),
                        '', 'Los mensajes y llamadas en este chat ahora '
                        'están protegidos con cifrado de extremo a extremo. '
                        'Toca para más información.', ''),
                ]),
                ('human1', [
                    (datetime.datetime(2018, 2, 19, 17, 2), 'human1', 'Hola', 4),
                ]),
                ('human2', [
                    (datetime.datetime(2018, 2, 19, 17, 14), 'human2', 'como estás?', 5),
                ]),
              ],
              'input_basenames': ['fake_filename'],
              'input_full_paths': ['fake_filename']})

    def test6_Neil(self):
        self.maxDiff = None
        messages = comm_history.IdentifyWAMessages(INPUT_6)
        template_data = comm_history.TemplateData(messages, ["fake_filename"])
        self.assertEqual(template_data, {
            'by_user': [
                ('Neil', [
                    (datetime.datetime(2016, 6, 27, 8, 4, 8),
                        'Neil', 'Hi', 6),
                ]),
              ],
              'input_basenames': ['fake_filename'],
              'input_full_paths': ['fake_filename']})


if __name__ == '__main__':
    unittest.main()
