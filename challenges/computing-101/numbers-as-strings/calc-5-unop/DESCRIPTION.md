Every operator so far has been *binary* --- two operands with an operator between them.
The last two are *unary*: a single operand, with the operator in front.

- `-` negates: `- 5` is `-5`.
- `~` flips every bit (bitwise NOT): `~ 5` is `-6`, because two's complement makes `~x` equal `-x - 1`.

The new idea is telling the two shapes apart.
A binary call passes three arguments after the program name (`prog A OP B`); a unary call passes two (`prog OP A`).
So the **argument count** decides which you're reading, and you already know where it lives: `argc` sits at `[rsp]`.
Branch on it *first*:

- `argc == 4`: the binary dispatch you already wrote (operator in `argv[2]`).
- `argc == 3`: the new unary dispatch, operator in `argv[1]` and operand in `argv[2]`.

This split is exactly what lets `-` mean two things: binary `-` subtracts (`12 - 5 = 7`), unary `-` negates (`- 5 = -5`).
The argument count tells them apart.

For the unary operators: `neg` the operand for `-`, and `not` it for `~`.
Print the result with your signed `itoa`, like any other answer.

```
- 5   ->  neg  ->  -5
~ 5   ->  not  ->  -6
```

Add the `argc` split and the two unary branches; an unrecognized unary operator quits, just like a binary one.
The shell expands a bare `~` to your home directory, so quote it (`-` you can type straight):

```console
hacker@dojo:~$ as -o prog.o prog.s
hacker@dojo:~$ ld -o prog prog.o
hacker@dojo:~$ ./prog - 5
-5
hacker@dojo:~$ ./prog '~' 5
-6
hacker@dojo:~$ /challenge/check prog
```

Split on the argument count, handle both unary operators, and score!
