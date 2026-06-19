A different first-stage bug can leak a different object or a different base field.
The escape stage still needs the same target offset, so the exploit must recalibrate from the new leak shape.

In this level, the harness gives you a first-stage leak and the delta to the escape preflight field.
Compute the target offset and write the token there, then run `/challenge/run` with your solve file to get the flag.
