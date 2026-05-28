set confirm off
set auto-load no
set history save off

set disassembly-flavor intel

# Layered defense: redefine in-gdb command escapes as no-ops.
# Not airtight, but closes the obvious paths.
define shell
  printf "(disabled by /challenge/bin/gdb)\n"
end

define pipe
  printf "(disabled by /challenge/bin/gdb)\n"
end

define python
  printf "(disabled by /challenge/bin/gdb)\n"
end

define python-interactive
  printf "(disabled by /challenge/bin/gdb)\n"
end

define guile
  printf "(disabled by /challenge/bin/gdb)\n"
end

define source
  printf "(disabled by /challenge/bin/gdb)\n"
end

define add-symbol-file
  printf "(disabled by /challenge/bin/gdb)\n"
end

define dump
  printf "(disabled by /challenge/bin/gdb)\n"
end

define save
  printf "(disabled by /challenge/bin/gdb)\n"
end
