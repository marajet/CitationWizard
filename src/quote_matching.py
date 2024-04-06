from collections import defaultdict, Counter


def bag_of_bigrams(words: list[str]):
    bigrams = dict()

    previous = ""
    for i in range(len(words)):
        if previous in bigrams:
            if words[i] in bigrams[previous]:
                # append location of bigram
                bigrams[previous][words[i]].append(i-1)
            else:
                bigrams[previous].update({words[i]: [i-1]})
        else:
            bigrams[previous] = {words[i]: [i-1]}
        previous = words[i]

    return bigrams


def quote_match(orig: str, comp: str):
    quotes = []
    threshold = 3
    orig_words = orig.split(" ")
    orig_bigrams = bag_of_bigrams(orig_words)

    searchable = comp.split(" ")
    i = 1
    while i in range(1, len(searchable)):
        if searchable[i-1] in orig_bigrams:
            if searchable[i] in orig_bigrams[searchable[i-1]]:
                # if bigram is in both original and comparison...
                for j in orig_bigrams[searchable[i-1]][searchable[i]]:
                    k_search = i + 1
                    k_orig = j + 2
                    while k_orig < len(orig_words) and k_search < len(searchable) and orig_words[k_orig] == searchable[k_search]:
                        k_search += 1
                        k_orig += 1
                    if k_orig - j >= threshold:
                        quotes.append((j, k_orig-1, orig_words[j:k_orig]))
                        i = k_search
        i += 1

    return quotes


if __name__ == "__main__":
    files = {}
    files.update({"original": "Given that hugles are great bugs, please do nothing. hugles yeah hugles yeah"})
    files.update({"same": "Given that hugles are great bugs, please do nothing."})
    files.update({"similar": "hugles yeah hugles yeah Given that hugles are big bugs, please don't do anything. " +
                             "hugles yeah hugles yeah"})
    files.update({"different": "Well there we were walking down to the river, and I said..."})
    print(quote_match(files["original"], files["same"]))
    print(quote_match(files["original"], files["similar"]))
    print(quote_match(files["original"], files["different"]))
