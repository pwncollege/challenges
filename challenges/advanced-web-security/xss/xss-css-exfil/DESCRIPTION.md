Blocking JavaScript does not make attacker-controlled CSS inert.
CSS attribute selectors can test secrets already present in the DOM, while a matching rule can trigger an outbound request through `url()`.
Repeated guesses turn those conditional requests into an oracle that reveals the secret one piece at a time.
Recover the administrator's token without JavaScript, redeem it, and get the flag.
Run `/challenge/server`, save your CSS, start your listener, and run `/challenge/victim`.
