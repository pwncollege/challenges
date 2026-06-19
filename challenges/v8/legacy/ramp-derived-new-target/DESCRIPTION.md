Derived JavaScript constructors do not create their receiver until `super()` runs.
The constructor that runs and the `new.target` used for allocation can be different.

That matters for Maglev bugs that reason about one constructor's allocation shape while JavaScript asks for another `new.target`.

In this level, the harness gives you a derived constructor and a replacement constructor.
Use `Reflect.construct` to run the derived constructor while supplying the replacement constructor as `new.target`, then run `/challenge/run` with your solve file to get the flag.
