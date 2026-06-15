"""Browser-based web UI for mUtils."""

import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from . import mdiffer
from . import mremover
from . import mrenamer
from . import msymlinker

CONFIRM_TOKEN = 'CONFIRM'


STYLE = """
body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 0;
  background: #f6f7f9;
  color: #1f2937;
}
header {
  background: #1f2937;
  color: white;
  padding: 16px 24px;
}
main {
  max-width: 1120px;
  margin: 0 auto;
  padding: 20px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
section, .result {
  background: white;
  border: 1px solid #d8dee8;
  border-radius: 6px;
  padding: 16px;
}
label {
  display: block;
  margin: 10px 0 4px;
  font-weight: 600;
}
input, select {
  box-sizing: border-box;
  width: 100%;
  padding: 8px;
  border: 1px solid #b8c0cc;
  border-radius: 4px;
}
button {
  margin-top: 12px;
  padding: 9px 12px;
  border: 0;
  border-radius: 4px;
  background: #2563eb;
  color: white;
  font-weight: 700;
  cursor: pointer;
}
pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #f3f4f6;
  border-radius: 4px;
  padding: 12px;
}
.danger {
  color: #991b1b;
}
"""


def _field(form, name, default=''):
    """Return one stripped form value."""
    return form.get(name, [default])[0].strip()


def _checked(form, name):
    """Return whether a checkbox-like value is set."""
    return _field(form, name).lower() in ('1', 'true', 'yes', 'on')


def _html_page(result_title='', result_text=''):
    """Render the main web UI page."""
    result_html = ''
    if result_title or result_text:
        result_html = """
        <div class="result">
          <h2>{}</h2>
          <pre>{}</pre>
        </div>
        """.format(html.escape(result_title), html.escape(result_text))

    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>mUtils Web UI</title>
  <style>{style}</style>
</head>
<body>
  <header>
    <h1>mUtils Web UI</h1>
  </header>
  <main>
    {result}
    <div class="grid">
      <section>
        <h2>mdiffer</h2>
        <form method="post" action="/run">
          <input type="hidden" name="tool" value="mdiffer">
          <label>Primary directory</label>
          <input name="primary_dir">
          <label>Secondary directory</label>
          <input name="secondary_dir">
          <label>Output directory</label>
          <input name="output_dir">
          <label>Log directory</label>
          <input name="log_dir">
          <label><input type="checkbox" name="case_sensitive"> Case-sensitive</label>
          <label><input type="checkbox" name="overwrite"> Overwrite output files</label>
          <button type="submit">Find duplicates</button>
        </form>
      </section>
      <section>
        <h2>mremover</h2>
        <form method="post" action="/run">
          <input type="hidden" name="tool" value="mremover">
          <label>Source directory</label>
          <input name="source">
          <label>Extension</label>
          <input name="extension" value=".nfo">
          <label>Exclude paths (CSV)</label>
          <input name="exclude">
          <label>Action</label>
          <select name="mode">
            <option value="preview">Preview only</option>
            <option value="delete">Delete files</option>
          </select>
          <label class="danger">Type CONFIRM to delete</label>
          <input name="confirm">
          <button type="submit">Run remover</button>
        </form>
      </section>
      <section>
        <h2>mrenamer</h2>
        <form method="post" action="/run">
          <input type="hidden" name="tool" value="mrenamer">
          <label>Source directory</label>
          <input name="source">
          <label>Action</label>
          <select name="mode">
            <option value="preview">Preview only</option>
            <option value="rename">Rename files</option>
          </select>
          <label class="danger">Type CONFIRM to rename</label>
          <input name="confirm">
          <button type="submit">Run renamer</button>
        </form>
      </section>
      <section>
        <h2>msymlinker</h2>
        <form method="post" action="/run">
          <input type="hidden" name="tool" value="msymlinker">
          <label>Source directory</label>
          <input name="source">
          <label>Original name</label>
          <input name="old_name">
          <label>Destination directory</label>
          <input name="dest_dir">
          <label>Symlink name</label>
          <input name="new_name">
          <button type="submit">Create symlink</button>
        </form>
      </section>
    </div>
  </main>
</body>
</html>""".format(style=STYLE, result=result_html)


def handle_tool(form):
    """Run one tool from parsed form data and return ``(title, result_text)``."""
    tool = _field(form, 'tool')

    if tool == 'mdiffer':
        output_dir = _field(form, 'output_dir') or mdiffer.OUTPUT_DIR
        log_dir = _field(form, 'log_dir') or mdiffer.LOG_DIR
        result = mdiffer.run_diff(
            _field(form, 'primary_dir'),
            _field(form, 'secondary_dir'),
            output_dir=output_dir,
            log_dir=log_dir,
            case_sensitive=_checked(form, 'case_sensitive'),
            overwrite=_checked(form, 'overwrite')
        )
        return 'mdiffer result', mdiffer.format_diff_result(result)

    if tool == 'mremover':
        delete_mode = _field(form, 'mode') == 'delete'
        if delete_mode and _field(form, 'confirm') != CONFIRM_TOKEN:
            return 'mremover blocked', 'Type CONFIRM to delete files.'
        result = mremover.remover(
            _field(form, 'source'),
            _field(form, 'extension'),
            dry_run=not delete_mode,
            exclude_paths=mremover.parse_exclude_paths(_field(form, 'exclude'))
        )
        return 'mremover result', mremover.format_remove_result(result)

    if tool == 'mrenamer':
        rename_mode = _field(form, 'mode') == 'rename'
        if rename_mode and _field(form, 'confirm') != CONFIRM_TOKEN:
            return 'mrenamer blocked', 'Type CONFIRM to rename files.'
        result = mrenamer.renamer(
            _field(form, 'source'),
            dry_run=not rename_mode
        )
        return 'mrenamer result', mrenamer.format_rename_result(result)

    if tool == 'msymlinker':
        result = msymlinker.linker(
            _field(form, 'source'),
            _field(form, 'old_name'),
            _field(form, 'dest_dir'),
            _field(form, 'new_name')
        )
        return 'msymlinker result', msymlinker.format_link_result(result)

    return 'Unknown tool', 'No supported tool was selected.'


class MUtilsWebHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the mUtils web UI."""

    def _send_html(self, body, status=200):
        encoded = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        """Render the main page."""
        if self.path not in ('/', '/index.html'):
            self._send_html(_html_page('Not found', 'Unknown route.'), status=404)
            return
        self._send_html(_html_page())

    def do_POST(self):
        """Run a tool and render the result."""
        if self.path != '/run':
            self._send_html(_html_page('Not found', 'Unknown route.'), status=404)
            return

        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length).decode('utf-8')
        form = parse_qs(raw, keep_blank_values=True)
        try:
            title, result = handle_tool(form)
        except Exception as exc:
            title, result = 'Error', str(exc)
        self._send_html(_html_page(title, result))

    def log_message(self, format, *args):
        """Silence default request logging."""
        return


def create_server(host='127.0.0.1', port=8000):
    """Create a web UI server instance."""
    return ThreadingHTTPServer((host, port), MUtilsWebHandler)


def _build_parser():
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description='Run the mUtils web UI.')
    parser.add_argument('--host', default='127.0.0.1', help='bind host')
    parser.add_argument('--port', type=int, default=8000, help='bind port')
    return parser


def main(argv=None):
    """Entry point for the mwui web UI command."""
    args = _build_parser().parse_args(argv)
    server = create_server(args.host, args.port)
    print('Serving mUtils Web UI at http://{}:{}/'.format(args.host, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
