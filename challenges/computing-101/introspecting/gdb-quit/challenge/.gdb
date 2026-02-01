set logging redirect on
set logging file /dev/null
set logging on
set confirm off
set height 0
starti
stepi
set logging off
printf "\n\n"
printf "You successfully started GDB!\n"
printf "Here is the secret number: %d\n", $rdi
printf "Submit that with /challenge/submit-number.\n"
printf "\n"
printf "HACKER: Now, quit GDB by typing 'quit' (or just 'q').\n"
printf "\n"
