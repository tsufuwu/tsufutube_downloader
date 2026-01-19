import tkinter as tk

class Tooltip:
    def __init__(self, widget, text_key, app_instance=None):
        self.widget = widget
        self.text_key = text_key
        self.app = app_instance
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text_key: return
        
        # Get translated text if app instance provided, else use key as text
        text = self.app.T(self.text_key) if self.app else self.text_key
        if not text: return

        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Determine colors based on theme if available
        bg = "#ffffe0"
        fg = "black"
        if self.app and hasattr(self.app, 'theme_var'):
            # High contrast for tooltip
            bg = "#333333" if self.app.theme_var.get() == "Dark" else "#ffffe0"
            fg = "#ffffff" if self.app.theme_var.get() == "Dark" else "#000000"

        label = tk.Label(tw, text=text, justify='left',
                       background=bg, foreground=fg,
                       relief='solid', borderwidth=1,
                       font=("Segoe UI", 9, "normal"))
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw: tw.destroy()
