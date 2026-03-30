# ngrams.py
from helper import library
from enum import Enum
from helper import syllab
import pandas as pd

# Create consistent labels for tones
class Tones(Enum):
    H = 1
    M = 0
    L = -1

# possible vowels in Yoruba
VOWELS = ['a','e','i','o','u']

# remove the diacritics from a syllable
# can keep 'underdiacs', 'tone', or 'none'
def _rm_diacritics_syll(syllable, keep='underdiacs'):
    new_syll = []
    for letter in syllable:
        # corner cases
        if letter == 'SP': return syllable
        if letter == 'ERR': return syllable

        # normal syllable
        include = [letter[0]] # keep original letter
        
        # check second char
        if (len(letter) > 1) and ((letter[1] in library.UNDERDIACS) and (keep=='underdiacs')):
            include.append(letter[1])
        if (len(letter) > 1) and ((letter[1] in library.TONECHARS) and (keep=='tone')):
            include.append(letter[1])

        # check third char
        if (len(letter) > 2) and ((letter[2] in library.UNDERDIACS) and (keep=='underdiacs')):
            include.append(letter[2])
        if (len(letter) > 2) and ((letter[2] in library.TONECHARS) and (keep=='tone')):
            include.append(letter[2])

        # create string from included characters
        new_syll.append(''.join(include))
    return new_syll

# remove diacritics from a set of syllables
def rm_diacritics_row(row, keep='underdiacs'):
    return [_rm_diacritics_syll(x, keep) for x in row['Syllables']]

# remove diacritics from df
# can keep 'underdiacs', 'tone', or 'none'
def rm_diacritics_df(df, keep='underdiacs'):
    new_df = df.copy()
    new_df['Syllables'] = new_df.apply(lambda row: rm_diacritics_row(row, keep), axis=1)
    return new_df

# return the index where the tone carrier is located in syllable
def _tone_carrier_index(syllable):
    # find tone carrier in syllable (either N or M alone, or V)
    if len(syllable) == 1: return 0
    
    # if len > 0, tone carrier MUST be a vowel; at most 1 vowel per syll
    else: 
        if (syllable[0][0] in VOWELS): return 0
        else: return 1 # vowel MUST be first or second in syllable

# identify the tone of a syllable
# returns 
def get_tone(syllable):
    # corner cases
    if syllable[0] == 'SP' or syllable[0] == 'ERR': return Tones.M

    tone_carrier = syllable[_tone_carrier_index(syllable)]

    # get tone from tone carrier
    if (len(tone_carrier) > 1) and (tone_carrier[1] in library.TONECHARS):
        tone = tone_carrier[1]
    elif (len(tone_carrier) > 2) and (tone_carrier[2] in library.TONECHARS):
        tone = tone_carrier[2]
    else: return Tones.M # no tone present --> Mid tone

    if tone == library.LOTONE: return Tones.L
    elif tone == library.HITONE: return Tones.H
    else: return Tones.M # default/error is midtone

# add a given tone to a syllable
def _add_tone(syllable, tone):
    if tone == Tones.H: tone_char = library.HITONE
    elif tone == Tones.L: tone_char = library.LOTONE
    else: return syllable # mid tone is unmarked

    index = _tone_carrier_index(syllable)
    new_syll = syllable[:]
    new_syll[index] = ''.join([syllable[index], tone_char])
    return new_syll

# find the n-sized context string for syllable i in syllables
def _get_context(syllables, n, i):
    context = []
    for j in range(1, n+1):
        # get -Syl
        # insert at FRONT of list
        if (i-j >= 0): 
            curr_context = syllables[i-j]
            curr_context = _rm_diacritics_syll(curr_context)
            curr_context_str = ''.join(curr_context)
            context.insert(0, curr_context_str)
        else: context.insert(0, '<') # start of sentence token

        # get +Syl
        # add to END of list
        if (i+j < len(syllables)):
            curr_context = syllables[i+j]
            curr_context = _rm_diacritics_syll(curr_context)
            curr_context_str = ''.join(curr_context)
            context.append(curr_context_str)
        else: context.append('>') # end of sentence token
    
    # merge context into a string
    context_str = '.'.join(context) # -Syl.-Syl.+Syl.+Syl
    return context_str


