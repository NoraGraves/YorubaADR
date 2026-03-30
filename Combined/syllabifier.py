from enum import Enum
from string import punctuation
import library

class Syllabifier:
    ####################
    # class variables
    ####################
    # define the possible types of letters
    class Letters(Enum):
        P = -2  # punctuation
        SP = -1 # space
        UNK = 0 # unknown char
        C = 1   # consonant
        M = 2   # m (could be syllabic or consonant)
        N = 3   # n (could be syllabic, consonant, or nasal vowel)
        V = 4   # vowel

    # initialize an instance
    def __init__(self, print_it=False):
        # set instance variables
        self.print_it = print_it

        # train the model

    ####################
    # syllabification helper
    ####################
    # is the given text an alphabetic character?
    def _ischar(self, text):
        return text[0].isalpha()

    # is the given text a vowel, consonant, punctuation, etc?
    def _chartype(self, text):
        if self._ischar(text): 
            if text[0] in ['a', 'e', 'i', 'o', 'u']: return self.Letters.V
            elif text[0] == 'm': return self.Letters.M
            elif text[0] == 'n': return self.Letters.N
            else: return self.Letters.C
        elif text[0] in set(punctuation): return self.Letters.P
        elif text[0].isspace(): return self.Letters.SP
        return self.Letters.UNK # char type unknown

    # syllabify a list of letters, assuming len(letters) != 0
    # return new letters, syllables
    def _get_next_syll(self, letters, syllables):  
        # get char types  
        # get last char's type
        types = [self._chartype(letters[-1])]
        # get second and third to last chars (if present)
        if len(letters) > 2:
            types.insert(0, self._chartype(letters[-2]))
            types.insert(0, self._chartype(letters[-3]))
        # get second to last char, default third to last to SP
        elif len(letters) > 1: 
            types.insert(0, self._chartype(letters[-2]))
            types.insert(0, self.Letters.SP)
        # set other values to default value SP
        else:
            types.insert(0, self.Letters.SP)
            types.insert(0, self.Letters.SP)
        if self.print_it: print('Types:', types)

        # identify the syllable
        # logic based on Kumolalo 2010
        curr_syll = [] # store current identified syllable
        # handle when last thing isn't a letter
        if (types[-1] == self.Letters.SP) or (types[-1] == self.Letters.P):
            curr_syll = ['SP', letters[-1]]
            letters = letters[:-1]
            if self.print_it: print('SP curr_syll : ', curr_syll)
        elif (types[-1] == self.Letters.UNK):
            curr_syll = ['UNK', letters[-1]]
            letters = letters[:-1]
            if self.print_it: print('UNK curr_syll : ', curr_syll)

        # look for CVn (same as DVn in this set up)
        elif (types[-3] in [self.Letters.C, self.Letters.M, self.Letters.N]) and (types[-2] == self.Letters.V) and (types[-1] == self.Letters.N):
            curr_syll = letters[-3:]
            letters = letters[:-3]
            if self.print_it: print('CVn curr_syll : ', curr_syll)
        # look for CV (same as DV)
        elif (types[-2] in [self.Letters.C, self.Letters.M, self.Letters.N]) and (types[-1] == self.Letters.V):
            curr_syll = letters[-2:]
            letters = letters[:-2]
            if self.print_it: print('CV curr_syll : ', curr_syll)
        # look for Vn
        elif (types[-2] == self.Letters.V) and (types[-1] == self.Letters.N):
            curr_syll = letters[-2:]
            letters = letters[:-2]
            if self.print_it: print('Vn curr_syll : ', curr_syll)
        # look for V
        elif types[-1] == self.Letters.V:
            curr_syll = letters[-1:]
            letters = letters[:-1]
            if self.print_it: print('V curr_syll : ', curr_syll)
        # look for N
        elif types[-1] in [self.Letters.N, self.Letters.M]:
            curr_syll = letters[-1:]
            letters = letters[:-1]
            if self.print_it: print('N curr_syll : ', curr_syll)
        # handle other scenario (must be an unknown syllable type)
        else:
            curr_syll = ['UNK', letters[-1]]
            letters = letters[:-1]
            if self.print_it: print('UNK : ', letters[-3:])

        syllables.insert(0,curr_syll) # add syllable to front of list
        return letters, syllables

    # turn letters into syllables
    # combine non-standard syllable types (SP a SP b --> SP a b)
    # return syllables
    def _syllabify_letters(self, letters):
        syllables = []
        # get each syllable
        while (len(letters) > 0):
            if self.print_it: print('_get_next_syll')
            letters, syllables = self._get_next_syll(letters, syllables)

        # merge non-standard syllables
        # prev starts out empty, then append label and all letters
        # when it ends, add non-empty one to list of syllables, and reset to empty
        merged_syllables = []
        prev_sp = []
        prev_p = []
        prev_err = []
        prev_unk = []
        def _reset(prev_sp, prev_p, prev_err, prev_unk):
            # find non-empty merged non-standard syllable
            if len(prev_sp) > 0: 
                merged_syllables.append(prev_sp)
                prev_sp = []
            if len(prev_p) > 0:
                merged_syllables.append(prev_p)
                prev_p = []
            if len(prev_err) > 0:
                merged_syllables.append(prev_err)
                prev_err = []
            if len(prev_unk) > 0:
                merged_syllables.append(prev_unk)
                prev_unk = []
            return prev_sp, prev_p, prev_err, prev_unk
        
        for syllable in syllables:
            # collect non-standard syllables but don't add until merged
            if syllable[0] == 'SP':
                if len(prev_sp) == 0: 
                    prev_sp, prev_p, prev_err, prev_unk = _reset(prev_sp, prev_p, prev_err, prev_unk) # reset possible previous merger (only necessary for first item in SP)
                    prev_sp.append('SP') # add label
                prev_sp.append(syllable[1]) # add subsequent items
            elif syllable[0] == 'P':
                if len(prev_p) == 0: 
                    prev_sp, prev_p, prev_err, prev_unk = _reset(prev_sp, prev_p, prev_err, prev_unk)
                    prev_p.append('P') # add label
                prev_p.append(syllable[1]) # add subsequent items
            elif syllable[0] == 'ERR':
                if len(prev_err) == 0: 
                    prev_sp, prev_p, prev_err, prev_unk = _reset(prev_sp, prev_p, prev_err, prev_unk)
                    prev_err.append('ERR') # add label
                prev_err.append(syllable[1]) # add subsequent items
            elif syllable[0] == 'UNK':
                if len(prev_unk) == 0: 
                    prev_sp, prev_p, prev_err, prev_unk = _reset(prev_sp, prev_p, prev_err, prev_unk)
                    prev_unk.append('UNK') # add label
                prev_unk.append(syllable[1]) # add subsequent items

            # add merged non-standard syllables, current syllable, and reset
            else:
                prev_sp, prev_p, prev_err, prev_unk = _reset(prev_sp, prev_p, prev_err, prev_unk) # add any merged non-standard syllables
                # add current syllable
                merged_syllables.append(syllable)
        _reset(prev_sp, prev_p, prev_err, prev_unk)        
        return merged_syllables

    ####################
    # syllabification
    ####################
    # syllabify an entire df of text
    # return the syllables
    def syllabify_df(self, df):
        syllables = []
        for id, row in df.iterrows():
            letters = library.get_letters(row['sentence'])
            curr_sylls = self._syllabify_letters(letters)
            syllables.append([id, curr_sylls])
        return syllables        



