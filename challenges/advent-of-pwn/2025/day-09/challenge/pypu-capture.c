#include "qemu/osdep.h"

#include <Python.h>
#include <stdio.h>
#include <string.h>

#include "pypu-capture.h"

static PyObject *capture_write(PyObject *self, PyObject *args)
{
    PypuCapture *cf = (PypuCapture *)self;
    const char *data = NULL;
    Py_ssize_t len = 0;
    if (!PyArg_ParseTuple(args, "s#", &data, &len)) {
        return NULL;
    }
    if (!cf->buf || cf->cap == 0) {
        Py_RETURN_NONE;
    }
    size_t copy_len = (size_t)len;
    if (copy_len > cf->cap - 1 - cf->pos) {
        copy_len = cf->cap - 1 - cf->pos;
    }
    if (copy_len > 0) {
        memcpy(cf->buf + cf->pos, data, copy_len);
        cf->pos += copy_len;
        cf->buf[cf->pos] = '\0';
    }
    return PyLong_FromSsize_t((Py_ssize_t)copy_len);
}

static PyObject *capture_flush(PyObject *self, PyObject *Py_UNUSED(ignored))
{
    Py_RETURN_NONE;
}

static PyObject *capture_seek(PyObject *self, PyObject *args)
{
    PypuCapture *cf = (PypuCapture *)self;
    Py_ssize_t offset = 0;
    int whence = SEEK_SET;
    if (!PyArg_ParseTuple(args, "n|i", &offset, &whence)) {
        return NULL;
    }

    Py_ssize_t newpos = 0;
    if (whence == SEEK_SET) {
        newpos = offset;
    } else if (whence == SEEK_CUR) {
        newpos = (Py_ssize_t)cf->pos + offset;
    } else if (whence == SEEK_END) {
        Py_ssize_t end = cf->buf ? (Py_ssize_t)strlen(cf->buf) : 0;
        newpos = end + offset;
    } else {
        PyErr_SetString(PyExc_ValueError, "invalid whence");
        return NULL;
    }

    Py_ssize_t max_pos = (Py_ssize_t)((cf->cap > 0) ? (cf->cap - 1) : 0);
    if (newpos < 0) {
        newpos = 0;
    } else if (newpos > max_pos) {
        newpos = max_pos;
    }
    cf->pos = (size_t)newpos;
    return PyLong_FromSize_t(cf->pos);
}

static PyMethodDef capture_methods[] = {
    {"write", capture_write, METH_VARARGS, "Append to buffer"},
    {"flush", capture_flush, METH_NOARGS, "No-op flush"},
    {"seek", capture_seek, METH_VARARGS, "Adjust write position"},
    {NULL, NULL, 0, NULL},
};

static PyTypeObject CaptureType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "pypu.Capture",
    .tp_basicsize = sizeof(PypuCapture),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_methods = capture_methods,
};

PyObject *pypu_capture_new(char *buf, size_t cap)
{
    static int type_ready = 0;
    if (!type_ready) {
        if (PyType_Ready(&CaptureType) < 0) {
            return NULL;
        }
        type_ready = 1;
    }
    PypuCapture *cf = PyObject_New(PypuCapture, &CaptureType);
    if (!cf) {
        return NULL;
    }
    cf->buf = buf;
    cf->cap = cap;
    cf->pos = 0;
    if (cf->buf && cf->cap > 0) {
        cf->buf[0] = '\0';
    }
    return (PyObject *)cf;
}
