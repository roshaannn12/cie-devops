from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

# Use plain ASCII labels throughout the UI to avoid encoding issues.
s = s.replace("? &nbsp; Overview", "OVERVIEW &nbsp;")
s = s.replace("? &nbsp; My Tasks", "TASKS &nbsp;")
s = s.replace("? &nbsp; Activity", "ACTIVITY &nbsp;")
s = s.replace("? &nbsp; Settings", "SETTINGS &nbsp;")
s = s.replace(">{check}</button>", ">{'DONE' if done else 'OPEN'}</button>")
s = s.replace("? Application operational", "STATUS: Application operational")
s = s.replace("? &nbsp; Application health", "OK &nbsp; Application health")
s = s.replace("? &nbsp; Container runtime", "DOCKER &nbsp; Container runtime")
s = s.replace("? &nbsp; Orchestration", "K8S &nbsp; Orchestration")
s = s.replace("? &nbsp; Metrics endpoint", "METRICS &nbsp; Metrics endpoint")
s = s.replace("? Application operational", "ONLINE &nbsp; Application operational")

p.write_text(s, encoding="utf-8")
print("Updated UI labels.")
