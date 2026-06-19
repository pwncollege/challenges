Maglev is V8's mid-tier optimizing compiler.
A Maglev-only vulnerability is not reachable until the target function actually runs as Maglev code.

In this level, d8 exposes V8 native optimization helpers and a narrow `WinMaglevObserved(maglev_status, turbofan_status)` checker.
Compile one function with Maglev, compile a second function with TurboFan, pass both optimization status values to the checker, and get the flag.
