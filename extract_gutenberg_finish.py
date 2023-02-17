import requests
from bs4 import BeautifulSoup
import requests, libvoikko, json, jsonlines, collections, sys
import os.path
from datetime import datetime
import humanize

GUTENBERG_fi = "https://www.gutenberg.org/browse/languages/fi"

gutenberg_html = requests.get(GUTENBERG_fi).text

soup = BeautifulSoup(gutenberg_html, "html.parser")
full_text_file = "fullest_text.txt"


# https://www.gutenberg.org/cache/epub/63138/pg63138.txt
finnish_books = []
full_text = []
counter = 0
start_time = datetime.now()
if not os.path.exists(full_text_file):
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and "/ebooks" in href:
            code = href.split("/")[-1]
            if len(code) == 0:
                continue
            book_url = f"https://www.gutenberg.org/cache/epub/{code}/pg{code}.txt"
            since_start = humanize.precisedelta(datetime.now() - start_time)
            print(f"Opening {counter}. {book_url} at {since_start}")
            r = requests.get(book_url)
            if r.status_code < 400:
                normalized = " ".join(list(set(r.text.lower().split())))
                full_text.append(normalized)
                counter = counter + 1

fullest = " ".join(full_text)

f = open(full_text_file, "w+")
f.write(fullest)
f.close()

normalized_full = list(set(fullest.split()))
print(f"There are {len(normalized_full)} words in this sample")

v = libvoikko.Voikko("fi")
word_forms = [
    (word, v.analyze(word)) for word in normalized_full if len(v.analyze(word)) > 0
]

print("Starting voikko")

flat_words = []
for item in word_forms:
    word = item[0]
    for i in item[1]:
        flat_words.append({"BOOKWORD": word.lower(), **i})

f = open("kotus_all.json")
kotus = json.loads(f.read())
f.close()

book_bw = set([w["BASEFORM"] for w in flat_words])
kotus_w = set([w["word"] for w in kotus])

kotus_dict = dict([(x["word"], x) for x in kotus])


results = []
for bw in flat_words:
    baseform = bw["BASEFORM"]
    if baseform in kotus_dict:
        results.append({**kotus_dict[baseform], **bw})


summary = collections.Counter(
    [
        (w["tn"], w["av"], w["SIJAMUOTO"], w["NUMBER"])
        for w in results
        if "SIJAMUOTO" in w and "NUMBER" in w
    ]
)

# utils
def query(tn, av, list_):
    return sorted(
        list(set([x["BOOKWORD"] for x in list_ if x["tn"] == tn and x["av"] == av]))
    )


def queryform(form, list_):
    return sorted(
        list(
            set(
                [
                    x["BOOKWORD"]
                    for x in list_
                    if "SIJAMUOTO" in x and x["SIJAMUOTO"] == form
                ]
            )
        )
    )


with jsonlines.open("output.jsonl", "w") as writer:
    writer.write_all(results)
