import json
from rust_bridge import RustBridge

rb = RustBridge()
params = {
    "mode": "add",
    "f1": 1.0,
    "a1": 1.0,
    "p1": 0.0,
    "f2": 2.0,
    "a2": 0.5,
    "p2": 0.0,
    "duration": 0.5,
    "dt": 0.01,
}
res = rb.run_job(params)
# Summarize the result
summary = {
    "meta": res.get("meta"),
    "time_len": len(res.get("time", [])),
    "y_len": len(res.get("y", [])),
    "y_head": (res.get("y", [])[:5])
}
print(json.dumps(summary))
