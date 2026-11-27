import http.client
import json
import os
import shutil
import socket
import ssl
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 20 * 1024 * 1024


class Backend(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        pass

    def respond(self, status, body=b"", headers=None):
        self.send_response(status)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/v1/auth/forward/":
            if self.server.fail_auth:
                self.respond(503)
            elif self.server.omit_identity:
                self.respond(200)
            elif self.headers.get("Cookie") == "sessionid=valid":
                self.respond(200, headers={
                    "X-Forwarded-User": "alice",
                    "X-Forwarded-Groups": "user|team-7",
                })
            else:
                target = self.headers.get("X-Forwarded-Uri", "/jenkins/")
                self.respond(302, headers={"Location": "/login?next=" + quote(target, safe="")})
        elif self.path.startswith("/api/v1/action-history/") or self.path.startswith("/api/v1/jenkins/jobs/"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(b"data: first\n\n")
            self.wfile.flush()
            time.sleep(int(self.headers.get("X-Test-Stream-Delay", "1")))
            self.wfile.write(b"data: second\n\n")
            self.wfile.flush()
            self.close_connection = True
        elif self.path.startswith("/jenkins"):
            body = json.dumps({
                "path": self.path,
                "user": self.headers.get("X-Forwarded-User"),
                "groups": self.headers.get("X-Forwarded-Groups"),
                "authorization": self.headers.get("Authorization"),
                "host": self.headers.get("Host"),
                "proto": self.headers.get("X-Forwarded-Proto"),
                "prefix": self.headers.get("X-Forwarded-Prefix"),
            }).encode()
            self.respond(200, body)
        else:
            self.respond(200, b"webapp")

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(size)
        self.respond(200, str(len(body)).encode())


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def proxy(tmp_path_factory):
    binary = os.environ.get("TRAEFIK_BINARY")
    if not binary:
        pytest.fail("Set TRAEFIK_BINARY to the pinned Traefik binary")

    root = tmp_path_factory.mktemp("traefik")
    cert = root / "certificate.crt"
    key = root / "certificate.key"
    subprocess.run([
        "openssl", "req", "-x509", "-nodes", "-newkey", "rsa:2048",
        "-keyout", str(key), "-out", str(cert), "-days", "1",
        "-subj", "/CN=nita-test",
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    backend = ThreadingHTTPServer(("127.0.0.1", 0), Backend)
    backend.fail_auth = False
    backend.omit_identity = False
    thread = threading.Thread(target=backend.serve_forever, daemon=True)
    thread.start()
    backend_url = f"http://127.0.0.1:{backend.server_port}"
    port, http_port = free_port(), free_port()
    while http_port == port:
        http_port = free_port()
    static = yaml.safe_load((ROOT / "traefik/traefik.yaml").read_text())
    static["entryPoints"]["web"]["address"] = f"127.0.0.1:{http_port}"
    static["entryPoints"]["websecure"]["address"] = f"127.0.0.1:{port}"
    static["providers"]["file"]["filename"] = str(root / "routes.yaml")
    dynamic_text = (ROOT / "traefik/routes.yaml").read_text()
    dynamic_text = dynamic_text.replace("http://webapp:8000", backend_url)
    dynamic_text = dynamic_text.replace("http://jenkins:8080", backend_url)
    dynamic_text = dynamic_text.replace("/etc/certificate/nginx-certificate.crt", str(cert))
    dynamic_text = dynamic_text.replace("/etc/certificate/nginx-certificate-key.key", str(key))
    (root / "traefik.yaml").write_text(yaml.safe_dump(static))
    (root / "routes.yaml").write_text(dynamic_text)
    for plugin in ("bodylimit", "identityguard"):
        plugin_dir = root / "plugins-local/src/github.com/Juniper/nita-webapp/traefik" / plugin
        shutil.copytree(ROOT / "traefik" / plugin, plugin_dir)

    with (root / "traefik.log").open("w+") as log:
        process = subprocess.Popen(
            [binary, "--configFile", str(root / "traefik.yaml")],
            cwd=root, stdout=log, stderr=subprocess.STDOUT,
            env={**os.environ, "TMPDIR": str(root)},
        )
        try:
            for _ in range(100):
                if process.poll() is not None:
                    break
                try:
                    conn = http.client.HTTPConnection("127.0.0.1", http_port, timeout=1)
                    conn.request("GET", "/")
                    response = conn.getresponse()
                    if response.status == 200 and response.read() == b"webapp":
                        conn.close()
                        break
                    conn.close()
                except OSError:
                    pass
                time.sleep(0.1)
            else:
                log.flush()
                pytest.fail(f"Traefik did not become ready: {(root / 'traefik.log').read_text()}")
            if process.poll() is not None:
                log.flush()
                pytest.fail(f"Traefik exited: {(root / 'traefik.log').read_text()}")
            yield {"port": port, "http_port": http_port, "cert": cert, "backend": backend}
        finally:
            process.terminate()
            process.wait(timeout=10)
            backend.shutdown()
            backend.server_close()
            thread.join(timeout=10)
            assert not list(root.glob("nita-proxy-body-*")), "request body temporary files leaked"


def request(proxy, method, path, headers=None, body=None, encode_chunked=False):
    conn = http.client.HTTPSConnection(
        "127.0.0.1", proxy["port"], timeout=10,
        context=ssl._create_unverified_context(),
    )
    conn.request(method, path, body=body, headers=headers or {}, encode_chunked=encode_chunked)
    return conn, conn.getresponse()


def test_routes_and_jenkins_identity(proxy):
    conn, response = request(proxy, "GET", "/")
    assert response.status == 200
    assert response.read() == b"webapp"
    conn.close()

    conn, response = request(proxy, "GET", "/jenkins/job/example/?x=1")
    assert response.status == 302
    assert response.getheader("Location") == "/login?next=%2Fjenkins%2Fjob%2Fexample%2F%3Fx%3D1"
    response.read()
    conn.close()

    conn, response = request(proxy, "GET", "/jenkins/job/example/", headers={
        "Cookie": "sessionid=valid",
        "Authorization": "Bearer attacker",
        "X-Forwarded-User": "admin",
        "X-Forwarded-Groups": "admin",
        "X-Forwarded-Proto": "http",
    })
    assert response.status == 200
    data = json.loads(response.read())
    assert data == {
        "path": "/jenkins/job/example/",
        "user": "alice",
        "groups": "user|team-7",
        "authorization": None,
        "host": f"127.0.0.1:{proxy['port']}",
        "proto": "https",
        "prefix": "/jenkins",
    }
    conn.close()


def test_jenkins_slash_redirect_preserves_port(proxy):
    conn, response = request(proxy, "GET", "/jenkins")
    assert response.status in (301, 302, 307, 308)
    assert response.getheader("Location") == f"https://127.0.0.1:{proxy['port']}/jenkins/"
    response.read()
    conn.close()


def test_jenkins_asset_keeps_prefix(proxy):
    path = "/jenkins/static/example/css/style.css"
    conn, response = request(proxy, "GET", path, headers={"Cookie": "sessionid=valid"})
    assert response.status == 200
    assert json.loads(response.read())["path"] == path
    conn.close()


def test_jenkins_auth_failure_is_closed(proxy):
    proxy["backend"].fail_auth = True
    try:
        conn, response = request(proxy, "GET", "/jenkins/", headers={"Cookie": "sessionid=valid"})
        assert response.status == 503
        response.read()
        conn.close()
    finally:
        proxy["backend"].fail_auth = False


def test_missing_identity_from_auth_is_closed(proxy):
    proxy["backend"].omit_identity = True
    try:
        conn, response = request(proxy, "GET", "/jenkins/", headers={
            "Cookie": "sessionid=valid",
            "X-Forwarded-User": "admin",
            "X-Forwarded-Groups": "admin",
        })
        assert response.status == 503
        response.read()
        conn.close()
    finally:
        proxy["backend"].omit_identity = False


@pytest.mark.parametrize("path", ["/", "/jenkins/"])
def test_body_limit_allows_exact_boundary(proxy, path):
    body = b"x" * MAX_BODY
    conn, response = request(proxy, "POST", path, headers={"Cookie": "sessionid=valid"}, body=body)
    assert response.status == 200
    assert response.read() == str(MAX_BODY).encode()
    conn.close()


@pytest.mark.parametrize("path", [
    "/", "/jenkins/", "/api/v1/action-history/1/stream/",
    "/api/v1/jenkins/jobs/job/1/stream/",
])
@pytest.mark.parametrize("chunked", [False, True])
def test_oversized_requests_rejected_before_backend(proxy, path, chunked):
    if chunked:
        body = iter([b"x" * (MAX_BODY + 1)])
        conn, response = request(proxy, "POST", path, body=body, encode_chunked=True)
    else:
        conn, response = request(proxy, "POST", path, headers={"Content-Length": str(MAX_BODY + 1)})
    assert response.status == 413
    response.read()
    conn.close()


@pytest.mark.parametrize("path", ["/api/v1/action-history/1/stream/", "/api/v1/jenkins/jobs/job/1/stream/"])
def test_sse_response_is_delivered_incrementally(proxy, path):
    started = time.monotonic()
    conn, response = request(proxy, "GET", path)
    assert response.status == 200
    assert response.readline() == b"data: first\n"
    assert time.monotonic() - started < 0.9
    assert response.readline() == b"\n"
    assert response.readline() == b"data: second\n"
    response.read()
    conn.close()


def test_certificate_is_presented_without_sni(proxy):
    expected = ssl.PEM_cert_to_DER_cert(proxy["cert"].read_text())
    context = ssl._create_unverified_context()
    with socket.create_connection(("127.0.0.1", proxy["port"]), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=None) as secure:
            assert secure.getpeercert(binary_form=True) == expected


@pytest.mark.parametrize("hostname", ["localhost", "127.0.0.1"])
def test_certificate_is_presented_with_sni(proxy, hostname):
    expected = ssl.PEM_cert_to_DER_cert(proxy["cert"].read_text())
    context = ssl._create_unverified_context()
    with socket.create_connection(("127.0.0.1", proxy["port"]), timeout=5) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as secure:
            assert secure.getpeercert(binary_form=True) == expected


@pytest.mark.skipif(
    os.environ.get("TRAEFIK_LONG_STREAM_TEST") != "1",
    reason="Set TRAEFIK_LONG_STREAM_TEST=1 to run the 1850-second idle check",
)
def test_sse_survives_1850_seconds_idle(proxy):
    def check_stream(path):
        conn = http.client.HTTPSConnection(
            "127.0.0.1", proxy["port"], timeout=1900,
            context=ssl._create_unverified_context(),
        )
        try:
            conn.request("GET", path, headers={"X-Test-Stream-Delay": "1850"})
            response = conn.getresponse()
            assert response.status == 200
            assert response.readline() == b"data: first\n"
            assert response.readline() == b"\n"
            started = time.monotonic()
            assert response.readline() == b"data: second\n"
            assert time.monotonic() - started >= 1849
            response.read()
        finally:
            conn.close()

    paths = [
        "/api/v1/action-history/1/stream/",
        "/api/v1/jenkins/jobs/job/1/stream/",
    ]
    with ThreadPoolExecutor(max_workers=len(paths)) as executor:
        list(executor.map(check_stream, paths))
