A nonce-based Content Security Policy authorizes trusted scripts while rejecting injected script elements and event handlers.
With `'strict-dynamic'`, that trust also follows scripts which an authorized script loads at runtime.
This is safe only when every trusted loader keeps attacker-controlled values away from its script source.
Find the loader gadget in the administrator's review page, make trusted code load your script, and exfiltrate the protected data.
Run `/challenge/server`, save your markup, start your web server, and run `/challenge/victim`.
