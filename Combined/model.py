from enum import Enum
import library
import pandas as pd

# train and use a model
class Model:
    # initialize instance
    def __init__(self, add_diacrtic, eval_diacritic, keep, n, print_it=False):
        self.add_diacritic = add_diacrtic
        self.eval_diacritic = eval_diacritic
        self.keep = keep # which diacritics to maintain (can be 'underdiacs', 'tone', or 'none')
        self.n = n
        self.print_it = print_it
        self.counts = [] # empty at first

    ################
    # HELPERS
    ################ 
    # remove the diacritics from a syllable
    # return the syllable with diacritics removed
    def _rm_diacritics_syll(self, syllable):
        new_syll = []
        # loop through each letter in syllable
        for letter in syllable:
            # corner cases
            if (letter == 'SP') or (letter == 'P'): return syllable
            if (letter == 'ERR') or (letter == 'UNK'): 
                new_syll.append(letter)
                continue
            if (letter[0:2] == 'gb'):
                new_syll.append(letter[0:2])
                continue

            # normal syllable
            include = [letter[0]] # keep original letter
                    
            # check second char
            if (len(letter) > 1) and ((letter[1] in library.UNDERDIACS) and (self.keep=='underdiacs')):
                include.append(letter[1])
            if (len(letter) > 1) and ((letter[1] in library.TONECHARS) and (self.keep=='tone')):
                include.append(letter[1])

            # check third char
            if (len(letter) > 2) and ((letter[2] in library.UNDERDIACS) and (self.keep=='underdiacs')):
                include.append(letter[2])
            if (len(letter) > 2) and ((letter[2] in library.TONECHARS) and (self.keep=='tone')):
                include.append(letter[2])

            # create string from included characters
            new_syll.append(''.join(include))
        return new_syll

    # remove diacritics from a set of syllables
    def rm_diacritics_row(self, row):
        return [self._rm_diacritics_syll(x) for x in row['Syllables']]

    # remove diacritics from df
    # can keep 'underdiacs', 'tone', or 'none'
    def rm_diacritics_df(self, df):
        new_df = df.copy()
        new_df['Syllables'] = new_df.apply(lambda row: self.rm_diacritics_row(row), axis=1)
        return new_df

    # find the n-sized context string for syllable i in syllables
    def _get_context(self, syllables, n, i):
        context = []
        for j in range(1, n+1):
            # get -Syl
            # insert at FRONT of list
            if (i-j >= 0): 
                curr_context = syllables[i-j]
                curr_context = self._rm_diacritics_syll(curr_context)
                if (curr_context[0] == 'SP') or (curr_context[0] == 'ERR') or (curr_context[0] == 'UNK'):
                    curr_context_str = curr_context[0]
                else: curr_context_str = ''.join(curr_context)
                context.insert(0, curr_context_str)
            else: context.insert(0, '<') # start of sentence token

            # get +Syl
            # add to END of list
            if (i+j < len(syllables)):
                curr_context = syllables[i+j]
                curr_context = self._rm_diacritics_syll(curr_context)
                if (curr_context[0] == 'SP') or (curr_context[0] == 'ERR') or (curr_context[0] == 'UNK'):
                    curr_context_str = curr_context[0]
                else: curr_context_str = ''.join(curr_context)
                context.append(curr_context_str)
            else: context.append('>') # end of sentence token
        
        # merge context into a string
        context_str = '.'.join(context) # -Syl.-Syl.+Syl.+Syl
        return context_str

    ################
    # TONE FUNCTIONS
    ################
    # return the index where the tone carrier is located in syllable
    def _tone_carrier_index(self, syllable):
        # find tone carrier in syllable (either N or M alone, or V)
        if len(syllable) == 1: return 0
        
        # if len > 0, tone carrier MUST be a vowel; at most 1 vowel per syll
        else: 
            if (syllable[0][0] in library.VOWELS): return 0
            else: return 1 # vowel MUST be first or second in syllable

    # identify the tone of a syllable
    # returns the tone type
    def _get_tone(self, syllable):
        # corner cases
        if syllable[0] == 'SP' or syllable[0] == 'P' or syllable[0] == 'ERR' or syllable[0] == 'UNK': return 'M'

        tone_carrier = syllable[self._tone_carrier_index(syllable)]

        # get tone from tone carrier
        if (len(tone_carrier) > 1) and (tone_carrier[1] in library.TONECHARS):
            tone = tone_carrier[1]
        elif (len(tone_carrier) > 2) and (tone_carrier[2] in library.TONECHARS):
            tone = tone_carrier[2]
        else: return 'M' # no tone present --> Mid tone

        if tone == library.LOTONE: return 'L'
        elif tone == library.HITONE: return 'H'
        else: return 'M' # default/error is midtone

    # add a given tone to a syllable
    # return syllable with tone added
    def _add_tone(self, syllable, tone):
        if tone == 'H': tone_char = library.HITONE
        elif tone == 'L': tone_char = library.LOTONE
        else: return syllable # mid tone is unmarked

        index = self._tone_carrier_index(syllable)
        new_syll = syllable[:]
        new_syll[index] = ''.join([syllable[index], tone_char])
        return new_syll

    ################
    # DOT FUNCTIONS
    ################

    # determine which letters get dots
    # type = both, vowels, or cons
    def _dots_present(self, syllable):
        dots = []
        for index, letter in enumerate(syllable):
            if (letter[0] in library.DOTCONS):
                # print('DOTCONS', letter, len(letter))
                if (len(letter) > 1) and (letter[1] in library.UNDERDIACS): dots.append('1')
                elif (len(letter) > 2) and (letter[2] in library.UNDERDIACS): dots.append('1')
                else: dots.append('0')
            if (letter[0] in library.DOTVOWELS):
                # print('DOTVOWELS', letter, len(letter))
                if (len(letter) > 1) and (letter[1] in library.UNDERDIACS): dots.append('1')
                elif (len(letter) > 2) and (letter[2] in library.UNDERDIACS): dots.append('1')
                else: dots.append('0')
            if len(dots) <= index: dots.append('0')

        return ' '.join(dots)

    # add given dots to a syllable
    def _add_dots(self, syllable, dots):
        new_syll = []
        dots = dots.split(' ')
        # iterate through letters and add dots
        for index, letter in enumerate(syllable):
            if (dots[index] == '1'): 
                curr_char = ''.join([letter, library.UNDERDOT])
            else: curr_char = letter
            new_syll.append(curr_char)
        return new_syll

    ################
    # TRAINING
    ################
    # get n-grams
    # n is the number of items before and after to consider
    def _syll_grams(self, syllables, counts):
        # initialize empty dictionaries
        if not counts: 
            counts = []
            for i in range(self.n+1): counts.append(dict())
        
        # counts has format [n=0, n=1, ..., {syll: {-Syl.-Syl.+Syl.+Syl : {value : count, value : count, value : count}}}]
        # value is Tone:Dots (tone is H M L, dots are 010)
        for i, syll in enumerate(syllables):
            syll_str = ''.join(self._rm_diacritics_syll(syll))
            # corner case
            if (syll[0] == 'SP') or (syll[0] == 'ERR') or (syll[0] == 'UNK'):
                syll_str = syll[0]

            # find all contexts in range 0-n (inclusive)
            for j in range(self.n+1):
                # get contexts for this syllable so far
                poss_contexts = counts[j].get(syll_str, dict())

                # get current context for syllable
                context_str = self._get_context(syllables, j, i)
                context_counts = poss_contexts.get(context_str, dict())

                # find current tone if necessary
                # context_tones = poss_contexts.get(context_str, dict())
                if (self.add_diacritic == 'tone') or (self.add_diacritic == 'both'):
                    curr_tone = self._get_tone(syll)
                else: curr_tone = ' '

                # find current dots if necessary
                if (self.add_diacritic == 'dots') or (self.add_diacritic == 'both'):
                    curr_dot = self._dots_present(syll)
                else: curr_dot = ' '

                # add to counts
                curr_diacs = ''.join([curr_tone, curr_dot])
                curr_diac_count = context_counts.get(curr_diacs, 0)

                # update all dictionaries
                context_counts.update({curr_tone : curr_diac_count + 1})
                poss_contexts.update({context_str : context_counts})
                counts[j].update({syll_str : poss_contexts})
        self.counts = counts
        return counts

    # create a full n-gram count from a df
    def create_syll_grams(self, df):
        counts = dict()
        for _, row in df.iterrows():
            counts = self._syll_grams(row['Syllables'], counts)
        self.counts = counts
        return counts

    ################
    # PREDICTIONS
    ################
    # predict the diacritics for each syllable in list of syllables
    def _pred_diacs(self, syllables):
        with_diacs = []
        
        for i, syll in enumerate(syllables):
            # corner case
            if syll[0] == 'SP' or syll[0] == 'ERR':
                with_diacs.append(syll)
                continue

            # get current syllable and its context WITH BACKOFF
            syll_str = ''.join(syll)
            new_syll = ''
            # try n, n-1, ..., 0 (and stop as soon as it is possible)
            for j in range(self.n, -1, -1):
                # get context
                context_str = self._get_context(syllables, j, i)

                # collect stored counts
                poss_diacs = self.counts[j].get(syll_str, dict()).get(context_str, dict())

                # get most frequent diacs
                pred_tone = ''
                pred_dots = ''
                max_use = -1
                for key,value in poss_diacs.items():
                    if value > max_use:
                        pred_tone,pred_dots = key.split(':')
                        max_use = value
                    # if values are equal, arbitrarily keep whichever has the dot pattern seen first
                    # if only the tones differ, revert to a default M
                    if value == max_use:
                        n_tone, n_dots = key.split(':')
                        if (n_dots == pred_dots):
                            n_tone = 'M'

                # add dots if necessary
                syll_with_diacs = syll
                if (self.add_diacritic == 'dots') or (self.add_diacritic == 'both'):
                    syll_with_diacs = self._add_dots(syll_with_diacs, pred_dots)

                # add tone if necessary
                if (self.add_diacritic == 'tone') or (self.add_diacritic == 'both'):
                    syll_with_diacs = self._add_tone(syll_with_diacs, pred_tone)

                # break if this syllable/sequence of syllables exists in these n-grams
                if not poss_diacs: continue # dictionary is empty, so keep trying
                else: 
                    if(self.print_it) : print('n-gram found, stopping; j = ',j,  syll_str, context_str)
                    break # dictionary was found, so stop going to smaller syllables
            with_diacs.append(new_syll)

        return with_diacs

    # predict the tone for each syllable in list of syllables
    def _pred_tone(self, syllables):
        with_tones = []
        
        for i, syll in enumerate(syllables):
            # corner case
            if syll[0] == 'SP' or syll[0] == 'ERR':
                with_tones.append(syll)
                continue

            # get current syllable and its context WITH BACKOFF
            syll_str = ''.join(syll)
            new_syll = ''
            # try n, n-1, ..., 0 (and stop as soon as it is possible)
            for j in range(self.n, -1, -1):
                # get context
                context_str = self._get_context(syllables, j, i)

                # collect stored counts
                poss_tones = self.counts[j].get(syll_str, dict()).get(context_str, dict())

                # get most frequent tone
                h = poss_tones.get('H', 0)
                m = poss_tones.get('M', 0)
                l = poss_tones.get('L', 0)

                # add the tone
                if (h > m) and (h > l): new_syll = self._add_tone(syll, 'H')
                elif (l > m) and (l > h): new_syll = self._add_tone(syll, 'L')
                else: new_syll = self._add_tone(syll, 'M')

                # break if this syllable/sequence of syllables exists in these n-grams
                if not poss_tones: continue # dictionary is empty, so keep trying
                else: 
                    if(self.print_it) : print('n-gram found, stopping; j = ',j,  syll_str, context_str)
                    break # dictionary was found, so stop going to smaller syllables
            with_tones.append(new_syll)

        return with_tones

    ################
    # EVALUATION
    ################
    # calculate word error rate for a row, returns (wrong words, total words)
    def _eval_row(self, row):
        correct = row['Syllables']
        pred = row['Prediction']

        wrong_words = 0
        total_words = 0
        in_word = False # identifies whether currently in a word or not
        curr_word_accurate = True # identifies whether the current word has gotten a tone wrong yet

        # iterate through syllables
        for i in range(len(correct)):
            # check if tones match if necessary for eval
            if (self.eval_diacritic == 'tone') or (self.eval_diacritic == 'both'):
                corr_tone = self._get_tone(correct[i])
                pred_tone = self._get_tone(pred[i])
                if corr_tone != pred_tone: 
                    curr_word_accurate = False

            # check if underdots match if necessary for eval

            # check if a word is finished
            if in_word:
                # word has ended
                if correct[i][0] == 'SP':
                    in_word = False
                    if not curr_word_accurate: 
                        wrong_words += 1
                        if self.print_it: print('WRONG', correct,pred)
                    total_words += 1
                    curr_word_accurate = True # reset accuracy
            if correct[i][0] != 'SP': in_word = True

        return pd.Series({'Wrong Words' : wrong_words, 'Total Words' : total_words})

    # determine wrong words in df of syllables
    def evaluate(self, df):
        new_df = df.copy()
        new_df[['Wrong Words', 'Total Words']] = new_df.apply(lambda row: self._eval_row(row), axis=1, result_type='expand')
        return new_df
