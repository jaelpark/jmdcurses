
import curses
import romkan				#kana/romaji conversion
import re					#trim leftover characters from incomplete input conversion

def loopOn(input):
	if isinstance(input,list):
		for i in input:
			yield i;
	else: yield input;

class UIComponentBase:
	def __init__(self, win):
		self.win = win;
	
	def clear(self):
		self.win.erase();
		self.win.move(0,0);
	
class SearchBox(UIComponentBase):
	def __init__(self, win):
		super(SearchBox,self).__init__(win);
		self.bst = [];
		self.buf = [];
	
	def clear(self):
		super(SearchBox,self).clear();
		self.bst.clear();
		self.buf.clear();
	
	def input(self, ch):
		(y,x) = self.win.getyx();
		if ch in (127,curses.ascii.BS,curses.KEY_BACKSPACE):
			if len(self.bst) == 0:
				return False;
			for i in range(self.bst[-1][1]):
				self.win.move(y,x-i-1);
				self.win.delch();
			del self.bst[-1];

			return len(self.bst) > 0;

		self.buf.append(bytes([ch]));
		try:
			a = b''.join(self.buf);
			(y,x) = self.win.getyx(); #some combinations print more than one character, keep track of them
			self.win.addch(a.decode('utf-8'));
			(y,X) = self.win.getyx();
			self.bst.append((a,X-x));
			self.buf.clear();

			return True;
		except UnicodeDecodeError:
			return False;
	
	def gather(self):
		return b''.join([i[0] for i in self.bst]).decode('utf-8');

class SearchResults(UIComponentBase):
	def __init__(self, win, jisho):
		super(SearchResults,self).__init__(win);
		self.jisho = jisho;
		self.results = [];
		self.query = "";
		self.sel = None;
		self.kr = re.compile("[a-zA-Z]");
	
	def clear(self):
		super(SearchResults,self).clear();
		self.results.clear();
		self.query = "";
		self.sel = None;
	
	def set(self, entries, query, sel):
		self.results = entries;
		self.query = query;
		self.sel = sel;
	
	def render(self):
		super(SearchResults,self).clear();

		(h,w) = self.win.getmaxyx();
		for i,entry in enumerate(self.results):

			kele = entry.get("k_ele");
			kele = ([kele] if not isinstance(kele,list) else kele) if kele is not None else [];
			rele = entry.get("r_ele");
			rele = ([rele] if not isinstance(rele,list) else rele) if rele is not None else [];

			index = 0; #re_restr kanji index

			#create kanji->reading dictionary for read restrictions
			kett = {};
			for r in rele:
				try:
					for restr in loopOn(r["re_restr"]):
						if kett.get(restr) is None:
							kett[restr] = index;
							index += 1;
				except KeyError:
					continue;

			#construct the lines for the list view
			fln = "";
			for k in kele:
				if len(fln) > 0:
					fln += ", ";
				fln += k["keb"];
				try:
					fln += "["+str(kett[k["keb"]])+"]";
				except KeyError:
					pass;
					
			for r in rele:
				if len(fln) > 0:
					fln += ", ";
				fln += r["reb"];
				try:
					for restr in loopOn(r["re_restr"]):
						fln += "["+str(kett[restr])+"]";
				except KeyError:
					pass;

			sense = entry["sense"];

			gln = "";
			for s in loopOn(sense):
				for g in loopOn(s["gloss"]):
					if len(gln) > 0:
						gln += ", ";
					gln += g["#text"];

			tagged = False;
			for te in self.jisho.tagdict:
				if entry["ent_seq"] in self.jisho.tagdict[te]:
					fln += " ["+u"\u2764 "+te+"]";
					tagged = True;

			hiragana = romkan.to_hiragana(self.query);
			hiragana = self.kr.sub("",hiragana);
			katakana = romkan.to_katakana(self.query);
			katakana = self.kr.sub("",katakana);
			qs = [(self.query,len(self.query)),(hiragana,len(hiragana)),(katakana,len(katakana))];

			for s in [fln,gln]:
				try:
					#highlight the query
					c = [(1,4),
						[(2+i%2,5+i%2),(20,21)][tagged]
					][self.sel != i];
					q = 0;
					while qs[0][1] > 0:
						Q = -1;
						l = +0;
						for qe in qs:
							if qe[1] == 0:
								continue;
							Q1 = s.find(qe[0],q);
							l1 = qe[1];
							if Q1 != -1 and (Q1 < Q or Q == -1):
								Q = Q1;
								l = l1;
						if Q == -1:
							break;
						self.win.addstr(s[q:Q],curses.color_pair(c[0]));
						self.win.addstr(s[Q:Q+l],curses.color_pair(c[1]));
						q = Q+l;
					self.win.addstr(s[q:],curses.color_pair(c[0]));
					#self.win.addstr(s,curses.color_pair(c[0]));
					(_,x) = self.win.getyx();
					self.win.addstr(' '*(w-x),curses.color_pair(c[0]));

				except curses.error:
					break;
			else:
				continue;
			break;

		self.win.refresh();

	def input(self, ch):
		if self.sel is None:
			return;
		if ch in (ord('j'),curses.KEY_DOWN):
			if self.sel < len(self.results)-1:
				self.sel += 1;
		elif ch in (ord('k'),curses.KEY_UP):
			if self.sel > 0:
				self.sel -= 1;
	
	def gather(self):
		return self.results[self.sel] if self.sel is not None else None;

