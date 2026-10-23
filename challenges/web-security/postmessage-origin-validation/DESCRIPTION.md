Frames and windows from different origins cannot directly read each other's pages, so applications often use `postMessage()` to communicate across that boundary.
The receiving page must authenticate both the sender's exact origin and the window that sent the message before returning sensitive data.
A hostname-suffix check can mistake an attacker-controlled subdomain for the intended peer, and a permissive reply sends the result back across the boundary.
Build a page at `http://hacker.challenge.localhost:1337/` that talks to the administrator's dashboard, recover its token, and redeem it for the flag.
Run `/challenge/server`, start your web server, and run `/challenge/victim`.
