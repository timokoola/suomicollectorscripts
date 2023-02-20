import json
from typing import List
import requests
from bs4 import BeautifulSoup
import os.path
import jsonlines

GUTENBERG_fi = "https://www.gutenberg.org/browse/languages/fi"

gutenberg_html = requests.get(GUTENBERG_fi).text

soup = BeautifulSoup(gutenberg_html, "html.parser")
fullest_text_file = "fullest_text.txt"


# create directory gutenberg if it doesn't exist
if not os.path.exists("gutenberg"):
    os.makedirs("gutenberg")


# function to get all book codes from gutenberg for finnish books
def get_links(url: str) -> List[str]:
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and "/ebooks" in href:
            code = href.split("/")[-1]
            if len(code) == 0:
                continue
            # book_url = f"https://www.gutenberg.org/cache/epub/{code}/pg{code}.txt"
            links.append(code)
    return links


# check if book with code exists in gutenberg directory
# and download it if it doesn't
def download_book(code: str) -> None:
    book_url = f"https://www.gutenberg.org/cache/epub/{code}/pg{code}.txt"
    book_file = f"gutenberg/{code}.txt"
    if not os.path.exists(book_file):
        print(f"Downloading {book_url}")
        r = requests.get(book_url, timeout=10)
        if r.status_code < 400:
            f = open(book_file, "w+")
            f.write(r.text)
            f.close()
        elif r.status_code == 404:
            print(f"Book {code} not found")
            f = open(book_file, "w+")
            f.write("")
            f.close()
    else:
        print(f"Book {code} already exists")


# get kotus data
def get_kotus_data() -> dict:
    f = open("kotus_all.json")
    kotus = json.loads(f.read())
    f.close()
    return kotus


# from kotus_all.json generate a list of singular nimentos
# with tn and av values
def get_kotus_nimentos() -> List[dict]:
    kotus = get_kotus_data()
    nimentos = []
    for item in kotus:
        # if tn > 52, it is not a noun
        if item["tn"] > 52:
            continue
        word = {**item}
        word["BASEFORM"] = word["word"]
        word["BOOKWORD"] = word["word"]
        word["SIJAMUOTO"] = "nimento"
        word["NUMBER"] = "singular"
        nimentos.append(word)
    return nimentos


# generate dictionary key that contains
# all the information needed to identify a word
# in a unique way
# needed fields: BOOKWORD, av, tn, SIJAMUOTO, NUMBER
def get_key(word: dict) -> str:
    return f"{word['BOOKWORD']}_{word['av']}_{word['tn']}_{word['SIJAMUOTO']}_{word['NUMBER']}"


if __name__ == "__main__":
    links = get_links(GUTENBERG_fi)
    for link in links:
        download_book(link)

    # generate the initial result list
    nimentos = get_kotus_nimentos()
    results: dict = dict([(get_key(nimento), nimento) for nimento in nimentos])

    print(f"Found {len(results)} nimentos")

    # loop through all books in gutenberg directory
    full_text = []
    for book in os.listdir("gutenberg"):
        if book.endswith(".txt"):
            print(f"Processing {book}")
            f = open(f"gutenberg/{book}")
            book_text = f.read()
            f.close()
            book_text = " ".join(book_text.lower().split())
            full_text.append(book_text)

    fullest_text = " ".join(full_text)
    normalized_full = list(set(fullest_text.split()))

    # write full text file for posterity
    with open(fullest_text_file, "w+") as f:
        f.write(fullest_text)

    # run all words through voikko
    v = libvoikko.Voikko("fi")
    word_forms = [
        (word, v.analyze(word)) for word in normalized_full if len(v.analyze(word)) > 0
    ]

    kotus = get_kotus_data()
    flat_words = []
    for item in word_forms:
        word = item[0]
        for i in item[1]:
            flat_words.append({"BOOKWORD": word.lower(), **i})

    book_bw = set([w["BASEFORM"] for w in flat_words])
    kotus_w = set([w["word"] for w in kotus])

    kotus_dict = dict([(x["word"], x) for x in kotus])

    # words from gutenberg that have been run through voikko
    gutenberg_results = []
    for bw in flat_words:
        baseform = bw["BASEFORM"]
        if baseform in kotus_dict:
            gutenberg_results.append({**kotus_dict[baseform], **bw})

    # merge results from kotus and gutenberg
    for result in gutenberg_results:
        key = get_key(result)
        if key in results:
            results[key]["COUNT"] += 1
        else:
            results[key] = result
            results[key]["COUNT"] = 1

    with jsonlines.open("output.jsonl", "w") as writer:
        writer.write_all(results)
