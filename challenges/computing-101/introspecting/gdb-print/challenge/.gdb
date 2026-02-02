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
    printf "HACKER: The disassembly is CENSORED! Use 'stepi' to execute the first instruction.\n"
  end
  if $stop_count == 2
    printf "HACKER: You just executed 'mov rdi, CENSORED' --- the secret is now in rdi!\n"
    printf "HACKER: Use 'print $rdi' to read the register value!\n"
    printf "HACKER: When you're done, quit GDB with 'quit' (or 'q').\n"
  end
  if $stop_count >= 3
    printf "HACKER: You stepped further --- rdi may have been overwritten!\n"
    printf "HACKER: Restart with 'run' and step only ONCE before printing $rdi.\n"
  end
end
