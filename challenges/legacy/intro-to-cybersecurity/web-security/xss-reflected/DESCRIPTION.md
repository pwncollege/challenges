In the previous examples, your injection content was first stored in the database (as posts), and was triggered when the web server retrieved it from the database and sent it to the victim's browser.
Because the data has to be stored first and retrieved later, this is called a _Stored_ XSS.
However, the magic of HTTP GET requests and their URL parameters opens the door to another type of XSS: _Reflected_ XSS.

Reflected XSS happens when a URL parameter is rendered into a generated HTML page in a way that, again, allows the attacker to insert HTML/JavaScript/etc.
To carry out such an attack, an attacker typically needs to trick the victim into visiting a very specifically-crafted URL with the right URL parameters.
This is unlike a Stored XSS, where an attacker might be able to simply make a post in a vulnerable forum and wait for victims to stumble onto it.

Anyways, this level is a Reflected XSS vulnerability.
The `/challenge/victim` of this challenge takes a URL argument on the commandline, and it will visit that URL.
Fool the `/challenge/victim` into making a JavaScript `alert("PWNED")`, and you'll get the flag!
