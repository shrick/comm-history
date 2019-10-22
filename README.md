# comm-history

## Overview

Format your exported email and WhatsApp conversation in HTML.

  * WhatsApp: Use the [Saving your chat history][saving] instructions to export your chat history. You'll get an email with a .txt file. Save it on disk.
  * Email: Save each email as a separate file in simple text format (MH or similiar) by using the export functionality of your mail program.

Then run this script.

[saving]: https://faq.whatsapp.com/en/android/23756533/?category=5245251

## Requirements

  * Python 3
  * python3-dateutil (on Debian)
  * python3-jinja2 (on Debian)

## SYNOPSIS

    comm_history.py [-s <style_file>] [-c] -o <output_file> -i <input_file1 [input_file2 ...]>
    
With options as follows:

    -s <style_file>
  
Optional CSS style file to use instead of the bundled default.

    -c
  
Collate subsequent messages by same user.

    -o <output_file>
  
The HTML conversation file to write.
  
    -i <input_file1 [input_file2 ...]>
  
The text input files. You can mix WhatsApp and email export files. But files are read in the order as given on command line. i.e. conversation is NOT ordered by date.

## TODOs

Email integration tasks:
- [x] rename files
- [x] rename GitHub project
- [x] order messages by date
- [ ] add message type to apply different formats
- [ ] parse multiple emails in single text file
- [ ] strip email signature

Common tasks:
- [ ] change message tuples into named tuples
- [ ] efficient duplication check
- [ ] restructure app layout
