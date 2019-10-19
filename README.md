# comm-html-history

Format your exported email and WhatsApp conversation in HTML.

  * WhatsApp: Use the [Saving your chat history][saving] instructions to export your chat history. You'll get an email with a .txt file. Save it on disk.
  * Email: Save each email as a separate file in simple text format (MH or similiar) by using the export functionality of your mail program.

Then run this script.

Requirements:

   * Python 3
   * python3-dateutil (on Debian)
   * python3-jinja2 (on Debian)

On Linux, run this in shell. On Windows, run this in cmd:

    ./whatsapp_archive.py -i your_file.txt [another_file ...] -o output.html

Or this with collating subsequent messages by same user:

    ./whatsapp_archive.py -c -i your_file.txt [another_file ...] -o output.html

[saving]: https://faq.whatsapp.com/en/android/23756533/?category=5245251
