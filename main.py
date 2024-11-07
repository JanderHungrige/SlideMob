import tkinter as tk
from slidemob.gui.main import SlideMobGUI

def main():
    root = tk.Tk()
    app = SlideMobGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()