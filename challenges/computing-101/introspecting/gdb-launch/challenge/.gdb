set logging redirect on
set logging file /dev/null
set logging on
set height 0
starti
stepi
set logging off
printf "\n\n"
printf "You successfully started GDB!\n"
printf "Here is the secret number: %d\n", $rsi
printf "Submit that with /challenge/submit-number. Goodbye!\n"
set logging on
stop
quit
