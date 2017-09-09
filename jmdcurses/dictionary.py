
import xmltodict as xmld	#JMDict parsing
from gzip import GzipFile	#JMDict streaming 
import pickle				#cache serialization
import romkan				#kana/romaji conversion

def loopOn(input):
	if isinstance(input,list):
		for i in input:
			yield i;
	else: yield input;

class Dictionary:
	def __init__(self, jmfile, kjfile):
		self.jmfile = jmfile;
		self.kjfile = kjfile;
		pass;
	
	def Load(self, dictfile):
		try:
			with open(dictfile,"rb") as f:
				print("Loading dictionary...");
				(self.jmdict,self.rindex,self.kjdict,self.kindex) = pickle.load(f);
		except (OSError,IOError):
			print("Parsing JMdict...");
			self.jmdict = xmld.parse(GzipFile(self.jmfile));
			self.jmdict = self.jmdict["JMdict"]["entry"];
			print("Indexing...");
			self.rindex = {};
			for i,entry in enumerate(self.jmdict):
				try:
					kele = entry["k_ele"];
					for j in loopOn(kele):
						r = j["keb"];
						a = self.rindex.get(r);
						if a is None:
							self.rindex[r] = [i];
						else: a.append(i);
				except KeyError:
					pass;

				try:
					rele = entry["r_ele"];
					for j in loopOn(rele):#rele:
						r = romkan.to_roma(j["reb"]).replace('\'','');
						a = self.rindex.get(r);
						if a is None:
							self.rindex[r] = [i];
						else: a.append(i);
				except KeyError:
					pass;

				sense = entry["sense"];
				for j in loopOn(sense):
					for g in loopOn(j["gloss"]):
						t = g["#text"];
						a = self.rindex.get(t);
						if a is None:
							self.rindex[t] = [i];
						else: a.append(i);
			
			print("Parsing KANJIDIC2...");
			self.kjdict = xmld.parse(GzipFile(self.kjfile));
			self.kjdict = self.kjdict["kanjidic2"]["character"];
			print("Indexing...");
			self.kindex = {};
			for i,entry in enumerate(self.kjdict):
				lit = entry["literal"];

				ron = [];
				kun = [];
				meaning = [];

				try:
					rm = entry["reading_meaning"]["rmgroup"];
				except KeyError:
					continue; #radical: skip for now

				try:
					for rele in loopOn(rm["reading"]):
						if rele["@r_type"] == "ja_on":
							ron.append(rele["#text"]);
						elif rele["@r_type"] == "ja_kun":
							kun.append(rele["#text"]);
				except KeyError:
					pass;

				try:
					for mele in loopOn(rm["meaning"]):
						if isinstance(mele,str): #other than english are dictionaries
							meaning.append(mele);
				except KeyError:
					pass;

				self.kindex[lit] = (ron,kun,meaning);
			
			with open(dictfile,"wb") as f:
				print("Caching...");
				pickle.dump((self.jmdict,self.rindex,self.kjdict,self.kindex),f);
	
	def LoadTags(self, tagfile, tagdef):
		self.tagfile = tagfile;
		self.tagdef = tagdef;
		try:
			with open(self.tagfile,"rb") as f:
				print("Loading tags...");
				self.tagdict = pickle.load(f);
		except (OSError,IOError):
			self.tagdict = {};
			self.tagdict[self.tagdef] = [];

	
	def SaveTags(self):
		if len(self.tagdict) > 1 or len(self.tagdict[self.tagdef]) > 0:
			with open(self.tagfile,"wb") as f:
				pickle.dump(self.tagdict,f);


