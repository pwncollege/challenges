set logging redirect on
set logging file /dev/null
set logging enabled on
set height 0
starti
stepi
set logging enabled off
printf "\n\n"
printf "You successfully started GDB!\n"
printf "Here is the secret number: %d\n", $rdi
printf "Submit that with /challenge/submit-number. Goodbye!\n"
set logging enabled on
stop
quit
