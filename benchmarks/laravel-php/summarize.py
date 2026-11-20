"""Summarize results.jsonl: per workload and PHP version, median ms per iteration over all samples,
the interquartile range, and the change against PHP 8.3."""
import json, statistics, sys
from collections import defaultdict

data = defaultdict(list)
for line in open(sys.argv[1]):
    r = json.loads(line)
    data[(r["workload"], r["php"].rsplit(".", 1)[0], r["php"])].extend(r["ms"])

def q(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)

labels = {"request": "Full request (boot + route + Eloquent + Blade)", "eloquent": "Eloquent: 1,000 posts + authors, toArray",
          "blade": "Blade: render 50 posts", "collections": "Collections: 100k items pipeline"}
print("| Workload | PHP | Median ms | IQR ms | Samples | vs 8.3 |")
print("|---|---|---:|---:|---:|---:|")
for w in ["request", "eloquent", "blade", "collections"]:
    rows = sorted((k, v) for k, v in data.items() if k[0] == w)
    base = next((statistics.median(v) for k, v in rows if k[1] == "8.3"), None)
    for (wl, minor, full), v in rows:
        m = statistics.median(v)
        rel = "" if minor == "8.3" or not base else "%+.1f%%" % ((m / base - 1) * 100)
        print("| %s | %s | %.3f | %.3f–%.3f | %d | %s |" % (labels[w], full, m, q(v, .25), q(v, .75), len(v), rel))
