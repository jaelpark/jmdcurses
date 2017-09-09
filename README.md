# JMDcurses
JMdcurses is a console Japanese-English dictionary with typeahead bidirectional queries and custom study lists (including flashcards). JMdcurses is written in Python, and features a curses interface and VI-like key bindings. For the words and translations JMdcurses uses the [JMDict/EDICT](http://www.edrdg.org/jmdict/j_jmdict.html) and [KANJIDIC2](http://www.edrdg.org/kanjidic/kanjd2index.html) dictionaries, property of the [Electronic Dictionary Research and Development Group](http://www.edrdg.org/).

Up to date dictionary files must be separately downloaded. Two files are required, the Japanese-English dictionary [JMdict_e.gz](http://www.edrdg.org/jmdict/edict_doc.html#IREF01) and the kanji dictionary [kanjidic2.xml.gz](http://www.edrdg.org/kanjidic/kanjd2index.html). By default JMDcurses looks for these files in the working directory. The dictionaries are indexed and cached to a configurable location. See the man page for instructions.

## Dependencies

 - `xmltodict` to import the dictionaries
 - `python-romkan` to handle queries in romaji