class EntryScreen(UIComponentBase):
	def __init__(self, win, jisho):
		super(EntryScreen,self).__init__(win);
		self.jisho = jisho;

		self.entries = [];
		self.sel = None;

		(h,w) = self.win.getmaxyx();
		self.suba = self.win.derwin(h-1,int(0.5*w)-2,0,0);
		self.subb = self.win.derwin(h-1,int(0.5*w)+1,0,int(0.5*w)-1);
	
	def resize(self):
		(h,w) = self.win.getmaxyx();
		#self.suba.mvderwin(0,0);
		#self.suba.resize(h-1,int(0.5*w)-2);
		#self.subb.mvderwin(0,int(0.5*w)-1);
		#self.subb.resize(h-1,int(0.5*w)+1);
		self.suba = self.win.derwin(h-1,int(0.5*w)-2,0,0);
		self.subb = self.win.derwin(h-1,int(0.5*w)+1,0,int(0.5*w)-1);
	
	def set(self, entries, sel = 0):
		self.entries = entries; #should be prerandomized for flashcards
		self.sel = sel;
	
	def render(self, flashmode):
		#self.clear();

		self.suba.erase();
		self.suba.move(0,0);

		entry = self.entries[self.sel];
		kele = entry.get("k_ele");
		kele = ([kele] if not isinstance(kele,list) else kele) if kele is not None else [];
		rele = entry.get("r_ele");
		rele = ([rele] if not isinstance(rele,list) else rele) if rele is not None else [];

		index = 0; #re_restr kanji index

		try:
			#create kanji->reading dictionary for read restrictions
			kett = {};
			for r in rele:
				try:
					for restr in loopOn(r["re_restr"]):
						if kett.get(restr) is None:
							kett[restr] = index;
							index += 1;
				except KeyError:
					continue;

			kjlist = [];

			for k in kele:
				kelett = k["keb"];
				self.suba.addstr(kelett);
				#list the individual kanjis
				for kj in kelett:
					if kj not in kjlist and kj in self.jisho.kindex:
						kjlist.append(kj);
				#tag the read restrictions
				tt = kett.get(kelett);
				if tt is not None:
					self.suba.addstr(" ["+str(tt)+"]",curses.color_pair(tt+8));
				self.suba.addstr("\n");

			if not flashmode or len(kele) == 0:
				if len(kele) > 0:
					self.suba.addstr("\nReading:\n");

				for r in rele:
					self.suba.addstr(r["reb"]);
					try:
						for restr in loopOn(r["re_restr"]):
							tt = kett[restr];
							self.suba.addstr("["+str(tt)+"]",curses.color_pair(tt+8));
					except KeyError:
						pass;
					self.suba.addstr("\n");

			if not flashmode:
				self.suba.addstr("\nGlossary:\n");

				sense = entry["sense"];
				sense = [sense] if not isinstance(sense,list) else sense;
				sense = sorted(sense,key=lambda k: k.get("xref") is not None);
				for j in sense:
					xref = j.get("xref");
					if xref is not None:
						for x,xr in enumerate(loopOn(xref)):
							if x > 0:
								self.suba.addstr(", ",curses.color_pair(8));
							self.suba.addstr(xr,curses.color_pair(8));
						self.suba.addstr(" ");
					else: self.suba.addstr("● ");
					for x,g in enumerate(loopOn(j["gloss"])):
						if x > 0:
							self.suba.addstr(", ");
						self.suba.addstr(g["#text"]);
					self.suba.addstr("\n");

				tagged = False;
				self.suba.addstr("\nTags:\n");
				for te in self.jisho.tagdict:
					if entry["ent_seq"] in self.jisho.tagdict[te]:
						self.suba.addstr("["+u"\u2764 "+te+"] ");
						tagged = True;
				if tagged:
					self.suba.addstr("\n");

				self.suba.addstr("\nSequence:\n"+str(entry["ent_seq"]));

		except curses.error:
			pass;

		try:
			self.subb.erase();
			self.subb.move(0,0);

			if not flashmode:
				self.subb.addstr("Kanji:",curses.color_pair(1));
				(_,w) = self.subb.getmaxyx();
				(_,x) = self.subb.getyx();
				self.subb.addstr(' '*(w-x),curses.color_pair(1));

				#problems: are
				for kj in kjlist:
					#self.subb.addstr(kj+"\n");
					ke = self.jisho.kindex[kj];
					self.subb.addstr(kj+" ");
					for k,meaning in enumerate(ke[2]):
						if k > 0:
							self.subb.addstr(", ");
						self.subb.addstr(meaning);
					self.subb.addstr("\n");
					for k,ron in enumerate(ke[0]):
						if k > 0:
							self.subb.addstr(", ");
						self.subb.addstr(ron,curses.color_pair(6));
					if len(ke[0]) > 0:
						self.subb.addstr("\n");
					for k,kun in enumerate(ke[1]):
						if k > 0:
							self.subb.addstr(", ");
						self.subb.addstr(kun,curses.color_pair(6));
					self.subb.addstr("\n\n");

		except curses.error:
			pass;

		self.suba.refresh();
		self.subb.refresh();
	
	def input(self, ch):
		if ch in (ord('j'),curses.KEY_DOWN):
			if self.sel < len(self.entries)-1:
				self.sel += 1;
			else:
				self.sel = 0;
		elif ch in (ord('k'),curses.KEY_UP):
			if self.sel > 0:
				self.sel -= 1;
			else:
				self.sel = len(self.entries)-1;
	
	def gather(self):
		return self.entries[self.sel] if self.sel is not None else None;

