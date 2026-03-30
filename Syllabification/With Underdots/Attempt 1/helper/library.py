import pandas as pd
import unicodedata

# diacritics as their unicode value
LOTONE = chr(0x0300)
HITONE = chr(0x0301)
RISETONE = chr(0x030C)
MIDTONE1 = chr(0x0304)
MIDTONE2 = chr(0x0305)
TONECHARS = {LOTONE, HITONE, RISETONE,MIDTONE1,MIDTONE2}

UNDERDOT = chr(0x0323)
UNDERLINE = chr(0x0329)
UNDERDIACS = {UNDERDOT, UNDERLINE}

# split characters into letters (with their diacritics)
def get_letters(text):
    try:
        text = unicodedata.normalize('NFD', text)
    except:
        print(text)
        return []
    text = text.replace(UNDERLINE, UNDERDOT)
    # MAYBE DO THIS??? # text = text.lower()
    letters = []
    i = 0
    while i < len(text):
        curr_letter = ''
        # look for gb
        if ((i+1) < len(text) and ((text[i] == 'g') and (text[i+1] == 'b'))):
            curr_letter = text[i:i+2]
            i+=2

        # check if next char exists and is a diacritic
        elif ((i+1) < len(text)) and ((text[i+1] in TONECHARS) or text[i+1] in UNDERDIACS):
            if ((i+2) < len(text) and ((text[i+2] in TONECHARS) or text[i+2] in UNDERDIACS)):
                curr_letter = text[i:i+3]
                # print(f"{text[i:i+3]}\t{text[max(i-4, 0):i+4]}\t{text}")
                i+=3 # skip next two chars
            else:
                curr_letter = text[i:i+2]
                i+=2 # skip next char
                
        # normal case (the letter is one single char)
        else: 
            curr_letter = text[i]
            i+=1 # go to next char
        
        # add letter to list
        letters.append(curr_letter.lower())
    return letters

# load in data
def load_dataset(filename):
    return pd.read_csv(filename, header=0, index_col=0)