# Flag Test Diff Review

This file groups the repeated diff shapes from the flag-capture migration so the review can focus on one representative per pattern.

## Pattern 1: direct string output -> regex match/assert/print

Representative shape:

```diff
-assert FLAG in output
-print(f"Exploit successful! Flag: {FLAG}")
+match = FLAG_RE.search(output)
+assert match, f"Flag not found in output: {output}"
+flag = match.group(0)
+print(f"Flag: {flag}")
```

Representative files:

- `challenges/web-security/auth-bypass-cookie/tests_private/test_exploit.py`
- `challenges/web-security/auth-bypass-param/tests_private/test_exploit.py`
- `challenges/web-security/csrf-get/tests_private/test_exploit.py`
- `challenges/web-security/csrf-post/tests_private/test_exploit.py`
- `challenges/web-security/csrf-reflected-alert/tests_private/test_exploit.py`
- `challenges/web-security/csrf-xss-cookie/tests_private/test_exploit.py`
- `challenges/web-security/csrf-xss-post/tests_private/test_exploit.py`
- `challenges/web-security/sqli-password/tests_private/test_exploit.py.j2`
- `challenges/web-security/sqli-pin/tests_private/test_exploit.py.j2`
- `challenges/web-security/sqli-tablename/tests_private/test_exploit.py.j2`
- `challenges/web-security/sqli-union/tests_private/test_exploit.py.j2`
- `challenges/web-security/xss-context/tests_private/test_exploit.py.j2`
- `challenges/web-security/xss-exfil-cookie/tests_private/test_exploit.py.j2`
- `challenges/web-security/xss-reflected/tests_private/test_exploit.py.j2`
- `challenges/web-security/xss-rf-get/tests_private/test_exploit.py.j2`
- `challenges/web-security/xss-rf-post/tests_private/test_exploit.py.j2`
- `challenges/web-security/xss-stored-alert/tests_private/test_exploit.py.j2`
- `challenges/web-security/xss-stored-html/tests_private/test_exploit.py.j2`
- `challenges/sql-playground/sql-query/tests_private/test_exploit.py.j2`
- `challenges/sql-playground/sql-where/tests_private/test_exploit.py.j2`
- `challenges/sql-playground/sql-where-one/tests_private/test_exploit.py.j2`
- `challenges/sql-playground/sql-where-one-random/tests_private/test_exploit.py.j2`
- `challenges/sql-playground/sql-where-one-string/tests_private/test_exploit.py.j2`
- `challenges/sql-playground/sql-where-substr/tests_private/test_exploit.py.j2`
- `challenges/sql-playground/sql-composite-conditions/tests_private/test_exploit.py.j2`
- `challenges/sql-playground/sql-limit/tests_private/test_exploit.py.j2`

## Pattern 2: bytes output -> regex match/assert/print

Representative shape:

```diff
-assert FLAG in output
+match = FLAG_RE.search(output)
+assert match, f"Flag not found in output: {output!r}"
+print(f"Flag: {match.group(0).decode()}")
```

Representative files:

- `challenges/web-security/path-traversal-1/tests_private/test_solve.py.j2`
- `challenges/web-security/path-traversal-2/tests_private/test_solve.py.j2`
- `challenges/shell-lin-do/first/10/tests_private/test_solve.py`
- `challenges/shell-lin-do/first/20/tests_private/test_solve.py`
- `challenges/shell-lin-do/first/30/tests_private/test_solve.py`
- `challenges/shell-lin-do/other/10/tests_private/test_solve.py`
- `challenges/shell-lin-do/other/20/tests_private/test_solve.py`
- `challenges/shell-lin-do/other/30/tests_private/test_solve.py`
- `challenges/shell-lin-do/other/41/tests_private/solve.py`
- `challenges/shell-lin-do/other/45/tests_private/test_solve.py`
- `challenges/shell-lin-do/unexpected-input/10/tests_private/test_solve.py`
- `challenges/shell-lin-do/unexpected-input/30/tests_private/test_solve.py`
- `challenges/shell-lin-do/unexpected-input/40/tests_private/test_solve.py`
- `challenges/shell-lin-do/unexpected-input/50/tests_private/test_solve.py`
- `challenges/shell-lin-do/unexpected-input/60/tests_private/test_solve.py`
- `challenges/shell-lin-do/unexpected-input/61/tests_private/test_solve.py`
- `challenges/shell-lin-do/unexpected-input/70/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/10/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/11/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/13/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/14/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/15/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/16/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/17/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/18/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/19/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/19-next/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/19-next-2/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/19-next-2b/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/19-next-3/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/20/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/23/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/25/tests_private/test_solve.py`
- `challenges/shell-lin-do/input-restrictions/30/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/2/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/10/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/15/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/16/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/18/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/19/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/20/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/21/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/22/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/23/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/24/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/24-1/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/25/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/30/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/40/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/40-1/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/41/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/42/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/42-1/tests_private/test_solve.py`
- `challenges/shell-lin-do/expansion/43/tests_private/test_solve.py`

