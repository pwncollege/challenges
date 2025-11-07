You've used XSS to inject JavaScript to cause the victim to make HTTP requests.
But what if there is no XSS?
Can you just "inject" the HTTP requests directly?

Shockingly, the answer is yes.
The web was designed to enable interconnectivity across many different websites.
Sites can embed images from other sites, link to other sites, and even _redirect_ to other sites.
All of this flexibility represents some serious security risks, and there is almost nothing preventing a malicious website from simply directly causing a victim visitor to make potentially sensitive requests, such as (in our case) a `GET` request to `http://challenge.localhost/publish`!

This style of _forging_ requests _across_ sites is called _Cross Site Request Forgery_, or CSRF for short.

Note that I said _almost_ nothing prevents this.
The [Same-origin Policy](https://en.wikipedia.org/wiki/Same-origin_policy) was created in the 1990s, when the web was still young, to (try to) mitigate this problem.
SOP prevents a site at one Origin (say, `http://www.hacker.com` or, in our case, `http://hacker.localhost:1337`) from interacting in certain security-critical ways with sites at other Origins (say, `http://www.asu.edu` or, in our case, `http://challenge.localhost/`).
SOP prevents some common CSRF vectors (e.g., when using JavaScript to make a requests across Origins, cookies will not be sent!), but there are plenty of SOP-avoiding ways to, e.g., make `GET` requests with cookies intact (such as full-on redirects).

In this level, pwnpost has fixed its XSS issues (at least for the `admin` user).
You'll need to use CSRF to publish the flag post!
The `/challenge/victim` of this level will log into pwnpost (`http://challenge.localhost/`) and will then visit an evil site that you can set up (`http://hacker.localhost:1337/`).
`hacker.localhost` points to your local workspace, but you will need to set up a web server to serve an HTTP request on port 1337 yourself.
Again, this can be done with `nc` or with a python server (for example, by using http.server or simply adapting the challenge server code itself!).
Because these sites will have different Origins, SOP protections will apply, so be careful about how you forge the request!
