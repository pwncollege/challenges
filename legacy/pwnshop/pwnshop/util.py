import contextlib
import traceback
import signal

def retry(max_attempts, timeout=None):
    def wrapper(func):
        @contextlib.wraps(func)
        def wrapped(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    if timeout:
                        def alarm(*args):
                            raise TimeoutError("ATTEMPT TIMED OUT")
                        signal.signal(signal.SIGALRM, alarm)
                        signal.alarm(timeout)
                    return func(*args, **kwargs)
                except TimeoutError:
                    print("... timed out. Retrying...")
                except AssertionError as e:
                    print("... verification failed:", e)
                    traceback.print_exc()
                    if attempt != max_attempts - 1:
                        print("... retrying...")
                finally:
                    signal.alarm(0)

            raise RuntimeError(f"Failed after {max_attempts} attempts!")

        return wrapped

    return wrapper

def did_segfault(process):
    r = process.poll(True)
    return r in (139, -signal.SIGSEGV)

def did_timeout(process):
    r = process.poll(True)
    return r in (124, 142, -signal.SIGALRM)

def did_abort(process):
    r = process.poll(True)
    return r in (134, -signal.SIGABRT)

def did_sigsys(process):
    r = process.poll(True)
    return r in (159, -signal.SIGSYS)
