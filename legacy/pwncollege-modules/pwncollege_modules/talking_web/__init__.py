import contextlib
import pwnshop
import urllib
import os

ENDPOINT_NAMES_CHALLENGE = [
    "access", "verify", "submit", "solve", "complete",
    "challenge", "request", "qualify", "validate", "entry",
    "check", "meet", "gateway", "pass", "fulfill",
    "authenticate", "task", "submission", "trial", "evaluate",
    "attempt", "progress", "gate", "mission",
    "hack", "pwn",
]

GET_PARAMETER_SECRET_PASSWORD = [
    "password", "pass", "secret", "key", "token",
    "auth", "credential", "access", "secret_key", "auth_key",
    "security", "hash", "signature", "auth_token", "code",
    "pin", "keycode", "authcode", "security_token", "login_key",
    "private_key", "challenge_key", "flag", "solution", "unlock",
    "verify", "access_code", "auth_pass", "secure_key", "unlock_code"
]

HACKING_FQDNS = [
    "root-me.org", "pwn.college", "picoctf.com", "www.w3challs.com", "wechall.net", "archive.ooo", "ctflearn.com", "dreamhack.io", "flagyard.com", "net-force.nl", "pwnable.kr", "www.thisislegal.com", "pwnable.tw", "overthewire.org", "reversing.kr", "crackmy.app", "gandalf.lakera.ai", "gpa.43z.one", "redarena.ai", "challs.reyammer.io", "alf.nu", "websec.fr", "0xf.at", "webhacking.kr", "www.xssgame.com", "xss.pwnfunction.com", "dojo-yeswehack.com", "cryptohack.org", "id0-rsa.pub", "cryptopals.com", "mysterytwister.org", "flaws.cloud", "flaws2.cloud", "ae27ff.com", "sadservers.com", "pydefis.callicode.fr", "wargame.nexus"
]

ALL_CLIENTS = [ "nc", "python3", "curl" ]

