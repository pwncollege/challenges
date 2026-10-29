Template engines often resolve names through a configured loader so one template can reuse another.
That loader is part of the security boundary: a function that reads template source may expose every file inside its search path.

This Twig preview has a loader rooted more broadly than the application intended.
Use Twig's loader-related functionality to recover the flag.
