In the beginning of the web, HTML, though _Hyper_, was pretty static.
It described its layouts, and that was it.
Sometime in the 1990s, the movers and shakers of the internet thought "What if web pages could execute logic?", and JavaScript was born.

JavaScript is a programming language that allows web pages to dynamically make decisions and carry out actions.
It is, hands down (and unfortunately, because it's terrible) the most important programming language out there (though luckily not the most used), and try as we might to avoid it (did we mention that it's terrible), we have to account for it in any discussion of web security.

HTML specifies JavaScript to be executed through the `<script>` tag.
This tag tells the browser that what is inside that tag is JavaScript, and the browser executes it.
There are many resources online for how to write script tags, and how to write JavaScript, and we'll leave their finding as an exercise for you, the learner.
Here, we'll practice something very specific: using JavaScript to redirect the browser to a different web page.

As previously, the client browser will print out the page it receives, but it will start by going to `http://challenge.localhost/~hacker/solve.html`.
Here, we harken back to the olden days of shared servers: `http://challenge.localhost/~hacker/anything` will be served out of the `public_html` subdirectory of your home directory!
Create a `/home/hacker/public_html/solve.html`, write the JavaScript you need to redirect the browser, and get the flag!

----
**HINT:**
The JavaScript object you want is `window.location`.
You can assign a string to it to redirect the browser to a new location.

**HINT:**
Debugging this can be tricky with the built-in browser.
Try it using the dojo's Firefox!
You can't get the final flag with it, but you can at least tell if your redirect is working!
