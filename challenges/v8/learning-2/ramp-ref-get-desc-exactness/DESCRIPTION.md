Descriptor extraction still has to preserve whether the reference was exact or generic.
That distinction is what later makes an exactness confusion exploitable.

In this level, the harness gives you exact and generic values.
Extract both descriptor tokens without merging the cases, then run `/challenge/run` with your solve file to get the flag.
