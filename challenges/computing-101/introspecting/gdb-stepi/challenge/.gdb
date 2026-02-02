set disassembly-flavor intel
set logging redirect on
set logging file /dev/null
set logging on
set confirm off
set height 0

set $stop_count = 0

define show-censored-disas
  if $stop_count <= 0
    shell cat /challenge/.censored-disas-0
  else
    if $stop_count >= 5
      shell cat /challenge/.censored-disas-3
    else
      eval "shell cat /challenge/.censored-disas-%d", $stop_count - 1
    end
  end
end

define disassemble
  show-censored-disas
end

define disas
  show-censored-disas
end

define hook-stop
  set $stop_count = $stop_count + 1
  set logging off
  printf "\n"
  show-censored-disas
  printf "\n"
  if $stop_count == 1
    printf "HACKER: The disassembly above shows the program, but the secret value is CENSORED!\n"
    printf "HACKER: You can't read it from the code, but you CAN execute the instruction\n"
    printf "HACKER: and then read the register. Use 'stepi' (or 'si') to execute one instruction.\n"
  end
  if $stop_count == 2
    printf "HACKER: You stepped forward! The 'mov rdi, CENSORED' instruction just executed.\n"
    printf "HACKER: I'll now read the rdi register for you:\n"
    printf "\n(gdb) print $rdi\n"
    print $rdi
    printf "\nHACKER: There's your secret! Submit it with /challenge/submit-number.\n"
    printf "HACKER: You can quit GDB with 'quit' (or 'q').\n"
  end
end
