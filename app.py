from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock
from html import escape
import json
from urllib.parse import parse_qs, urlparse

tasks = [
    {"id": 1, "title": "Set up Git repository", "done": True},
    {"id": 2, "title": "Build Docker image", "done": True},
    {"id": 3, "title": "Deploy app to Kubernetes", "done": False},
    {"id": 4, "title": "Configure Prometheus monitoring", "done": False},
]
next_id = 5
requests_total = 0
lock = Lock()

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TaskFlow - CI/CD Demo | DevOps Dashboard</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f7fb;color:#172033;
font-family:Inter,"Segoe UI",Arial,sans-serif}.layout{display:flex;min-height:100vh}
aside{width:225px;background:#17243a;color:#cbd5e1;padding:28px 18px}
.brand{font-size:23px;font-weight:800;color:white;margin:0 0 40px}
.brand span{color:#60a5fa}.nav{padding:12px;border-radius:9px;margin:8px 0}
.nav.active{background:#293c59;color:white}.small{font-size:12px;color:#94a3b8;
margin-top:38px;line-height:2}main{padding:36px;max-width:1100px;flex:1}
.top{display:flex;justify-content:space-between;align-items:center;gap:16px}
h1{margin:0;font-size:29px}p{color:#64748b}.pill{background:#dcfce7;color:#166534;
padding:9px 13px;border-radius:20px;font-size:12px;font-weight:700}
.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:28px 0}
.card,.panel{background:white;border:1px solid #e5eaf2;border-radius:14px;padding:22px;
box-shadow:0 4px 14px #17243a08}.label{color:#64748b;font-size:13px}
.num{font-size:30px;font-weight:800;margin-top:10px}.blue{color:#2563eb}
.panel h2{font-size:18px;margin:0 0 8px}.add{display:flex;gap:10px;margin:20px 0}
input{min-width:0;flex:1;border:1px solid #d6deea;border-radius:8px;padding:12px;font-size:14px}
button{border:0;border-radius:8px;padding:11px 14px;background:#2563eb;color:white;
font-weight:700;cursor:pointer}button:hover{opacity:.88}.task{display:flex;align-items:center;
gap:12px;padding:15px 0;border-bottom:1px solid #edf0f5}.task:last-child{border:0}
.task-title{flex:1}.done{text-decoration:line-through;color:#94a3b8}
.actions{display:flex;gap:7px}.secondary{background:#e8efff;color:#1d4ed8}
.delete{background:#fee2e2;color:#b91c1c}.status{font-size:11px;color:#64748b}
footer{margin-top:24px;font-size:12px;color:#94a3b8}
@media(max-width:700px){aside{width:145px;padding:20px 10px}main{padding:20px 12px}
.cards{grid-template-columns:1fr}h1{font-size:23px}.top{align-items:flex-start;flex-direction:column}}
</style></head>
<body><div class="layout"><aside>
<div class="brand">Task<span>Flow</span></div>
<div class="nav active">▦ &nbsp; Overview</div><div class="nav">☑ &nbsp; My Tasks</div>
<div class="nav">◷ &nbsp; Activity</div><div class="nav">⚙ &nbsp; Settings</div>
<div class="small">DEVOPS PROJECT<br>Docker · Kubernetes<br>Prometheus · Grafana</div>
</aside><main>
<div class="top"><div><h1>Project overview</h1>
<p>Track your work and deployment progress.</p></div><span class="pill">● APPLICATION ONLINE</span></div>
<div class="cards">
<div class="card"><div class="label">Total tasks</div><div class="num" id="total">0</div></div>
<div class="card"><div class="label">Completed</div><div class="num blue" id="completed">0</div></div>
<div class="card"><div class="label">In progress</div><div class="num" id="pending">0</div></div>
</div>
<section class="panel"><h2>My tasks</h2><p>Manage your DevOps checklist.</p>
<form class="add" id="addform"><input id="title" maxlength="100" placeholder="Add a new task..." required>
<button type="submit">+ Add task</button></form><div id="tasks"></div></section>
<footer>TaskFlow DevOps demo · Health checks and Prometheus metrics enabled</footer>
</main></div>
<script>
async function api(url,options){const r=await fetch(url,options);if(!r.ok)throw Error("Request failed");return r.json()}
async function refresh(){const data=await api("/api/tasks");const list=document.getElementById("tasks");
document.getElementById("total").textContent=data.length;
document.getElementById("completed").textContent=data.filter(t=>t.done).length;
document.getElementById("pending").textContent=data.filter(t=>!t.done).length;
list.replaceChildren();
for(const t of data){const row=document.createElement("div");row.className="task";
const title=document.createElement("span");title.className="task-title"+(t.done?" done":"");title.textContent=t.title;
const actions=document.createElement("div");actions.className="actions";
const toggle=document.createElement("button");toggle.className="secondary";toggle.textContent=t.done?"Reopen":"Complete";
toggle.onclick=async()=>{await api("/api/toggle?id="+t.id,{method:"POST"});refresh()};
const del=document.createElement("button");del.className="delete";del.textContent="Delete";
del.onclick=async()=>{await api("/api/delete?id="+t.id,{method:"POST"});refresh()};
actions.append(toggle,del);row.append(title,actions);list.append(row)}}
document.getElementById("addform").onsubmit=async e=>{e.preventDefault();const input=document.getElementById("title");
await api("/api/add",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"title="+encodeURIComponent(input.value)});
input.value="";refresh()};
refresh().catch(()=>document.getElementById("tasks").textContent="Could not load tasks. Refresh the page.");
</script></body></html>"""

class App(BaseHTTPRequestHandler):
    def respond(self, status, body, content_type="application/json"):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        global requests_total
        path = urlparse(self.path).path
        if path != "/metrics":
            with lock:
                requests_total += 1
        if path == "/metrics":
            with lock:
                count = requests_total
            return self.respond(200,
                "# HELP cie_app_up Whether the CIE app is running\n"
                "# TYPE cie_app_up gauge\ncie_app_up 1\n"
                "# HELP cie_app_requests_total Total HTTP requests\n"
                "# TYPE cie_app_requests_total counter\n"
                f"cie_app_requests_total {count}\n",
                "text/plain; version=0.0.4; charset=utf-8")
        if path == "/health":
            return self.respond(200, "OK", "text/plain; charset=utf-8")
        if path == "/api/tasks":
            with lock:
                data = json.dumps(tasks)
            return self.respond(200, data)
        if path == "/":
            return self.respond(200, PAGE, "text/html; charset=utf-8")
        return self.respond(404, json.dumps({"error": "Not found"}))

    def do_POST(self):
        global next_id
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        with lock:
            if parsed.path == "/api/add":
                length = int(self.headers.get("Content-Length", "0"))
                form = parse_qs(self.rfile.read(length).decode("utf-8"))
                title = form.get("title", [""])[0].strip()[:100]
                if not title:
                    return self.respond(400, json.dumps({"error": "Task title required"}))
                tasks.append({"id": next_id, "title": title, "done": False})
                next_id += 1
            elif parsed.path == "/api/toggle":
                try:
                    task_id = int(query.get("id", ["0"])[0])
                except ValueError:
                    task_id = 0
                for task in tasks:
                    if task["id"] == task_id:
                        task["done"] = not task["done"]
                        break
            elif parsed.path == "/api/delete":
                try:
                    task_id = int(query.get("id", ["0"])[0])
                except ValueError:
                    task_id = 0
                tasks[:] = [t for t in tasks if t["id"] != task_id]
            else:
                return self.respond(404, json.dumps({"error": "Not found"}))
        return self.respond(200, json.dumps({"ok": True}))

    def log_message(self, fmt, *args):
        pass

HTTPServer(("0.0.0.0", 8080), App).serve_forever()
