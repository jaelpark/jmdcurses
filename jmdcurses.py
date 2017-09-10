#!/usr/bin/python

import curses
from curses.textpad import rectangle

import locale
from optparse import OptionParser
import difflib				#dictionary lookup
from random import shuffle	#randomized flashcards

import jmdcurses

class Layout:
	QUERY = 1;
	ENTRY = 2;
	TAGBR = 3;
	def __init__(self, stds, jisho):
		self.stds = stds;

		(h,w) = self.stds.getmaxyx();

		self.wsbox = curses.newwin(1,w-4,2,2); #nlines, ncols, beginy, beginx
		self.wrbox = curses.newwin(h-3,w-4,5,2);
		self.webox = curses.newwin(h-3,w-4,2,2);
		self.wtbox = curses.newwin(h-3,w-4,2,2);

		self.sbox = jmdcurses.uicomponent.SearchBox(self.wsbox);
		self.rbox = jmdcurses.uicomponent.SearchResults(self.wrbox,jisho);
		self.ebox = jmdcurses.uicomponent.EntryScreen(self.webox,jisho);
		self.tbox = jmdcurses.uicomponent.TagBrowser(self.wtbox,jisho);

		self.layout = self.QUERY;
		self.flashmode = False;
	
	def RenderBorder(self, win, stds):
		(y,x) = win.getbegyx();
		(h,w) = win.getmaxyx();
		rectangle(stds,y-1,x-1,h+2,w+2);

	def set(self, layout = None):
		if layout != None:
			self.layout = layout;
		if self.layout == self.QUERY:
			self.RenderBorder(self.wsbox,self.stds);
			self.stds.refresh();

			self.rbox.render();

		elif self.layout == self.ENTRY:
			self.RenderBorder(self.webox,self.stds);
			self.stds.refresh();

			self.ebox.render(self.flashmode);

		elif self.layout == self.TAGBR:
			self.RenderBorder(self.wtbox,self.stds);
			self.stds.refresh();

			self.tbox.render();

