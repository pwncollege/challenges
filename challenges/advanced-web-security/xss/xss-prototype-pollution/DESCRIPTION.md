Every ordinary JavaScript object inherits properties from `Object.prototype` unless the application deliberately chooses otherwise.
An unsafe recursive merge can follow special keys into that shared prototype, making an attacker-controlled value appear on unrelated objects later in the page.
When one of those inherited values reaches an HTML sink, prototype pollution becomes DOM XSS.
Turn the unsafe merge into code execution in the administrator's origin and exfiltrate the protected data.
Run `/challenge/server`, save your JSON, start your listener, and run `/challenge/victim`.
