Okay, so injecting some HTML was pretty cool!
You can imagine how this can be used to confuse victims, but it gets worse...

In the 1990s, the wise designers of the web invented JavaScript to make websites more interactive.
JavaScript lives alongside your HTML, and makes things interesting.
For example, this turns your browser into a clock:

```html
<html>
  <body>
    <script>
      document.body.innerHTML = Date();
    </script>
  </body>
</html>
```

Basically, the HTML `<script>` tag tells the browser that what is inside that tag is JavaScript, and the browser executes it.
I'm sure you can see where this is going...

In the previous level, you injected HTML.
In this one, you must use the exact same Stored XSS vulnerability to execute some JavaScript in the victim's browser.
Specifically, we want you to execute the JavaScript `alert("PWNED")` to pop up an alert that informs the victim that they've been pwned.
The _how_ of this level is the exact same as the previous one; only the _what_ changes, and suddenly, you're cooking with gas!

----
**DEBUGGING:**
Here, we need a slightly more advanced approach to debugging.
Two main things can go wrong here.

1. First, you might not be injecting your `<script>` tag properly.
   You should check this similar to the debugging path of the previous challenge: bring it up in Firefox and View Source or Inspect Element to make sure it looks correct.
2. Second, your actual JavaScript might be buggy.
   JavaScript errors will show up on your Firefox console.
   Pull up the web development console in the DOJO's Firefox, load the page, and see if anything has gone wrong!
   If it hasn't, consider resorting to print-debugging inside JavaScript (you can print to the console with, e.g., `console.log("wtf")`.
