set logging redirect on
set logging file /dev/null
set logging on
set height 0

define hook-stop
  stepi
  set logging off
  printf "\n\n"
  printf "You successfully started your program!\n"
  printf "Here is the secret number: %d\n", $rsi
  printf "Submit that with /challenge/submit-number. Goodbye!\n"
  set logging on
  stop
  quit
end
