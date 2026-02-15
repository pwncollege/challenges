#!/bin/bash -e
echo 'console.log("ok");' > /tmp/test.js
/challenge/d8 /tmp/test.js 2>&1 | grep -q ok
