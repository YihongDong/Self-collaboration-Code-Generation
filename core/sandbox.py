import contextlib
import faulthandler
import io
import os
import platform
import signal
import tempfile


def unsafe_execute(code, report):
    with create_tempdir():
        import os
        import shutil
        rmtree = shutil.rmtree
        rmdir = os.rmdir
        chdir = os.chdir

        reliability_guard()

        check_program = code + report

        try:
            exec_globals = {}
            with swallow_io():
                timeout = 10
                with time_limit(timeout):
                    exec(check_program, exec_globals)
            result = "Code Test Passed."
        except AssertionError as e:
            result = f"failed with AssertionError. {e}"
        except TimeoutException:
            result = "timed out"
        except BaseException as e:
            result = f"{e}"

        shutil.rmtree = rmtree
        os.rmdir = rmdir
        os.chdir = chdir
        return result


def reliability_guard(maximum_memory_bytes=None):
    if maximum_memory_bytes is not None:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (maximum_memory_bytes, maximum_memory_bytes))
        resource.setrlimit(resource.RLIMIT_DATA, (maximum_memory_bytes, maximum_memory_bytes))
        if not platform.uname().system == 'Darwin':
            resource.setrlimit(resource.RLIMIT_STACK, (maximum_memory_bytes, maximum_memory_bytes))

    faulthandler.disable()

    import builtins
    builtins.exit = None
    builtins.quit = None

    import os
    os.environ['OMP_NUM_THREADS'] = '1'
    os.rmdir = None
    os.chdir = None

    import shutil
    shutil.rmtree = None
    shutil.move = None
    shutil.chown = None

    import subprocess
    subprocess.Popen = None

    __builtins__['help'] = None

    import sys
    sys.modules['ipdb'] = None
    sys.modules['joblib'] = None
    sys.modules['resource'] = None
    sys.modules['psutil'] = None
    sys.modules['tkinter'] = None


@contextlib.contextmanager
def time_limit(seconds: float):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@contextlib.contextmanager
def swallow_io():
    stream = WriteOnlyStringIO()
    with contextlib.redirect_stdout(stream):
        with contextlib.redirect_stderr(stream):
            with redirect_stdin(stream):
                yield


@contextlib.contextmanager
def create_tempdir():
    with tempfile.TemporaryDirectory() as dirname:
        with chdir(dirname):
            yield dirname


class TimeoutException(Exception):
    pass


class WriteOnlyStringIO(io.StringIO):
    def read(self, *args, **kwargs):
        raise IOError

    def readline(self, *args, **kwargs):
        raise IOError

    def readlines(self, *args, **kwargs):
        raise IOError

    def readable(self, *args, **kwargs):
        return False


class redirect_stdin(contextlib._RedirectStream):
    _stream = 'stdin'


@contextlib.contextmanager
def chdir(root):
    if root == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(root)
    try:
        yield
    except BaseException as exc:
        raise exc
    finally:
        os.chdir(cwd)
