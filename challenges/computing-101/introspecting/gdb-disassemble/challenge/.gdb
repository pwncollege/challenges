set disassembly-flavor intel
set logging redirect on
set logging file /dev/null
set logging on
set height 0

define hook-stop
  if !$hook_ran
    set $hook_ran = 1
    set logging off
    printf "\n\n"
    printf "HACKER: You successfully started your program!\n"
    printf "HACKER: Now, run the 'disassemble' command to view the assembly code.\n"
    printf "HACKER: Read the assembly to find the secret number stored in rdi and\n"
    printf "HACKER: submit that with /challenge/submit-number. Good luck!\n"
    printf "\n"
  end
end
