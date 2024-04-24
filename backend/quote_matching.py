from difflib import SequenceMatcher
from dataclasses import dataclass, asdict
from dataClassDefinitions import source, defaultFunctionInput, inputWithBigramModel, sourceWithBigramModel
from collections import defaultdict, Counter

UNKNOWN = ""


def bag_of_bigrams(words: list[str]) -> dict[str, dict[str, list]]:
    bigrams = dict()
    previous = ""
    for i in range(len(words)):
        if previous in bigrams:
            if words[i] in bigrams[previous]:
                # append location of bigram
                bigrams[previous][words[i]].append(i - 1)
            else:
                bigrams[previous].update({words[i]: [i - 1]})
        else:
            bigrams[previous] = {words[i]: [i - 1]}
        previous = words[i]

    return bigrams


def bigram_model(document: sourceWithBigramModel) -> dict:
    bigrams = dict()

    counts = defaultdict(Counter)
    bigram_locs = bag_of_bigrams(document.sourceTokenizedText)
    for bigram_start in bigram_locs.keys():
        for bigram_end, locs in bigram_locs[bigram_start].items():
            counts[bigram_start][bigram_end] += len(locs)

    vocabs = dict()
    for prev, counter in counts.items():
        vocabs[prev] = len(counter)

    vocab = set(counts.keys())
    for _, ccs in counts.items():
        vocab.update(ccs.keys())

    max_total = 0
    for prev, ccs in counts.items():
        total = sum(ccs.values()) + vocabs[prev]
        if total > max_total:
            max_total = total
        temp = {curr: (count + 1) / total for curr, count in ccs.items()}
        temp[UNKNOWN] = 1 / total
        bigrams[prev] = temp
    bigrams[UNKNOWN] = 1 / max_total

    return bigrams


def find_style_matches(documents: inputWithBigramModel) -> tuple[inputWithBigramModel, list[dict]]:
    errors = []
    input = documents.textInputTokenized
    for source in documents.sources:
        if source.bigramModel is None:
            source.bigramModel = bigram_model(source)

        score = 0
        start = 0
        for i in range(1, len(input)):
            prev = input[i - 1]
            curr = input[i]
            # checks each line
            if "\n" in curr or i == len(input) - 1:
                score /= i - start
                if score >= 0.25:
                    errors.append({
                        'typeOfError': f'Content Match with {source.parenthetical}',
                        'textToFix': input[start:i],
                        'suggestedFix': None
                    })
                score = 0
                start = i + 1

            if prev not in source.bigramModel:
                score += source.bigramModel[UNKNOWN]
            else:
                if curr not in source.bigramModel[prev]:
                    curr = UNKNOWN
                score += source.bigramModel[prev][curr]

    return documents, errors


def exact_quote_match(orig: list[str], comp: list[str], threshold=5) -> list[tuple[int, int, list[str]]]:
    quotes = []
    orig_bigrams = bag_of_bigrams(orig)

    # exact match
    i = 1
    while i in range(1, len(comp)):
        if comp[i - 1] in orig_bigrams:
            if comp[i] in orig_bigrams[comp[i - 1]]:
                # if bigram is in both original and comparison, search for end of exact match
                for j in orig_bigrams[comp[i - 1]][comp[i]]:
                    if i + 1 < len(comp) - 1:
                        k_comp = i + 1
                    else:
                        k_comp = len(comp) - 1
                    if j + 2 < len(orig) - 1:
                        k_orig = j + 2
                    else:
                        k_orig = len(orig) - 1

                    while (k_orig < len(orig) - 1 and k_comp < len(comp) - 1 and
                           orig[k_orig] == comp[k_comp]):
                        k_comp += 1
                        k_orig += 1
                    # if the match meets the threshold for significant matches, return it as a quote
                    if j > 0:
                        j_index = j - 1
                    else:
                        j_index = 0
                    if k_orig + 1 < len(orig):
                        k_orig_index = k_orig + 1
                    else:
                        k_orig_index = k_orig
                    if k_orig - j >= threshold and (orig[j_index] != '\"' or orig[k_orig_index] != '\"'):
                        quotes.append((j, i - 1, orig[j:k_orig]))
                    i = k_comp
        i += 1

    return quotes