## Pattern 3: straightforward Python solver outputs

These files now just do the regex directly on the already-built `output` variable, without extra helper wrappers:

- `challenges/legacy/fundamentals/data-dealings/*/tests_private/test_solve.py`
- `challenges/legacy/fundamentals/sql-playground/*/tests_private/test_solve.py`
- `challenges/legacy/fundamentals/talking-web/http-*.py`

Representative files:

- `challenges/legacy/fundamentals/data-dealings/password-simple-1/tests_private/test_solve.py`
- `challenges/legacy/fundamentals/sql-playground/sql-query/tests_private/test_solve.py`
- `challenges/legacy/fundamentals/talking-web/http-flask/tests_private/test_solve.py`
- `challenges/legacy/fundamentals/talking-web/http-host-nc/tests_private/test_solve.py`

## Pattern 4: capture-server tests

These needed the same regex snippet, but against either `captured_flag` or `client_output`:

- `challenges/legacy/fundamentals/talking-web/http-server/tests_private/test_solve.py`
- `challenges/legacy/fundamentals/talking-web/http-server-fetch/tests_private/test_solve.py`
- `challenges/legacy/fundamentals/talking-web/http-server-fetch-params/tests_private/test_solve.py`
- `challenges/legacy/fundamentals/talking-web/http-server-fetch-post/tests_private/test_solve.py`
- `challenges/legacy/fundamentals/talking-web/http-server-include-js/tests_private/test_solve.py`

## Pattern 5: special-case rewrites

These are the files worth reviewing individually because they are not just the repeated regex swap:

- `challenges/web-security/sqli-blind/tests_private/test_exploit.py.j2`
  - helper defs were flattened into one top-level blind extraction loop
- `challenges/sql-playground/sql-metadata/tests_private/test_exploit.py.j2`
  - changed to a single interactive session so the discovered table name and follow-up query use the same process
- `challenges/sql-playground/sql-substr/tests_private/test_exploit.py.j2`
  - fixed row parsing to read the returned value rather than the column name from the printed dict
- `challenges/shell-lin-do/expansion/4/tests_private/test_solve.py`
  - deterministic `/tmp` setup so one run surfaces the real flag and prints it
- `challenges/shell-lin-do/expansion/24-2/tests_private/test_solve.py`
  - replaced placeholder-prefix logic with a real pattern-based recovery loop over the flag alphabet

## Pattern 6: legacy-program-security helper removal

These files used the same extra helper layer:

```diff
-FLAG_CAPTURE_RE = re.compile(...)
-
-def _capture_flag(blob):
-    ...
-    return FLAG_CAPTURE_RE.search(blob)
-
-def _print_flag(blob):
-    match = _capture_flag(blob)
-    ...
-    print(f"Flag: {flag}")
-    return flag
+FLAG_RE = re.compile(...)
...
+match = FLAG_RE.search(output_or_bytes)
+assert match, f"Flag not found in output: ..."
+flag = match.group(0)
+print(f"Flag: {flag}")
```

Representative files:

- `challenges/legacy/program-security/program-security/recursive-ruin-easy/tests_private/test_solve.py`
- `challenges/legacy/program-security/program-security/bounds-breaker-easy/tests_private/test_solve.py`
- `challenges/legacy/program-security/program-security/loop-lunacy-hard/tests_private/test_solve.py`
- `challenges/legacy/program-security/reverse-engineering/level-1-0/tests_private/test_solve.py`
- `challenges/legacy/program-security/reverse-engineering/level-22-1/tests_private/test_solve.py`
- `challenges/legacy/program-security/reverse-engineering/salty-stampede/tests_private/test_solve.py`
- `challenges/legacy/program-security/return-oriented-programming/level-1-0/tests_private/test_solve.py`
- `challenges/legacy/program-security/return-oriented-programming/level-12-0/tests_private/test_solve.py`
