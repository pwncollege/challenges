JavaScript can do many things in the context of the web page, and can, thus, lead to unexpected situations and security compromises.
You'll explore some of these situations in the Web Security module, but we'll lay the groundwork here.

In this level, `/challenge/client` will no longer print the web page, and `/challenge/server` will not serve up an HTML page of the flag, but a JavaScript script that sets a global `flag` variable to the value of the flag.
You'll need to make a web page to _include_ this script in your page (we'll leave it up to you to find the documentation for this --- hint: `src` is involved) and then create another script to somehow _exfiltrate_ this information.
Exfiltration is the art of smuggling sensitive data out right under the nose of its owners: in this case, `/challenge/client` and `/challenge/server`.
Your JavaScript running on your page, of course, has acess to the `flag` variable, but you'll need to somehow communicate it out to the world.
This can be done in a few different ways, but probably the easiest is to redirect (using your `window.location` trick from before!) the client browser to a URL that contains the flag (similar to how the client leaked it to you a few levels ago), and have that request go to somewhere where you can see the URL log (such as the log of `/challenge/server` or your own webserver!).

This sounds like a lot, but it's eminently doable.
Our reference HTML solution file is just 150 bytes long!
As before, remember: you can debug your solutions using your own browser (and can run it as root in practice mode to be able to include the flag script!).
