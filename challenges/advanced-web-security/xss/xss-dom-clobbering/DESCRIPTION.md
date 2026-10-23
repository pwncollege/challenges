HTML elements with certain `id` and `name` values become named properties on the page's global object.
Legacy compatibility makes that behavior useful to ordinary pages, but it also means injected markup can replace values that trusted JavaScript expects to be plain configuration objects.
When that script uses the resulting property in a security-sensitive operation, markup alone can redirect its behavior without injecting a new script.
Use that behavior to steer the administrator page's trusted code, recover its token, and redeem it for the flag.
Run `/challenge/server`, save your markup, start your listener, and run `/challenge/victim`.
