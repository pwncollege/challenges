In this level, you will work with control flow manipulation. This involves using instructions to indirectly and directly control the special register `rip`, the instruction pointer. You will use instructions such as `jmp`, `call`, `cmp`, and their alternatives to implement the requested behavior.

We will be testing your code multiple times in this level with dynamic values! This means we will run your code in various random ways to verify that the logic is robust enough to survive normal use.

The last jump type is the indirect jump, often used for switch statements in the real world. Switch statements are a special case of if-statements that use only numbers to determine where the control flow will go.

Here is an example:

```
switch(number):
  0: jmp do_thing_0
  1: jmp do_thing_1
  2: jmp do_thing_2
  default: jmp do_default_thing
```

The switch in this example works on `number`, which can either be 0, 1, or 2. If `number` is not one of those numbers, the default triggers. You can consider this a reduced else-if type structure. In x86, you are already used to using numbers, so it should be no surprise that you can make if statements based on something being an exact number. Additionally, if you know the range of the numbers, a switch statement works very well.

Take, for instance, the existence of a jump table. A jump table is a contiguous section of memory that holds addresses of places to jump.

In the above example, the jump table could look like:

```
[0x1337] = address of do_thing_0
[0x1337+0x8] = address of do_thing_1
[0x1337+0x10] = address of do_thing_2
[0x1337+0x18] = address of do_default_thing
```

Using the jump table, we can greatly reduce the amount of `cmps` we use. Now all we need to check is if `number` is greater than 2. If it is, always do:

```
jmp [0x1337+0x18]
```

Otherwise:

```
jmp [jump_table_address + number * 8]
```

Using the above knowledge, implement the following logic:
```plaintext
if rdi is 0:
  jmp 0x40301e
else if rdi is 1:
  jmp 0x4030da
else if rdi is 2:
  jmp 0x4031d5
else if rdi is 3:
  jmp 0x403268
else:
  jmp 0x40332c
```

Please do the above with the following constraints:

- Assume `rdi` will NOT be negative.
- Use no more than 1 `cmp` instruction.
- Use no more than 3 jumps (of any variant).
- We will provide you with the number to 'switch' on in `rdi`.
- We will provide you with a jump table base address in `rsi`.

Here is an example table:

```
[0x40427c] = 0x40301e (addrs will change)
[0x404284] = 0x4030da
[0x40428c] = 0x4031d5
[0x404294] = 0x403268
[0x40429c] = 0x40332c
```