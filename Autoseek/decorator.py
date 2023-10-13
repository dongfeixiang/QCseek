from functools import wraps

from PyQt6.QtWidgets import QMessageBox


def asyncCatchException(progress=None):
    def outer(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            try:
                await func(*args, **kwargs)
            except Exception as e:
                # progress.finished.emit()
                QMessageBox.critical(None, "错误", f"{type(e).__name__}({e})")
        return inner
    return outer
