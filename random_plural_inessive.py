import sys
from collections import defaultdict
from pymongo import MongoClient

# connect to database suomi
client = MongoClient('localhost', 27017)
db = client.suomi

# connect to collection suomi
collection = db.suomi

# find all word with number "plural" and sijamuoto "sisaolento"
# include only focus null and possessive null
cursor = collection.find({
    'NUMBER': 'plural',
    'SIJAMUOTO': 'sisaolento',
    'POSSESSIVE': {
        '$eq': None
    },
})

# put all documents in a list
documents = list(cursor)

# get all bookwords and put in a list
bookwords = list(set([document.get('BOOKWORD') for document in documents]))

# print how many bookwords
print(len(bookwords))

# init random
import random

# Random olla-verbi
olla = random.choice(['olen','olet','olemme','olette','ovat']).capitalize()

# random lisuke
lisuke = random.choice(["aivan ","ihan ","hyvin ","jokseenkin ", "vähän ", "", "aavistuksen "])

# print random document
document = random.choice(bookwords)
text = f"{olla} {lisuke}{document}."

print(text)


