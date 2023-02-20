import json
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import os.path
import jsonlines
import libvoikko

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
    pre_len = len(kotus)
    # remove duplicates
    kotus = list({v["word"]: v for v in kotus}.values())
    # report how many duplicates were removed
    print(f"Removed {pre_len - len(kotus)} duplicates")
    f.close()
    return kotus


# from kotus_all.json generate a list of singular nimentos
# with tn and av values
def get_kotus_nimentos() -> List[dict]:
    kotus = get_kotus_data()
    nimentos = []
    for item in kotus:
        # if tn > 51, it is not a noun
        if item["tn"] > 51:
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


def get_book_text(book: str) -> str:
    f = open(f"gutenberg/{book}")
    book_text = f.read()
    f.close()
    book_text = " ".join(book_text.lower().split())
    return book_text


def get_voikko_for_book(book_text: str):
    v = libvoikko.Voikko("fi")
    word_forms = [
        (word, v.analyze(word))
        for word in book_text.split()
        if len(v.analyze(word)) > 0
    ]

    return word_forms


def flatten_voikko_results(word_forms):
    flat_words = []
    for item in word_forms:
        word = item[0]
        for i in item[1]:
            flat_words.append({"BOOKWORD": word.lower(), **i})
    return flat_words


def get_book_words_in_kotus(kotus_dict, flat_words):
    gutenberg_results = []
    for bw in flat_words:
        baseform = bw["BASEFORM"]
        if baseform in kotus_dict and kotus_dict[baseform]["tn"] < 53:
            gutenberg_results.append({**kotus_dict[baseform], **bw})
    return gutenberg_results


def clear_console_line():
    print("\033[K", end="")


def extract_unique_words(unique_words, gutenberg_results):
    unique_gutenberg_words = []
    for item in gutenberg_results:
        # if the word is not in the unique words set
        # add it to the results list
        # and add it to the unique words set
        key = item["BOOKWORD"]
        if key not in unique_words:
            unique_gutenberg_words.append(item)
            unique_words.add(key)
    return unique_gutenberg_words


if __name__ == "__main__":
    links = get_links(GUTENBERG_fi)
    for link in links:
        download_book(link)

    # generate the initial result list
    nimentos = get_kotus_nimentos()
    results = nimentos

    print(f"Found {len(results)} nimentos")
    # write the initial result list to file
    with jsonlines.open("output.jsonl", "w") as writer:
        writer.write_all(results)

    # get kotus data
    kotus = get_kotus_data()
    # set to determine if we need to process the word
    unique_words = set([w["word"] for w in kotus])
    # kotus words as a dictionary for faster lookup
    kotus_dict = dict([(x["word"], x) for x in kotus])

    # count txt files in gutenberg directory
    txt_files = len([f for f in os.listdir("gutenberg") if f.endswith(".txt")])
    file_index = 1

    # loop through all books in gutenberg directory
    for book in os.listdir("gutenberg"):
        if book.endswith(".txt"):
            clear_console_line()
            print(f"Processing {book} ({file_index} of {txt_files})", end=" ")
            book_text = get_book_text(book)
            # run all words through voikko
            # note same word can produce multiple forms
            word_forms = get_voikko_for_book(book_text)

            flat_words = flatten_voikko_results(word_forms)

            # words from current book that have been run through voikko
            # as a set for faster lookup
            book_bw = set([w["BASEFORM"] for w in flat_words])

            # words from gutenberg that have been run through voikko
            gutenberg_results = get_book_words_in_kotus(kotus_dict, flat_words)

            pre_addition = len(unique_words)

            # extract unique words from gutenberg results
            unique_gutenberg_words = extract_unique_words(
                unique_words, gutenberg_results
            )

            # report added unique words
            print(
                f"Added {len(unique_gutenberg_words)} unique words from {book}",
                end="\r",
            )

            # append gutenbergs results to the output file
            with jsonlines.open("/feeds/output.jsonl", "a") as writer:
                writer.write_all(unique_gutenberg_words)

            file_index += 1
