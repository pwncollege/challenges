set disassembly-flavor intel
set logging redirect on
set logging file /dev/null
set logging enabled on
set confirm off
set height 0

set $stop_count = 0

define show-censored-disas
  if $stop_count <= 0
    shell cat /challenge/.censored-disas-0
  else
    if $stop_count >= 6
      shell cat /challenge/.censored-disas-4
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
  set logging enabled off
  printf "\n"
  show-censored-disas
  printf "\n"
  if $stop_count == 1
    printf "HACKER: Use 'stepi' to execute the first instruction.\n"
  end
  if $stop_count == 2
    printf "HACKER: The first instruction set rdi to 0.\n"
    printf "HACKER: Use 'set $rdi = 1337' to change it, then use 'stepi' once more.\n"
  end
  if $stop_count == 3
    printf "HACKER: Your changed register produced a secret number!\n"
    printf "HACKER: Use 'print $rdi' to read it, then submit it with /challenge/submit-number.\n"
    printf "HACKER: When you're done, quit GDB with 'quit' (or 'q').\n"
  end
  if $stop_count >= 4
    printf "HACKER: You stepped further, so rdi may have been overwritten.\n"
    printf "HACKER: Quit GDB and start over.\n"
  end
end
