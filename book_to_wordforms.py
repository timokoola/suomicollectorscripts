import requests, libvoikko, json, jsonlines, collections, sys


if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    print("Need a url that points to a text file")
    sys.exit(0)
r = requests.get(filename)

normalized = list(set(r.text.split()))

v = libvoikko.Voikko("fi")
word_forms = [
    (word, v.analyze(word)) for word in normalized if len(v.analyze(word)) > 0
]

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


f = open("output.json", "w+")
f.write(json.dumps(results, sort_keys=True, indent=4))
f.close()

with jsonlines.open('output.jsonl', 'w') as writer:
    writer.write_all(results)


print(summary)