#pragma once

#include <Python.h>
#include <stddef.h>

typedef struct {
    PyObject_HEAD
    char *buf;
    size_t cap;
    size_t pos;
} PypuCapture;

PyObject *pypu_capture_new(char *buf, size_t cap);
