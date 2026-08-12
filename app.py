import os
import threading
import http.server
import socketserver
import webview

PORT = 8765
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    def log_message(self, format, *args):
        pass # Suppress server logs

def start_server():
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()

def main():
    # Start local HTTP server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Create native desktop window
    url = f"http://127.0.0.1:{PORT}/index.html"
    window = webview.create_window(
        'QueueCraft Enterprise Simulation Studio',
        url,
        width=1366,
        height=850,
        resizable=True,
        min_width=900,
        min_height=650
    )
    webview.start()

if __name__ == '__main__':
    main()
