HTML sanitization is tied to the parse tree and context that the sanitizer inspected.
If an application later concatenates that output into a raw-text wrapper and parses it again, text that was harmless inside an attribute can acquire structural meaning.
This parse-sanitize-reparse gap is called mutation XSS.
Make the review system's markup-source preview mutate sanitized input into executable markup and exfiltrate the administrator's protected data.
Run `/challenge/server`, save your markup, start your listener, and run `/challenge/victim`.
