from enum import Enum
from helper import library

# define the possible types of letters
class Letters(Enum):
    SP = 0  # space
    C = 1   # consonant
    M = 2   # m (could be syllabic or consonant)
    N = 3   # n (could be syllabic, consonant, or nasal vowel)
    V = 4   # vowel

# helper functions
def ischar(text):
    return text[0].isalpha()

def chartype(text):
    if ischar(text): 
        if text[0] in ['a', 'e', 'i', 'o', 'u']: return Letters.V
        elif text[0] == 'm': return Letters.M
        elif text[0] == 'n': return Letters.N
        else: return Letters.C
    else: return Letters.SP # punctuation counts as spacing

# syllabify a list of letters, assuming len(letters) != 0
def get_next_syll(letters, syllables, print_it=False):    
    # get types of letters
    # get last char's type
    types = [chartype(letters[-1])]
    
    # get second and third to last chars (if present)
    if len(letters) > 2:
        types.insert(0, chartype(letters[-2]))
        types.insert(0, chartype(letters[-3]))
    # get second to last char, default third to last to SP
    elif len(letters) > 1: 
        types.insert(0, chartype(letters[-2]))
        types.insert(0, Letters.SP)
    # set other values to default value SP
    else:
        types.insert(0, Letters.SP)
        types.insert(0, Letters.SP)
    
    if print_it: print('Types:', types)

    # identify the syllable
    # logic based on Kumolalo 2010
    curr_syll = [] # store current identified syllable
    # handle when last thing isn't a letter
    if (types[-1] == Letters.SP):
        curr_syll = ['SP']
        letters = letters[:-1]
        if print_it: print('SP curr_syll : ', curr_syll)
    # look for CVn (same as DVn in this set up)
    elif (types[-3] in [Letters.C, Letters.M, Letters.N]) and (types[-2] == Letters.V) and (types[-1] == Letters.N):
        curr_syll = letters[-3:]
        letters = letters[:-3]
        if print_it: print('CVn curr_syll : ', curr_syll)
    # look for CV (same as DV)
    elif (types[-2] in [Letters.C, Letters.M, Letters.N]) and (types[-1] == Letters.V):
        curr_syll = letters[-2:]
        letters = letters[:-2]
        if print_it: print('CV curr_syll : ', curr_syll)
    # look for Vn
    elif (types[-2] == Letters.V) and (types[-1] == Letters.N):
        curr_syll = letters[-2:]
        letters = letters[:-2]
        if print_it: print('Vn curr_syll : ', curr_syll)
    # look for V
    elif types[-1] == Letters.V:
        curr_syll = letters[-1:]
        letters = letters[:-1]
        if print_it: print('V curr_syll : ', curr_syll)
    # look for N
    elif types[-1] in [Letters.N, Letters.M]:
        curr_syll = letters[-1:]
        letters = letters[:-1]
        if print_it: print('N curr_syll : ', curr_syll)
    # handle other scenario (must be an error)
    else:
        curr_syll = ['ERR']
        letters = letters[:-1]
        if print_it: print('ERR : ', letters[-3:])

    syllables.insert(0,curr_syll) # add syllable to front of list
    return letters, syllables

def syllabify_letters(letters, print_it = False):
    syllables = []
    while (len(letters) > 0):
        if print_it: print('get_next_syll')
        letters, syllables = get_next_syll(letters, syllables)

    return syllables

def syllabify_df(df):
    syllables = []
    for id, row in df.iterrows():
        letters = library.get_letters(row['sentence'])
        curr_sylls = syllabify_letters(letters)
        syllables.append([id, curr_sylls])
    return syllables