# helper method for similar matches
def find_range(len_orig: int, len_comp: int, quote: tuple[int, int, list[str]], reach=5) -> tuple[int, int, int, int]:
    orig_begin = quote[0] - reach
    before_reach = reach
    if orig_begin < 0:
        before_reach += orig_begin
        orig_begin = 0
    comp_begin = quote[1] - before_reach
    if comp_begin < 0:
        orig_begin -= comp_begin
        comp_begin = 0

    orig_end = quote[0] + len(quote[2]) + reach
    after_reach = reach
    if orig_end > len_orig:
        after_reach -= orig_end - len_orig
        orig_end = len_orig
    comp_end = quote[1] + len(quote[2]) + after_reach
    if comp_end > len_comp:
        orig_end -= comp_end - len_comp
        comp_end = len_comp

    return orig_begin, orig_end, comp_begin, comp_end


def similar_quote_match(orig: list[str], comp: list[str]) -> list[tuple[int, int, list[str]]]:
    quotes = []
    exact_quotes = exact_quote_match(orig, comp, 2)
    for exact_quote in exact_quotes:
        quote_orig_begin, quote_comp_begin, quote = exact_quote
        orig_begin, orig_end, comp_begin, comp_end = find_range(len(orig), len(comp), exact_quote, len(quote))
        # compare before sentence
        before_ratio = SequenceMatcher(a="".join(orig[orig_begin:quote_orig_begin]),
                                       b="".join(comp[comp_begin:quote_comp_begin])).ratio()
        # compare after ratio
        after_ratio = SequenceMatcher(a="".join(orig[(quote_orig_begin + len(quote)):orig_end]),
                                      b="".join(comp[(quote_orig_begin + len(quote)):comp_end])).ratio()
        if 1.0 > before_ratio > 0.5 and 1.0 > after_ratio > 0.5:
            quotes.append((orig_begin, comp_begin, orig[orig_begin:orig_end]))
        elif 1.0 > before_ratio > 0.5:
            quotes.append((orig_begin, comp_begin, orig[orig_begin:(quote_orig_begin + len(quote))]))
        elif 1.0 > after_ratio > 0.5:
            quotes.append((quote_orig_begin, quote_comp_begin, orig[quote_orig_begin:orig_end]))
        else:
            continue

        # check that it doesn't overlap with anything else. If so, merge them
        comp_quote = quotes[len(quotes) - 1]
        for i in range(len(quotes) - 1):
            # if quotes overlap...
            if (quotes[i][0] < comp_quote[0] < quotes[i][0] + len(quotes[i][2]) or
                    quotes[i][0] < comp_quote[0] + len(comp_quote[2]) < quotes[i][0] + len(quotes[i][2])):
                # put in a new one...
                min_orig = min(quotes[i][0], comp_quote[0])
                max_orig = max(quotes[i][0] + len(quotes[i][2]), comp_quote[0] + len(comp_quote[2]))
                quotes.append((min_orig, min(quotes[i][1], comp_quote[1]),
                               orig[min_orig:max_orig]))

                # remove the olds... and end loop
                quotes.pop(i)
                quotes.pop(len(quotes) - 2)
                break

    return quotes


def find_quote_errors(documents: defaultFunctionInput) -> list[dict]:
    errors = []

    for source in documents.sources:
        exact_quotes = exact_quote_match(documents.textInputTokenized, source.sourceTokenizedText)
        for quote in exact_quotes:
            errors.append({
                'typeOfError': 'Missing Quotation',
                'textToFix': quote[2],
                'suggestedFix': ' '.join(['\"'] + quote[2] + ['\"', source.parenthetical])
            })

        similar_quotes = similar_quote_match(documents.textInputTokenized, source.sourceTokenizedText)
        for quote in similar_quotes:
            overlap = False
            for exact_quote in exact_quotes:
                if quote[0] >= exact_quote[0] and quote[0] + len(quote) <= exact_quote[0] + len(exact_quote):
                    overlap = True

            if not overlap:
                errors.append({
                    'typeOfError': 'Poor Paraphrasing',
                    'textToFix': quote[2],
                    'suggestedFix': None
                })

    return errors
