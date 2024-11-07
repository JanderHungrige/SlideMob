import tkinter as tk
from slidemob.gui.main import SlideMobGUI
# from slidemob.utils.errorhandler import setup_error_logging

# # Initialize error logging
# setup_error_logging()

def main():
    root = tk.Tk()
    app = SlideMobGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()