import customtkinter as ctk

class TimeSpinbox(ctk.CTkFrame):
    def __init__(self, master, width=100, height=30, **kwargs):
        super().__init__(master, width=width, height=height, fg_color="transparent", **kwargs)
        
        # Grid layout
        self.grid_columnconfigure((0, 2, 4), weight=1) # Entries
        self.grid_columnconfigure((1, 3), weight=0)    # Separators
        
        # Variables (H, M, S)
        self.h_var = ctk.StringVar(value="00")
        self.m_var = ctk.StringVar(value="00")
        self.s_var = ctk.StringVar(value="00")
        
        # Create Entries
        self.ent_h = self._create_entry(0, self.h_var, 23)
        self._create_sep(1)
        self.ent_m = self._create_entry(2, self.m_var, 59)
        self._create_sep(3)
        self.ent_s = self._create_entry(4, self.s_var, 59)
        
        self.state = "normal"

    def _create_entry(self, col, var, max_val):
        ent = ctk.CTkEntry(self, width=30,  justify="center", textvariable=var)
        ent.grid(row=0, column=col, padx=0, pady=0, sticky="ew")
        
        # Bind events
        ent.bind("<FocusOut>", lambda e: self._validate(var, max_val))
        ent.bind("<FocusIn>", lambda e: self._on_focus_in(var))
        ent.bind("<MouseWheel>", lambda e: self._on_scroll(e, var, max_val))
        # Button-4/5 for Linux scroll
        ent.bind("<Button-4>", lambda e: self._on_scroll(e, var, max_val, 1))
        ent.bind("<Button-5>", lambda e: self._on_scroll(e, var, max_val, -1))
        
        return ent

    def _create_sep(self, col):
        ctk.CTkLabel(self, text=":", width=5).grid(row=0, column=col, padx=1)

    def _validate(self, var, max_val):
        val = var.get()
        if not val.isdigit():
            val = "00"
        else:
            v_int = int(val)
            if v_int < 0: v_int = 0
            if v_int > max_val: v_int = max_val
            val = f"{v_int:02d}"
        var.set(val)

    def _on_focus_in(self, var):
        if var.get() == "00":
            var.set("")

    def _on_scroll(self, event, var, max_val, delta=None):
        if self.state == "disabled": return
        
        current = var.get()
        if not current.isdigit(): current = 0
        else: current = int(current)
        
        # Determine scroll direction
        if delta is not None:
            diff = delta
        else:
            diff = 1 if event.delta > 0 else -1
            
        new_val = current + diff
        
        # Wrap around or clamp? Let's clamp for now, maybe wrap for minutes/seconds later
        if new_val < 0: new_val = max_val
        elif new_val > max_val: new_val = 0
        
        var.set(f"{new_val:02d}")
        # Stop propagation
        return "break"

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.set_state(kwargs.pop("state"))
        super().configure(**kwargs)

    def set_state(self, state):
        self.state = state
        self.ent_h.configure(state=state)
        self.ent_m.configure(state=state)
        self.ent_s.configure(state=state)

    def get(self):
        """Return HH:MM:SS string"""
        h = self.h_var.get()
        m = self.m_var.get()
        s = self.s_var.get()
        return f"{h}:{m}:{s}"

    def set(self, time_str):
        """Set from HH:MM:SS"""
        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                self.h_var.set(f"{int(parts[0]):02d}")
                self.m_var.set(f"{int(parts[1]):02d}")
                self.s_var.set(f"{int(parts[2]):02d}")
        except:
            pass

    def bind_change(self, callback):
        """Bind callback when time changes (on write)"""
        self.h_var.trace_add("write", lambda *args: callback(self.get()))
        self.m_var.trace_add("write", lambda *args: callback(self.get()))
        self.s_var.trace_add("write", lambda *args: callback(self.get()))
