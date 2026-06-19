Exactness still matters when values cross the JS-to-Wasm boundary.
The later bug path depends on distinguishing exact boundary values from subtype-compatible ones.

In this level, the harness gives you one exact boundary value and one subtype-compatible boundary value.
Route each value through the matching boundary API function, return the two route results in order, then run `/challenge/run` with your solve file to get the flag.
