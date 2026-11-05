set disassembly-flavor intel
set logging redirect on
set logging file /dev/null
set logging on
set confirm off
set height 0

define hook-stop
  set logging off
  printf "\n"
  disas
  printf "\n"
end

break int3_loc
commands
silent
python gdb.execute("set $rdi = " + __import__("subprocess").check_output(["/challenge/.read-secret"]).decode().strip())
end