class TagBrowser(UIComponentBase):
	def __init__(self, win, jisho):
		super(TagBrowser,self).__init__(win);

		self.jisho = jisho;
		self.tagsel = jisho.tagdef;
		self.sel = 0;
	
	def set(self, sel = None):
		self.taglist = list(self.jisho.tagdict);
		self.taglist.sort();
		if sel is not None:
			self.sel = sel;
	
	def render(self):
		self.clear();
		try:
			(h,w) = self.win.getmaxyx();

			for i,te in enumerate(self.taglist):
				c = [1,[2,7][te == self.tagsel]][self.sel != i];
				self.win.addstr(te+" ["+str(len(self.jisho.tagdict[te]))+"]",curses.color_pair(c));
				if te == self.tagsel:
					self.win.addstr(" [current tag]",curses.color_pair(c));
				(_,x) = self.win.getyx();
				self.win.addstr(' '*(w-x),curses.color_pair(c));

			if self.tagsel not in self.taglist:
				self.win.addstr("[copy to new list \""+self.tagsel+"\"]",curses.color_pair(6));

		except curses.error:
			pass;

		self.win.refresh();
	
	def input(self, ch):
		if ch in (ord('j'),curses.KEY_DOWN):
			if self.sel < len(self.taglist)-1:
				self.sel += 1;
			else:
				self.sel = 0;
		elif ch in (ord('k'),curses.KEY_UP):
			if self.sel > 0:
				self.sel -= 1;
			else:
				self.sel = len(self.taglist)-1;
		elif ch == ord('x'):
			tt = self.gather();
			if tt != self.jisho.tagdef:
				if tt == self.tagsel:
					self.tagsel = self.jisho.tagdef;
				self.jisho.tagdict.pop(tt,None);
				self.set(self.sel if self.sel < len(self.jisho.tagdict) else max(self.sel-1,0));
		elif ch == ord('y'):
			self.tagsel = self.gather();
		elif ch == ord('p'):
			tt = self.gather();
			if tt != self.tagsel:
				tg = self.jisho.tagdict.get(self.tagsel);
				if tg is not None:
					for ts in self.jisho.tagdict[tt]:
						if ts not in tg:
							tg.append(ts);
				else: self.jisho.tagdict[self.tagsel] = list(self.jisho.tagdict[tt]);

				self.set(self.sel);

		return self.tagsel;
	
	def gather(self):
		return self.taglist[self.sel];

