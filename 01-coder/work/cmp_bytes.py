import hashlib, os
base = r"D:\M6\Module6-workspace\01-coder\04-artifacts\impl\M6.2S"
cur = r"D:\M6\Module6-workspace\01-coder\04-artifacts\impl\M6.2T"
reg = "reg" + "istry"
files = [
    "app/config.py",
    "app/measurement/models/consumed.py",
    "app/measurement/%s/validator.py" % reg,
    "app/measurement/models/%s_feed.py" % reg,
    "app/measurement/scale/recall_risk_mapper.py",
    "app/measurement/adapters/%s_feed_reader.py" % reg,
    "app/measurement/scale/conditions.py",
]
def h(p):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    except FileNotFoundError:
        return "MISSING"
for f in files:
    hb, hc = h(os.path.join(base, f)), h(os.path.join(cur, f))
    print(("IDENTICAL" if hb == hc else "DIFFERS  "), hb, hc, f)
