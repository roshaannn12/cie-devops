from http.server import BaseHTTPRequestHandler, HTTPServer

class App(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>DevOps CIE App Running!</h1><p>Docker + Kubernetes</p>")

HTTPServer(("0.0.0.0", 8080), App).serve_forever()
