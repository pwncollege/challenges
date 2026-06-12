#!/bin/bash -e

sudo /challenge/run | tee /dev/stderr | grep -F 'pwn.college{'
