template ="""
{
  case: { $and: [{$eq:["$SIJAMUOTO", "%s"]}, {$eq:["$NUMBER", "%s"]}]},
  then: %d
},"""

numbers = ["singular", "plural"]
sijamuodot = ["nimento","kohdanto","omanto","olento","osanto","eronto","tulento","sisäolento","sisäeronto","sisätulento","ulko-olento","ulkoeronto","ulkotulento","vajanto","keinonto","seuranto"]

count = 0

for number in numbers:
    for sijamuoto in sijamuodot:
        print(template % (sijamuoto, number, count))
        count += 1
    count = 101