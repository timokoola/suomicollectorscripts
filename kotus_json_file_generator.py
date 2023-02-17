import xmltodict, json, collections, typing, random, time

f = open("kotus-sanalista_v1.xml")
kotus_ = f.read()
f.close()

kotus = xmltodict.parse(kotus_)

def toTn(tn):
    pass

def toLine(item):
    if "s" not in item or "t" not in item:
        return (item["s"], -1,"_")
    word = item["s"]
    type_ = item["t"]
    if isinstance(type_, typing.List):
        result = []
        for t_ in type_:
            tn = int(t_["tn"] if "tn" in t_ else "0")
            av = t_["av"] if "av" in t_ else "_"
            result.append((word, tn, av))
        return result
    else:
        tn = int(type_["tn"] if "tn" in type_ else "0")
        if "av" not in type_:
            av = "_"
        elif isinstance(type_["av"], collections.OrderedDict) and "#text" in type_["av"]:
            av = type_["av"]["#text"]
        else:
            av = type_["av"] if "av" in type_ else "_"
        return (word, tn, av)

def toKey(item):
    pass

simple = [toLine(x) for x in kotus['kotus-sanalista']['st'] if "t" in x and not isinstance(x["t"], typing.List)]
complex_ = [toLine(x) for x in kotus['kotus-sanalista']['st'] if "t" in x and isinstance(x["t"], typing.List)]

d = collections.defaultdict(list)
for s in simple:
    d[f"{s[1]}{s[2]}"].append({"word": s[0], "tn": s[1], "av": s[2]})
for c in complex_:
    for s in c:
        d[f"{s[1]}{s[2]}"].append({"word": s[0], "tn": s[1], "av": s[2]})


samples = []
full = []
for k in d.keys():
    for x in d[k]:
        full.append(x)
    if(len(d[k]) < 20):
        for x in d[k]:
            samples.append(x)
    else:
        sample = random.sample(d[k], 20)
        for x in sample:
            samples.append(x)

f = open(f"kotus_samples_{time.time()}.json", "w+")
f.write(json.dumps(samples, sort_keys=True, indent=4))
f.close()

f = open(f"kotus_all.json", "w+")
f.write(json.dumps(full))
f.close()