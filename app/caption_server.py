"""
Servidor HTTP local para Browser Source do OBS.
Serve a pagina HTML de legendas e o endpoint /text com {text, version}.
"""

import threading
import http.server
import socketserver
import json as _json

# HTML servido ao OBS. Placeholders substituidos em runtime:
#   __FONT_SIZE__   tamanho da fonte em px
#   __TEXT_COLOR__  cor CSS do texto
#   __BG_RGBA__     cor CSS rgba do fundo
CAPTION_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body {
    background: transparent;
    width: 100%; height: 100vh;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    overflow: hidden;
  }
  #sub {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: __FONT_SIZE__px;
    font-weight: 700;
    color: __TEXT_COLOR__;
    background: __BG_RGBA__;
    padding: 10px 28px;
    border-radius: 8px;
    text-align: center;
    text-shadow: 2px 2px 6px rgba(0,0,0,0.9), 0 0 12px rgba(0,0,0,0.7);
    max-width: 92%;
    margin-bottom: 36px;
    transition: opacity 0.28s ease;
    word-wrap: break-word;
    line-height: 1.35;
  }
  #sub.fade { opacity: 0; }
</style>
</head>
<body>
<div id="sub">\u00a0</div>
<script>
  var lastVer = -1, el = document.getElementById('sub');
  function poll() {
    fetch('/text')
      .then(function(r){ return r.json(); })
      .then(function(d){
        if (d.version !== lastVer) {
          lastVer = d.version;
          el.classList.add('fade');
          setTimeout(function(){
            el.textContent = d.text || '\u00a0';
            el.classList.remove('fade');
          }, 260);
        }
      })
      .catch(function(){})
      .finally(function(){ setTimeout(poll, 500); });
  }
  poll();
</script>
</body>
</html>"""


class CaptionServer:
    """
    Parametros:
        port         : porta TCP (ex: 5050)
        get_state_fn : callable() -> {"text": str, "version": int}
        html_content : string HTML ja com placeholders substituidos
    """

    def __init__(self, port: int, get_state_fn, html_content: str):
        self.port        = port
        self._get_state  = get_state_fn
        self._html_bytes = html_content.encode("utf-8")
        self._server     = None

    def start(self) -> bool:
        """Inicia o servidor em thread daemon. Retorna False se a porta estiver ocupada."""
        get_state  = self._get_state
        html_bytes = self._html_bytes

        class _Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/text":
                    body = _json.dumps(get_state()).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif self.path in ("/", "/index.html"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(html_bytes)))
                    self.end_headers()
                    self.wfile.write(html_bytes)
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *a):
                pass

        class _TCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        try:
            self._server = _TCPServer(("", self.port), _Handler)
            threading.Thread(target=self._server.serve_forever, daemon=True).start()
            return True
        except OSError:
            return False

    def stop(self) -> None:
        if self._server:
            threading.Thread(target=self._server.shutdown, daemon=True).start()
            self._server = None
