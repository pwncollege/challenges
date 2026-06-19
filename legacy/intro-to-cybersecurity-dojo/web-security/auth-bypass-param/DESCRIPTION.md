Of course, web applications can have security vulnerabilities that have nothing to do with the shell.
A common type of vulnerability is an _Authentication Bypass_, where an attacker can bypass the typical authentication logic of an application and log in without knowing the necessary user credentials.

This level challenges you to explore one such scenario.
This specific scenario arises because, again, of a gap between what the developer expects (that the URL parameters set by the application will only be set by the application itself) and the reality (that attackers can craft HTTP requests to their hearts content).

This level assumes a passing familiarity with SQL, which you can develop in the [SQL Playground](/fundamentals/sql-playground).
SQL will become incredibly relevant later, but for now, it is an incidental part of the challenge.

Anyways, go and bypass this authentication to log in as the `admin` user and get the flag!
