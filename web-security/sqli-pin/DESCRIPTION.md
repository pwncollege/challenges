Of course, these sorts of security gaps abound!
For example, in this level, the specification of the logged in user is actually secure.
Instead of get parameters or raw cookies, this level uses an encrypted session cookie that you will not be able to mess with.
Thus, your task is to get the application to actually authenticate you as admin!

Luckily, as the name of the level suggests, this application is vulnerable to a _SQL injection_.
A SQL injection, conceptually, is to SQL what a Command Injection is to the shell.
In Command Injections, the application assembled a command string, and a gap between the developer's intent and the command shell's actual functionality enabled attackers to carry out actions unintended by the attacker.
A SQL injection is the same: the developer builds the application to make SQL queries for certain goals, but because of the way these queries are assembled by the application logic, the resulting actions of the SQL query, when executed by the database, can be disastrous from a security perspective.

Command injections don't have a clear solution: the shell is an ancient piece of technology, and the interfaces to the shell have ossified decades ago and are very hard to change.
SQL is somewhat more nimble, and most databases now provide interfaces that are very resistant to being SQL-injectible.
In fact, the authentication bypass levels used such interfaces: they are very vulnerable, but _not_ to SQL injection.

This level, on the other hand, _is_ SQL injectible, as it purposefully uses a slightly different way to make SQL queries.
When you find the SQL query into which you can inject your input (hint: it is the only SQL query to substantially differ between this level and the previous level), look at what the query looks like right now, and what unintended conditions you might inject.
The quintessential SQL injection adds a condition so that an application can succeed without knowing the password.
How can you accomplish this?