def main(stds, jisho):
	#stds = curses.initscr();
	curses.start_color();
	curses.use_default_colors();
	curses.init_pair(1,-1,curses.COLOR_RED);
	curses.init_pair(2,-1,234);
	curses.init_pair(3,-1,-1);
	curses.init_pair(4,10,curses.COLOR_RED);
	curses.init_pair(5,10,234);
	curses.init_pair(6,10,-1);
	curses.init_pair(7,233,3); #current tag
	
	curses.init_pair(20,-1,23); #35 #tagged entry
	curses.init_pair(21,10,23); #highlight query in tagged entry

	for i in range(8,16):
		curses.init_pair(i,i,-1);
	
	curses.noecho();
	curses.cbreak();
	stds.keypad(True);

	layout = Layout(stds,jisho);

	layout.set(layout.QUERY);
	focus = stds;
	
	while True:
		try:
			c = focus.getch();
			if c == curses.KEY_RESIZE:
				(h,w) = stds.getmaxyx();
				stds.clear();
				stds.refresh();

				layout.wsbox.resize(1,w-4);
				layout.wrbox.resize(h-3,w-4);
				layout.webox.resize(h-3,w-4);
				layout.wtbox.resize(h-3,w-4);

				layout.ebox.resize();
				
				layout.set();

			elif focus is layout.sbox.win:
				if c == 10:
					query = layout.sbox.gather();
					if len(query) > 5 and query[0:5] == ":tag ":
						layout.tbox.tagsel = query[5:];
					focus = stds;
				elif c in (10,27):
					focus = stds;
				elif layout.sbox.input(c):
					query = layout.sbox.gather();
					m = difflib.get_close_matches(query,
						[x for x in jisho.rindex \
							if query in x and (len(query) > 1 or len(x) < 3) \
							and (len(query) > 3 or len(x) < 6)],12);

					results = [];
					dup = set();
					for i in m:
						for j in jisho.rindex[i]:
							if j in dup:
								continue;
							dup.add(j);

							results.append(jisho.jmdict[j]);
					
					layout.rbox.clear();
					layout.rbox.set(results,query,0);
					layout.rbox.render();

			elif c == ord('q'):
				break;

			elif c in (ord('t'),ord(' ')):
				entry = layout.rbox.gather();
				if entry is not None:
					try:
						td = jisho.tagdict[layout.tbox.tagsel];
						try:
							td.remove(entry["ent_seq"]);
						except ValueError:
							td.append(entry["ent_seq"]);
					except KeyError:
						jisho.tagdict[layout.tbox.tagsel] = [entry["ent_seq"]];
				if focus is stds:
					layout.rbox.render();
			
			elif c == ord('T'):
				entry = layout.rbox.gather();
				if entry is not None:
					jisho.tagdict[jisho.tagdef].append(entry["ent_seq"]);
				if focus is stds:
					layout.rbox.render();

			elif focus is layout.ebox.win:
				if c in (ord('h'),curses.KEY_LEFT,27):
					stds.erase();

					focus = stds;
					layout.flashmode = False;

					layout.rbox.sel = layout.ebox.sel;
					layout.set(layout.QUERY);

				elif c in (ord('l'),curses.KEY_RIGHT):
					layout.ebox.render(False);

				else:
					layout.ebox.input(c);
					layout.ebox.render(layout.flashmode);

			elif focus is layout.tbox.win:
				if c in (ord('h'),ord('i'),curses.KEY_LEFT,27):
					stds.erase();
					
					if c == ord('i'):
						layout.sbox.clear();
						focus = layout.sbox.win;
					else: focus = stds;

					#layout.rbox.sel = layout.ebox.sel;
					layout.set(layout.QUERY);

				elif c in (ord('l'),curses.KEY_RIGHT):
					stds.erase();

					focus = stds;

					results = [];
					for te in jisho.tagdict[layout.tbox.gather()]:
						for de in jisho.jmdict:
							if te == de["ent_seq"]:
								results.append(de);
								break;
					
					layout.rbox.clear();
					layout.rbox.set(results,"",0);
					layout.set(layout.QUERY);

				else:
					layout.tbox.input(c);
					layout.tbox.render();

			else: #focus on stds
				if c == ord('E'):
					results = [];
					tg = jisho.tagdict.get(layout.tbox.tagsel);
					if tg is not None:
						for te in tg:
							for de in jisho.jmdict:
								if te == de["ent_seq"]:
									results.append(de);
									break;
						layout.rbox.set(results,"",0);
						layout.rbox.render();

				elif c == ord('e'):
					focus = layout.tbox.win;

					layout.tbox.set();
					layout.set(layout.TAGBR);

				elif c == ord('r'): #flashcards from the currently visible list
					if len(layout.rbox.results) > 0:
						flashcards = layout.rbox.results;
						shuffle(flashcards);
						stds.erase();

						focus = layout.ebox.win;
						layout.flashmode = True;

						layout.ebox.set(flashcards,0);
						layout.set(layout.ENTRY);
						#layout.ebox.render(layout.flashmode);

				elif c == ord('i'):
					layout.sbox.clear();
					focus = layout.sbox.win;

				elif c == ord(':'):
					layout.sbox.clear();
					focus = layout.sbox.win;
					layout.sbox.input(c);

				elif c in (ord('l'),curses.KEY_RIGHT):
					entry = layout.rbox.gather();
					if entry is not None:
						stds.erase();

						focus = layout.ebox.win;

						layout.ebox.set(layout.rbox.results,layout.rbox.sel);
						layout.set(layout.ENTRY);

				else:
					layout.rbox.input(c);
					layout.rbox.render();
		except KeyboardInterrupt:
			focus = stds;

	curses.nocbreak();
	stds.keypad(False);
	curses.echo();
	curses.endwin();

locale.setlocale(locale.LC_ALL,"");

opt = OptionParser();
opt.option_list[0].help = "Print this help screen and exit";
opt.add_option("-j","--jmdict",default="./JMdict_e.gz",metavar="FILE",action="store",type="string",dest="jmfile",help="Location of the JMdict_e xml.gz [default: %default]");
opt.add_option("-k","--kjdict",default="./kanjidic2.xml.gz",metavar="FILE",action="store",type="string",dest="kjfile",help="Location of the KANJIDIC2 xml.gz [default: %default]");
opt.add_option("-c","--cache",default="/tmp/jmdcurses.bin",metavar="FILE",action="store",type="string",dest="cache",help="Location of the index cache [default: %default]");
opt.add_option("-t","--tagfile",default="./jmdcurses.tags.bin",metavar="FILE",action="store",type="string",dest="tagfile",help="Location of the tag file [default: %default]");
(options,args) = opt.parse_args();

jisho = jmdcurses.dictionary.Dictionary(options.jmfile,options.kjfile);

try:
	jisho.Load(options.cache);
except (OSError,IOError):
	print("Unable to find the required dictionary files.");
	exit(0);

jisho.LoadTags(options.tagfile,"favorites");

curses.wrapper(main,jisho);

jisho.SaveTags();

