set disassembly-flavor intel
set logging redirect on
set logging file /dev/null
set logging on
set confirm off
set height 0
set startup-with-shell off

define hook-stop
  set logging off
  printf "\n"
  disas
  printf "\n"
end