# get n-grams
# n is the number of items before and after to consider
def _syll_grams(syllables, counts, n):
    # counts has format {syll: {-Syl.-Syl.+Syl.+Syl : {H : count, M : count, L : count}}}
    for i, syll in enumerate(syllables):
        syll_str = ''.join(_rm_diacritics_syll(syll))

        # get contexts for this syllable so far
        poss_contexts = counts.get(syll_str, dict())

        # get current context for syllable
        context_str = _get_context(syllables, n, i)

        # update with new tones
        context_tones = poss_contexts.get(context_str, dict())
        curr_tone = get_tone(syll)
        curr_tone_count = context_tones.get(curr_tone, 0)

        # update all dictionaries
        context_tones.update({curr_tone : curr_tone_count + 1})
        poss_contexts.update({context_str : context_tones})
        counts.update({syll_str : poss_contexts})

    return counts

# create a full n-gram count from a df
def create_syll_grams(df, n=4):
    counts = dict()
    for _, row in df.iterrows():
        counts = _syll_grams(row['Syllables'], counts, n)
    return counts

# predict the tone for each syllable in list of syllables
def pred_tone(syllables, counts, n=4):
    with_tones = []
    
    for i, syll in enumerate(syllables):
        # corner case
        if syll[0] == 'SP' or syll[0] == 'ERR':
            with_tones.append(syll)
            continue

        # get current syllable and its context
        syll_str = ''.join(syll)
        context_str = _get_context(syllables, n, i)

        # collect stored counts
        poss_tones = counts.get(syll_str, dict()).get(context_str, dict())

        # get most frequent tone
        h = poss_tones.get(Tones.H, 0)
        m = poss_tones.get(Tones.M, 0)
        l = poss_tones.get(Tones.L, 0)
        if (h > m) and (h > l): new_syll = _add_tone(syll, Tones.H)
        elif (l > m) and (l > h): new_syll = _add_tone(syll, Tones.L)
        else: new_syll = _add_tone(syll, Tones.M)
        with_tones.append(new_syll)

    return with_tones

# do full predictions
def predict_all_tones(df, counts, n=4):
    new_df = df.copy()
    new_df['Prediction'] = new_df.apply(lambda row: pred_tone(row['Syllables'], counts, n), axis=1)
    return new_df

# calculate word error rate for a row, returns (wrong words, total words)
def _eval_row(row, print_it=False):
    correct = row['Syllables']
    pred = row['Prediction']

    wrong_words = 0
    total_words = 0
    in_word = False # identifies whether currently in a word or not
    curr_word_accurate = True # identifies whether the current word has gotten a tone wrong yet

    # iterate through syllables
    for i in range(len(correct)):
        # check if tones match
        corr_tone = get_tone(correct[i])
        pred_tone = get_tone(pred[i])
        if corr_tone != pred_tone: 
            curr_word_accurate = False

        # check if a word is finished
        if in_word:
            # word has ended
            if correct[i][0] == 'SP':
                in_word = False
                if not curr_word_accurate: 
                    wrong_words += 1
                    if print_it: print('WRONG', correct,pred)
                total_words += 1
                curr_word_accurate = True # reset accuracy
        if correct[i][0] != 'SP': in_word = True

    return pd.Series({'Wrong Words' : wrong_words, 'Total Words' : total_words})

# determine wrong words in df of syllables
def evaluate(df, print_it=False):
    new_df = df.copy()
    new_df[['Wrong Words', 'Total Words']] = new_df.apply(lambda row: _eval_row(row, print_it=print_it), axis=1, result_type='expand')
    return new_df

#