class TalkingWeb(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "talking-web.py"
    flask_host = None
    host_override = "challenge.localhost"
    flask_port = 80

    methods = [ "GET" ]
    endpoint_name = ""
    randomize_host = False
    randomize_endpoint = True
    words_in_endpoint = 1
    randomize_flag_location = False
    allowed_clients = [ ]
    useragent_substr = ""
    flag_in_html = True
    flag_in_header = False
    commented_flag = False
    num_get_params = 0
    num_post_params = 0
    index_form = False
    redirects = 0
    allowed_username = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_parameters = { }
        self.post_parameters = { }
        self.allowed_clients = list(self.allowed_clients)
        self.methods = list(self.methods)

        assert set(self.allowed_clients) <= set(ALL_CLIENTS)

        if self.randomize_host:
            self.flask_host = self.random.choice(HACKING_FQDNS)
        if self.randomize_endpoint:
            self.endpoint_name = " ".join(self.random.sample(ENDPOINT_NAMES_CHALLENGE, self.words_in_endpoint))
        if self.randomize_flag_location:
            self.flag_in_html, self.commented_flag, self.flag_in_header = self.random.choice([
                (True, False, False),
                (True, True, False),
                (False, False, True)
            ])
        if self.num_get_params:
            for k in self.random.sample(GET_PARAMETER_SECRET_PASSWORD, self.num_get_params):
                self.get_parameters[k] = self.random_word(8)
        if self.num_post_params:
            for k in self.random.sample(GET_PARAMETER_SECRET_PASSWORD, self.num_post_params):
                self.post_parameters[k] = self.random_word(8)

    @contextlib.contextmanager
    def run_challenge(self, **kwargs):
        with super().run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            try:
                yield process
            except Exception:
                print(process.clean().decode())
                raise

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            for client in ALL_CLIENTS:
                try:
                    getattr(self, "do_"+client)()
                    if client not in (self.allowed_clients or ALL_CLIENTS):
                        assert False
                except AssertionError:
                    if client in (self.allowed_clients or ALL_CLIENTS):
                        raise

    @property
    def query_string(self):
        if self.get_parameters:
            return "?" + "&".join(f"{urllib.request.quote(k)}={urllib.request.quote(v)}" for k,v in self.get_parameters.items())
        else:
            return ""

    @property
    def post_body(self):
        return "&".join(f"{urllib.request.quote(k)}={urllib.request.quote(v)}" for k,v in self.post_parameters.items())

    def do_nc(self):
        endpoint = self.endpoint_name
        if self.redirects:
            with self.run_sh([ "nc", self.host_override, str(self.flask_port) ], alarm=2) as r:
                r.sendline(f"GET / HTTP/1.1\nHost: {self.flask_host or 'localhost'}:80\nUser-Agent: netcat-{self.useragent_substr}\n\n")
                potential_endpoints = [w for w in r.readall().split() if w.endswith(self.endpoint_name.encode())]
                assert potential_endpoints
                endpoint = potential_endpoints[0]

        with self.run_sh([ "nc", self.host_override, str(self.flask_port) ], alarm=2) as r:
            post_data = ""
            req = "GET"
            if self.post_parameters:
                post_data = f"\nContent-Type: application/x-www-form-urlencoded\nContent-Length: {len(self.post_body)}\n\n{self.post_body}"
                req = "POST"

            r.sendline(f"{req} /{urllib.request.quote(endpoint)}{self.query_string} HTTP/1.1\nHost: {self.flask_host or 'localhost'}:80\nUser-Agent: netcat-{self.useragent_substr}{post_data}\n\n")
            assert self.flag in r.readall()

    def do_curl(self):
        post_opts = [ ]
        for k,v in self.post_parameters.items():
            post_opts += [ "-d", f"{k}={v}" ]
        endpoint = "" if self.redirects else f"{urllib.request.quote(self.endpoint_name)}{self.query_string}"
        with self.run_sh([
            "curl", "-v", "-L",
            "-H", f"Host: {self.flask_host or 'localhost'}",
            "-H", f"User-Agent: curl-{self.useragent_substr}",
            f"http://{self.host_override}:{self.flask_port}/{endpoint}",
            *post_opts
        ], alarm=5) as r:
            assert self.flag in r.readall()

    def do_python3(self):
        with self.run_sh(["python3", "-i"], alarm=5) as r:
            r.sendline("import requests")
            headers = { "User-Agent": f"requests-{self.useragent_substr}", "Host": self.flask_host or 'localhost' }
            post_data = f", data={self.post_parameters}" if self.post_parameters else ""
            req = "post" if post_data else "get"
            endpoint = "" if self.redirects else f"{urllib.request.quote(self.endpoint_name)}{self.query_string}"
            r.sendline(f"""r = requests.{req}("http://{self.host_override}:{self.flask_port}/{endpoint}", headers={headers}{post_data})""")
            r.sendline("print(r.text)")
            r.sendline("print(r.headers)")
            r.sendline("exit()")
            assert self.flag in r.readall()

    @property
    def endpoint_url(self):
        return f"http://{self.flask_host}:{self.flask_port}/{self.endpoint_name}"

class TalkingWebClient(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "base/selenium.py"
    specify_url = False
    flag_in_query = True
    port = 1337
    victim_url = "http://localhost:1337"
    epilogue = "Query sent! Go see if the flag is in your logs."

    def verify(self, **kwargs):
        with self.run_sh([ "nc", "-l", "-p", "1337" ], alarm=5) as server:
            with self.run_challenge(**kwargs, alarm=5):
                assert self.flag in server.readuntil("}")
            server.kill()

class TWRedirectClient(pwnshop.ChallengeGroup):
    challenges = { "server": TalkingWeb, "client": TalkingWebClient }
    challenge_names = [ "server", "client" ]
    BUILD_IMAGE = "pwncollege/challenge-legacy"
    VERIFY_IMAGE = "pwncollege/challenge-legacy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = self.challenge_instances["server"]
        self.client = self.challenge_instances["client"]

        self.client.flag_in_query = False
        self.client.print_page = True
        self.client.epilogue = " "
        self.server.allowed_username = "root"
        self.server.flask_host = "challenge.localhost"

    def verify(self, **kwargs):
        with self.server.run_challenge(**kwargs) as server:
            with self.run_sh([ "nc", "-l", "-p", "1337" ], alarm=5) as evil_server:
                evil_server.write(f"HTTP/1.1 301 Moved Permanently\nLocation: http://challenge.localhost:80/{self.server.endpoint_name}\n\n")
                with self.client.run_challenge(**kwargs) as client:
                    assert self.flag in client.readall()
            server.kill()

class TWRedirectJS(TWRedirectClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.flag_in_query = False
        self.client.print_page = True
        self.client.ensure_html = True
        self.client.epilogue = " "
        self.client.port = 80
        self.client.victim_url = "http://challenge.localhost:80/~hacker/solve.html"
        self.server.allowed_username = "root"
        self.server.public_html = True
        self.server.flask_host = "challenge.localhost"

    def verify(self, **kwargs):
        with self.run_sh("mkdir -p /home/hacker/public_html; cat > /home/hacker/public_html/solve.html <<END") as o:
            o.sendline(f"""<html><head><script>window.location = "http://challenge.localhost:80/{self.server.endpoint_name}"</script></head><body></body></html>""")
            o.sendline("END")

        with self.server.run_challenge(**kwargs) as server:
            with self.client.run_challenge(**kwargs) as client:
                assert self.flag in client.readall()
            server.kill()

class TWRemoteJS(TWRedirectClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.flag_in_query = False
        self.client.print_page = False
        self.client.port = 80
        self.client.victim_url = "http://challenge.localhost:80/~hacker/solve.html"
        self.server.allowed_username = "root"
        self.server.public_html = True
        self.server.flag_in_html = False
        self.server.flag_in_javascript = True
        self.server.flask_host = "challenge.localhost"

    def verify(self, **kwargs):
        with self.run_sh("mkdir -p /home/hacker/public_html; cat > /home/hacker/public_html/solve.html <<END") as o:
            o.sendline(f"""
              <html><head>
              <script src="{self.server.endpoint_url}"></script>
              <script>window.location = "http://challenge.localhost:80/"+flag</script>
              </head></html>
            """)
            o.sendline("END")

        with self.server.run_challenge(**kwargs) as server:
            with self.client.run_challenge(**kwargs) as client:
                client.wait()
            assert self.flag in server.clean()

class TWRemoteFetch(TWRedirectClient):
    num_get_params = 0
    num_post_params = 0
    methods = ["GET"]

    def __init__(self, *args, **kwargs):
        # insane hack
        self.challenges["server"].num_get_params = self.num_get_params
        self.challenges["server"].num_post_params = self.num_post_params
        self.challenges["server"].methods = self.methods
        super().__init__(*args, **kwargs)
        self.challenges["server"].num_get_params = 0
        self.challenges["server"].num_post_params = 0
        self.challenges["server"].methods = ["GET"]

        self.client.flag_in_query = False
        self.client.print_page = False
        self.client.port = 80
        self.client.victim_url = "http://challenge.localhost:80/~hacker/solve.html"
        self.server.allowed_username = "root"
        self.server.public_html = True
        self.server.flag_in_html = False
        self.server.flag_in_text = True
        self.server.flask_host = "challenge.localhost"

    def verify(self, **kwargs):
        with self.run_sh("mkdir -p /home/hacker/public_html; cat > /home/hacker/public_html/solve.html <<END") as o:
            post_args = ""
            if self.server.post_parameters:
                post_args = f""", {{ method: "POST", body: new URLSearchParams("{self.server.post_body}") }}"""

            o.sendline(f"""
              <html><head><script>
              fetch("{self.server.endpoint_url}{self.server.query_string}"{post_args}).then(response => response.text()).then(flag => window.location = "http://challenge.localhost:80/"+flag)
              </script></head></html>
            """)
            o.sendline("END")

        with self.server.run_challenge(**kwargs) as server:
            with self.client.run_challenge(**kwargs) as client:
                client.wait()
            assert self.flag in (server.clean() + server.clean())
