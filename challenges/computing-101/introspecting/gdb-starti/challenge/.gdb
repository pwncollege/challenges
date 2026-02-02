set disassembly-flavor intel
set logging redirect on
set logging file /dev/null
set logging on
set confirm off
set height 0

define hook-stop
  set logging off
  printf "\n\n"
  printf "HACKER: You successfully started your program!\n"
  printf "HACKER: I am now going to invoke the 'disassemble' command for you.\n"
  printf "HACKER: Read the assembly to find the secret number stored in rdi and\n"
  printf "HACKER: submit that with /challenge/submit-number. Good luck!\n"
  printf "\n(gdb) disassemble\n"
  disas
  printf "\nHACKER: You can now quit GDB by typing 'quit' (or just 'q').\n"
end
