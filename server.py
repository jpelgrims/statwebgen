import http.server
import socketserver
import threading
import signal
import json
import time
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

REFRESH_SCRIPT = ""
with open(os.path.join(SCRIPT_DIR, 'live_refresh.js'), 'r') as j:
    REFRESH_SCRIPT = '<script>' + j.read() + '</script>'


class LiveRefreshHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        # Endpoint for checking if live refresh is required
        if self.path == '/_refresh':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            refresh_required = self.server.wait()

            message = json.dumps({"refresh": refresh_required}).encode("utf-8")
            self.wfile.write(message)

            self.server.refresh_required = False

    def end_headers(self):
        # Allow CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


class LiveRefreshServer(socketserver.TCPServer):

    def __init__(self, server_address):
        self.refresh_required = False
        self.refresh_event = threading.Event()
        self.refresh_event.clear()
        self.lock = threading.Lock()
        self.allow_reuse_address = True
        
        super().__init__(server_address, LiveRefreshHandler)

    def serve_forever(self):
        super().serve_forever()
    
    def shutdown(self):
        print("Shutting down live refresh server...")
        self.socket.shutdown(1)
        self.socket.close()
        sys.exit(0)

    def wait(self):
        if self.refresh_required:
            return True
        self.refresh_event.wait(timeout=60*9)
        return self.refresh_required

    def notify(self):
        with self.lock:
            self.refresh_required = True
            self.refresh_event.set()
            self.refresh_event.clear()


class StaticWebsiteHandler(http.server.SimpleHTTPRequestHandler):

    def modify_header(self, keyword, value):
        for i in range(len(self._headers_buffer)):
            item = self._headers_buffer[i]
            if keyword.encode('utf-8') in item:
                 del self._headers_buffer[i]
                 self.send_header(keyword, value)
                 break

    def end_headers(self):
        path = self.translate_path(self.path)

        if self.guess_type(path) == "text/html":

            f = open(path, 'rb')
            fs = os.fstat(f.fileno())

            # Set correct Content-length (file length + length of refresh script)
            self.modify_header("Content-Length", str(fs[6] + len(REFRESH_SCRIPT)))
        super().end_headers()


    def do_GET(self):
        f = self.send_head()
        if f:
            try:
                if f.name.endswith(".html"):
                    lines = f.readlines()

                    for line in lines:
                        # Insert live-refresh script in head
                        if b"</head>" in line:
                            self.wfile.write(REFRESH_SCRIPT.encode('utf-8'))

                        self.wfile.write(line)
                else:
                    self.copyfile(f, self.wfile)
            finally:
                f.close()

    def translate_path(self,path):
        root = os.getcwd()
        #path = path.replace("/", "\\")

        if path[-1] != "/" and not "." in path[-5:]:
            return root + path + ".html"
        else:
            return root + path


class StaticWebsiteServer(socketserver.TCPServer):

    def __init__(self, server_address, directory):
        os.chdir(directory) 
        super().__init__(server_address, StaticWebsiteHandler)
    
    def shutdown(self):
        print("Shutting down website server...")
        super().shutdown()