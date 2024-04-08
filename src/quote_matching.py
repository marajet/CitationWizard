from difflib import SequenceMatcher


def bag_of_bigrams(words: list[str]):
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


def exact_quote_match(orig: list[str], comp: list[str], threshold=3) -> list[tuple[int, int, list[str]]]:
    quotes = []
    orig_bigrams = bag_of_bigrams(orig)

    # exact match
    i = 1
    while i in range(1, len(comp)):
        if comp[i - 1] in orig_bigrams:
            if comp[i] in orig_bigrams[comp[i - 1]]:
                # if bigram is in both original and comparison, search for end of exact match
                for j in orig_bigrams[comp[i - 1]][comp[i]]:
                    k_search = i + 1
                    k_orig = j + 2
                    while (k_orig < len(orig) and k_search < len(comp) and
                           orig[k_orig] == comp[k_search]):
                        k_search += 1
                        k_orig += 1
                    # if the match meets the threshold for significant matches, return it as a quote
                    if k_orig - j >= threshold:
                        quotes.append((j, i - 1, orig[j:k_orig]))
                        i = k_search
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


# note: this function does NOT match exact quotes!
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
        if before_ratio > 0.5 and after_ratio > 0.5:
            quotes.append((orig_begin, comp_begin, orig[orig_begin:orig_end]))
        elif before_ratio > 0.5:
            quotes.append((orig_begin, comp_begin, orig[orig_begin:(quote_orig_begin + len(quote))]))
        elif after_ratio > 0.5:
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


def find_quote_errors(documents: list[list[str]]) -> list[dict]:
    errors = []

    for i in range(1, len(documents)):
        exact_quotes = exact_quote_match(documents[0], documents[i])
        for quote in exact_quotes:
            errors.append({
                'typeOfError': 'Missing Quotation',
                'textToFix': quote[2],
                'suggestedFix': ['\"'] + quote[2] + ['\"']
            })

        similar_quotes = similar_quote_match(documents[0], documents[i])
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


if __name__ == "__main__":
    files = []
    original = ("Anyway there's some other stuff here, etc. Given that hugles are great bugs, please do nothing." +
                " Some more other stuff for the sake of variety.")
    same = ("Let's look at another example. Given that hugles are great bugs, please do nothing." +
                          " Have you ever seen anything as neat as that?")
    similar = ("Well I said just like that! Given that hugles are big bugs, please don't do anything."
                             + " Well anyway, there we were and I said to him, there we were!")
    different = "Well there we were walking down to the river, and I said..."
    files.append(original.split(" "))
    files.append(same.split(" "))
    files.append(similar.split(" "))
    files.append(different.split(" "))
    print(find_quote_errors(files))
