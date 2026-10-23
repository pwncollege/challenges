An `HttpOnly` session cookie cannot be read through `document.cookie`.
The browser still attaches that cookie to same-origin requests made by injected JavaScript, and the script can read the responses to those requests.
Use the administrator's browser to retrieve protected data and exfiltrate it to a server you control.
Run `/challenge/server`, save your payload, start your listener, and run `/challenge/victim`.
