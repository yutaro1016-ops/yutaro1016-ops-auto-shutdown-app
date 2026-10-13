import tkinter as tk
from tkinter import ttk

from config import setup_logging
from ui import AutoShutdownApp


def main() -> None:
    setup_logging()
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass
    ttk.Style(root).theme_use("vista") if "vista" in ttk.Style(root).theme_names() else None
    AutoShutdownApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
