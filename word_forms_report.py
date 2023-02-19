import sys
from collections import defaultdict
from pymongo import MongoClient

# read word from command line
word = sys.argv[1]

# mongodb connection
client = MongoClient('localhost', 27017)

# connect to database suomi
db = client.suomi

# connect to collection suomi
collection = db.suomi

# find all documents with word form word
# include only focus null and possessive null
cursor = collection.find({
    'word': word, 
    'POSSESSIVE': {
        '$eq': None
    }, 
    'FOCUS': {
        '$eq': None
    }
})
# count number of documents
count = 0

# {'_id': ObjectId('63efd750a355b7e205b36d61'), 'av': '_', 'tn': 38, 'word': 'hevonen', 'BOOKWORD': 'hevosineen', 'BASEFORM': 'hevonen', 'CLASS': 'nimisana', 'FSTOUTPUT': '[Ln][Xp]hevonen[X]hevos[Sko][Nm]inee[O3]n', 'NUMBER': 'plural', 'POSSESSIVE': '3', 'SIJAMUOTO': 'seuranto', 'STRUCTURE': '=pppppppppp', 'WORDBASES': '+hevonen(hevonen)'}

# number ordering
numbers = ["singular", "plural"]

# sijamuoto ordering
sijamuodot = ["nimento","kohdanto","omanto","olento","osanto","eronto","tulento","sisaolento","sisaeronto","sisatulento","ulkoolento","ulkoeronto","ulkotulento","vajanto","keinonto","seuranto"]

# default dictionary to store sijamuoto and number
words = defaultdict(list)

# iterate over all documents
for document in cursor:
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
print("word", word)
print("tn", document['tn'])
print("av", document['av'])

# print header
print("sijamuoto", "singular", "plural")

for sijamuoto in sijamuodot:
    print (sijamuoto, end="\t")
    # singular form for sijamuoto
    singular_forms = ", ".join(list(set(words['singular' + sijamuoto])))
    # plural form for sijamuoto
    plural_forms =  ", ".join(list(set(words['plural' + sijamuoto])))

    # if singular form is missing, add to missing_forms
    if len(singular_forms) == 0:
        missing_forms.append(sijamuoto + " singular")
    # if plural form is missing, add to missing_forms
    if len(plural_forms) == 0:
        missing_forms.append(sijamuoto + " plural")
    # print singular form
    print(singular_forms, end="\t")
    # print plural form
    print(plural_forms)


# print missing forms
print("missing forms: ", missing_forms)