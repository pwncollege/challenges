# Templated service / web challenges

One of the four archetypes (see `SKILL.md` §7). Used by `web-security`, `sql-playground`,
and any challenge that runs a service the learner attacks over the network. **Always
extend a common template** — these provide the Flask app, privilege handling, flag
plumbing, and randomized names. Hand-rolling a server is the wrong move.

Read alongside: `challenges/common/{flask.py.j2,random_names.j2,victim-selenium.py.j2}`
and the per-module bases in `challenges/web-security/common/` (`cmdi.py.j2`,
`sqli-pw.py.j2`, `sqli-userquery.py.j2`, `path-traversal.py.j2`, `xss-stored.py.j2`,
`auth-bypass.py.j2`, `pwnpost-basic|full.py.j2`, `temporarydb.py.j2`,
`victim-requests.py.j2`, `init.j2`), plus `sql-playground/common/{sql.j2,random_names.j2}`.

## The template pattern

A challenge's `challenge/server.j2` (or similar) **extends** a base and sets vars in
`{% block setup %}` (calling `super()` to keep parent init), overriding only the blocks
that differ:

```jinja2
{%- extends "../../common/sqli-pw.py.j2" -%}
{% block setup %}
  {{- super() -}}
  {%- set challenge.pw_name = "pin" -%}
  {%- set challenge.guest_pw = 1337 -%}
  {%- set challenge.admin_pw_code = "random.randrange(2**32, 2**63)" -%}
{% endblock %}
```

- The `challenge` (a.k.a. `settings`) namespace carries config; `flask.py.j2` provides
  blocks like `setup`, `imports`, `handlers`, `initialization`, `run_host` and handles
  the `exec-suid` shebang, UID/PATH reset, secret key, and binding.
- Web apps set `app.config['SERVER_NAME'] = "challenge.localhost:80"` and run on port 80.

## Randomized names (legitimate, seeded)

Use the `random_names.j2` macro to randomize endpoint/parameter/table names so public
exploits can't hardcode them:

```jinja2
{%- from '../../common/random_names.j2' import generate_names -%}
{{- generate_names(challenge, random) -}}
```

This is seeded by `CHALLENGE_SEED`, so a build and its tests get **identical** names —
reproducible, not a solve-path coin flip (SKILL.md §2). Admin passwords / secret table
suffixes are similarly generated at template time; they're data, not control flow, so the
exploit technique is unchanged.

## Flag delivery

The flag lives at `/flag`; the app reads it and reveals it **only on successful
exploitation** — e.g. printed on admin login (sqli/auth-bypass), returned when injection
succeeds (cmdi/path-traversal), or exfiltrated by a victim (xss/csrf). Don't invent a
side channel.

## Victims (XSS/CSRF)

For challenges needing a "victim" to visit attacker content, reuse a victim template
rather than writing browser automation:
- `common/victim-selenium.py.j2` — drives a real browser (logs in, fills forms, checks
  alerts/cookie exfil).
- `web-security/common/victim-requests.py.j2` — plain `requests` victim for
  injection-detection.
Both run via `exec-suid` so they hold the privilege to read `/flag` after the exploit.

## Tests

`tests_public` launches the server and asserts functionality; `tests_private` proves the
exploit. Both render with the same seed to get matching names, poll for readiness, then
use `requests` (or `pwnlib.tubes`):

```python
{% from '../../../common/random_names.j2' import generate_names %}
{% set challenge = namespace() %}{{ generate_names(challenge, random) }}
proc = subprocess.Popen(['/challenge/server'])
for _ in range(100):
    try: requests.get("http://challenge.localhost/"); break
    except requests.RequestException: time.sleep(0.1)
else: raise AssertionError("server did not become ready in time")
# ... drive the endpoint, assert status/body, and for tests_private grep the flag ...
```

Run under `nix develop --command pwnshop test`.

## Pick the base

| Goal | Extend |
|---|---|
| SQL injection at a login/PIN | `web-security/common/sqli-pw.py.j2` |
| SQL injection in a user query (hidden table) | `web-security/common/sqli-userquery.py.j2` |
| Command injection (with filter/quote variants) | `web-security/common/cmdi.py.j2` |
| Path traversal / file serving | `web-security/common/path-traversal.py.j2` |
| Stored XSS / posting service | `web-security/common/xss-stored.py.j2` or `pwnpost-basic.py.j2` |
| Auth/session bypass | `web-security/common/auth-bypass.py.j2` |
| Full login+draft/publish (CSRF/XSS) | `web-security/common/pwnpost-full.py.j2` |
| Any other HTTP service | `common/flask.py.j2` |
| SQL playground / freeform SQL | `sql-playground/common/sql.j2` |
