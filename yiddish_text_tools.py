import re
from urllib.request import urlopen

pairs = [
    ('וּ', 'וּ'),
    ('יִ', 'יִ'),
    ('ײַ', 'ײַ'),
    ('וו', 'װ'),
    ('וי', 'ױ'),
    ('יי', 'ײ'),
    ('אַ', 'אַ'),
    ('אָ', 'אָ'),
    ('בֿ', 'בֿ'),
    ('כּ', 'כּ'),
    ('פּ', 'פּ'),
    ('פֿ', 'פֿ'),
    ('שׂ', 'שׂ'),
    ('תּ', 'תּ'),
]

def replace_with_precombined(string):
    for pair in pairs:
        string = re.sub(pair[0], pair[1], string)
    string = re.sub('בּ', 'ב', string) # diacritic not used in YIVO
    string = re.sub('בּ', 'ב', string)
    return string

def replace_with_decomposed(string):
    for pair in pairs:
        string = re.sub(pair[1], pair[0], string)
    string = re.sub('ייַ', 'ײַ', string)
    string = re.sub('בּ', 'ב', string) # diacritic not used in YIVO
    string = re.sub('בּ', 'ב', string)
    return string

def replace_punctuation(string):
    string = re.sub(r"-", r"־", string) # YIVO-style hyphen
    string = re.sub(r'[′׳]', "'", string)
    string = re.sub(r'[″״]', '"', string)
    return string
    
def romanise_german(text):
    rom = {"א": "",    "אַ": "a", "אָ": "o",
           "ב": "b",   "בּ": "b", "בֿ": "w",
           "ג": "g",
           "ד": "d",
           "ה": "h",
           "ו": "u",   "וּ": "u",
           "װ": "w",
           "ױ": "eu",
           "ז": "s",
           "ח": "ch",
           "ט": "t",
           "י": "i",   "יִ": "i",
           "ײ": "ei",  "ײַ": "ei",
           "כּ": "k",   "כ": "ch", "ך": "ch",
           "ל": "l",
           "מ": "m",   "ם": "m",
           "נ": "n",   "ן": "n",
           "ס": "ss",
           "ע": "e",
           "פּ": "p",   "פֿ": "f",  "פ": "f", "ף": "f",
           "צ": "z",   "ץ": "z",
           "ק": "k",
           "ר": "r",
           "ש": "sch", "שׂ": "ss",
           "תּ": "t",   "ת": "ss"
        }

    output = ""
    for c in text:
        if c in rom.keys():
            output += rom[c]
        else:
            output += c

    output = re.sub(r"־", r"-", output)
    output = re.sub(r"schp", r"sp", output)
    output = re.sub(r"scht([aeiour])", r"st\1", output)
    output = re.sub(r"\bpun\b", r"fun", output)
    output = re.sub(r"eup", r"euf", output)
    output = re.sub(r"\bi([aeiou])", r"j\1", output)
    output = re.sub(r"([^aeiou])([nl])\b", r"\1e\2", output)

    return output

def respell_loshn_koydesh(text):
    url = 'https://raw.githubusercontent.com/ibleaman/loshn-koydesh-pronunciation/master/orthographic-to-phonetic.txt'
    respellings_list = urlopen(url).read().decode('utf-8')
    respellings_list = respellings_list.split('\n')
    respellings_list = [line for line in respellings_list if line]
    
    lk = {}
    for line in respellings_list:
        key = replace_with_precombined(line.split('\t')[0])
        key = replace_punctuation(key)
        entries = replace_with_precombined(line.split('\t')[1])
        entries = replace_punctuation(entries)
        if key not in lk:
            lk[key] = entries.split(',')
            
    # loop over keys, in reverse order from longest keys to shortest
    for key in sorted(list(lk.keys()), key=len, reverse=True):
        # skip Germanic homographs, which are usually phonetic
        if key not in ["אין", "צום", "בין", "ברי", "מיד", "קין", "שער", "מעגן", "צו", "מאַנס", "טוען", "מערער"]:
            # skip less common LK variants, in favor of more common ones
            if lk[key][0] in ["אַדױשעם", "כאַנוקע", "גדױלע", "כאַװײרע", "מיכיע", "כאָװער", "אָרעװ", "מאָסער", "כיִעס", "זקאָנים", "נעװאָלע", "מאַשלעם", "כפֿאָצים", "כאַכאָמע", "טאַנאָיִם"] and len(lk[key]) > 1:
                replacement = lk[key][1]
            else:
                replacement = lk[key][0]
                
            # replace whole words (separated by spaces & punctuation, but not
            # followed by an apostrophe);
            # also, append a Δ to the respelling so it's not accidentally overwritten
            # (e.g., to avoid סעודה to סודע to סױדע)
            text = re.sub(r'(?<![אאַאָבבֿגדהװווּזחטייִײײַױכּכךלמםנןסעפּפפֿףצץקרששׂתּתΔ])' + key + r'(?![\'אאַאָבבֿגדהװווּזחטייִײײַױכּכךלמםנןסעפּפפֿףצץקרששׂתּת])', 'Δ' + replacement, text)
    
    # missed items
    fixes = {
        "ר'": "רעב",
    }
    for key in fixes:
        text = re.sub(r'(?<![אאַאָבבֿגדהװווּזחטייִײײַױכּכךלמםנןסעפּפפֿףצץקרששׂתּתΔ])' + key + r'(?![\'אאַאָבבֿגדהװווּזחטייִײײַױכּכךלמםנןסעפּפפֿףצץקרששׂתּת])', fixes[key], text)
        
    # remove the added Δ
    text = re.sub('Δ', '', text)
    
    # undo whole-word mistakes
    mistakes = {
        'יוד"שין': "יאַש",
        "יוד״שין": "יאַש",
    }
    for key in mistakes:
        text = re.sub(r'(?<![אאַאָבבֿגדהװווּזחטייִײײַױכּכךלמםנןסעפּפפֿףצץקרששׂתּת])' + key + r'(?![\'אאַאָבבֿגדהװווּזחטייִײײַױכּכךלמםנןסעפּפפֿףצץקרששׂתּת])', mistakes[key], text)
    
    return text
    
def hasidify(text):
    # TODO
    
    return text