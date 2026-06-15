import http.client
import threading
from urllib.parse import urlencode

from mutils import web


def test_handle_tool_blocks_delete_without_confirmation():
    title, result = web.handle_tool({
        'tool': ['mremover'],
        'mode': ['delete'],
        'confirm': [''],
    })

    assert title == 'mremover blocked'
    assert 'CONFIRM' in result


def test_handle_tool_blocks_rename_without_confirmation():
    title, result = web.handle_tool({
        'tool': ['mrenamer'],
        'mode': ['rename'],
        'confirm': [''],
    })

    assert title == 'mrenamer blocked'
    assert 'CONFIRM' in result


def test_handle_tool_remover_defaults_to_dry_run(tmp_path):
    target = tmp_path / 'remove.nfo'
    target.write_text('data')

    title, result = web.handle_tool({
        'tool': ['mremover'],
        'source': [str(tmp_path)],
        'extension': ['.nfo'],
        'mode': ['preview'],
    })

    assert title == 'mremover result'
    assert 'Would remove file(s): 1' in result
    assert target.exists()


def test_http_get_renders_main_page():
    server = web.create_server('127.0.0.1', 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection(
            server.server_address[0],
            server.server_address[1],
            timeout=5
        )
        conn.request('GET', '/')
        response = conn.getresponse()
        body = response.read().decode('utf-8')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 200
    assert 'mUtils Web UI' in body
    assert 'mdiffer' in body


def test_http_post_blocks_destructive_remove_without_confirmation(tmp_path):
    target = tmp_path / 'remove.nfo'
    target.write_text('data')
    server = web.create_server('127.0.0.1', 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = urlencode({
            'tool': 'mremover',
            'source': str(tmp_path),
            'extension': '.nfo',
            'mode': 'delete',
            'confirm': '',
        })
        conn = http.client.HTTPConnection(
            server.server_address[0],
            server.server_address[1],
            timeout=5
        )
        conn.request(
            'POST',
            '/run',
            body=payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response = conn.getresponse()
        body = response.read().decode('utf-8')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 200
    assert 'mremover blocked' in body
    assert target.exists()
