import sys
from collections import defaultdict
from pymongo import MongoClient

# bail out if not enough arguments and print usage
if len(sys.argv) < 3:
    print("Usage: python3 word_form_report_by_type.py <tn> <av>")
    sys.exit(0)

# read av and tn from command line
tn = sys.argv[1]
av = sys.argv[2]

# mongodb connection
client = MongoClient('localhost', 27017)

# connect to database suomi
db = client.suomi

# connect to collection suomi
collection = db.suomi

# make tn  a integer
tn = int(tn)

# find all documents where tn and av match
# include only focus null and possessive null
cursor = collection.find({
    'tn': tn,
    'av': av,
    'POSSESSIVE': {
        '$eq': None
    },
    'FOCUS': {
        '$eq': None
    }
})

# number ordering
numbers = ["singular", "plural"]

# sijamuoto ordering
sijamuodot = ["nimento","kohdanto","omanto","olento","osanto","eronto","tulento","sisaolento","sisaeronto","sisatulento","ulkoolento","ulkoeronto","ulkotulento","vajanto","keinonto","seuranto"]

# default dictionary to store sijamuoto and number
words = defaultdict(list)

count = 0

# iterate over all documents
for document in cursor:
    # if no NUMBER or SIJAMUOTO, skip
    if 'NUMBER' not in document or 'SIJAMUOTO' not in document:
        continue
    dictionary_key = document['NUMBER'] + document['SIJAMUOTO']
    # print document
    words[dictionary_key].append(document['BOOKWORD'])
    # increase total count
    count += 1

# bail out if no documents found
if count == 0:
    print("No documents found")
    sys.exit(0)

missing_forms = []

# print words in order, if word is missing, add to missing_forms
# write to table with three columns
# sijamuoto, singular, plural

# print word, tv, and av
print("tn", document['tn'])
print("av", document['av'])

# print header
print("sijamuoto", "singular", "plural")

for sijamuoto in sijamuodot:
    print (sijamuoto, end="\t")
    # singular form for sijamuoto, pick random example word
    singular_forms = list(set(words['singular' + sijamuoto]))
    # plural form for sijamuoto
    plural_forms =  list(set(words['plural' + sijamuoto]))

    # if singular form is missing, add to missing_forms
    if len(singular_forms) == 0:
        missing_forms.append(sijamuoto + " singular")
    # if plural form is missing, add to missing_forms
    if len(plural_forms) == 0:
        missing_forms.append(sijamuoto + " plural")
    # print singular form
    singular_form_example = singular_forms[0] if len(singular_forms) > 0 else ""
    print(singular_form_example, end="\t")
    # print plural form
    plural_form_example = plural_forms[0] if len(plural_forms) > 0 else ""
    print(plural_form_example)


# print missing forms
print("missing forms", ", ".join(missing_forms))