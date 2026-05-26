import asyncio
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageOps

# Farbpalette
COLOR_BG = "#1e1e1e"
COLOR_RAILS = "#2a2d2e"
COLOR_DOOR_NORMAL = "#7a7a7a"
COLOR_DOOR_ERROR = "#ff3333"
COLOR_MOTOR_OFF = "#444444"
COLOR_MOTOR_ON = "#00cc44"
COLOR_LED_ON = "#00ff00"
COLOR_LED_OFF = "#555555"
COLOR_BTN_OFF = "#3a3a3a"
COLOR_BTN_ON = "#007a33"


class RolltorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Roller Door Simulation")
        self.geometry("740x500")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")

        # --- EIGENSCHAFTEN / STATE VARIABLES ---
        self.pos = 0.0  # 0% = geschlossen, 100% = komplett offen
        self.current_speed = 0.0  # AKTUELLE Geschwindigkeit (für Trägheit)
        self.error = False
        self.running = True

        # Hilfsvariablen für das manuelle Gedrückthalten der Sensoren
        self.manual_upper_pressed = False
        self.manual_lower_pressed = False

        self._load_background_image()
        self._setup_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_background_image(self):
        try:
            img = Image.open("assets/images/kyrgyzstan-info.jpg")
            img = ImageOps.fit(img, (780, 600), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Hintergrundbild konnte nicht geladen werden: {e}")
            self.bg_photo = None

    def _setup_ui(self):
        self.canvas_frame = ctk.CTkFrame(self, corner_radius=10)
        self.canvas_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.control_frame = ctk.CTkFrame(self, width=250, corner_radius=10)
        self.control_frame.pack(side="right", fill="y", padx=(0, 10), pady=10)

        self.canvas = tk.Canvas(self.canvas_frame, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # --- SCHALTVARIABLEN ---
        self.var_up = ctk.BooleanVar(value=False)
        self.var_down = ctk.BooleanVar(value=False)
        self.var_upper_limit = ctk.BooleanVar(value=False)
        self.var_lower_limit = ctk.BooleanVar(value=True)

        # --- STEUERUNGS-PANEL (Latching Logik) ---
        ctk.CTkLabel(self.control_frame, text="Motorsteuerung (Latching)", font=("Arial", 16, "bold")).pack(
            pady=(20, 10))

        # Changed to command callbacks for stateful toggling
        self.btn_up = ctk.CTkButton(self.control_frame, text="Motor AUF (Up)", fg_color=COLOR_BTN_OFF,
                                    command=self.toggle_motor_up)
        self.btn_up.pack(pady=5, padx=20)

        self.btn_down = ctk.CTkButton(self.control_frame, text="Motor AB (Down)", fg_color=COLOR_BTN_OFF,
                                      command=self.toggle_motor_down)
        self.btn_down.pack(pady=5, padx=20)

        ctk.CTkLabel(self.control_frame, text="Endschalter (Sensoren)", font=("Arial", 16, "bold")).pack(pady=(20, 10))

        self.btn_upper_limit = ctk.CTkButton(self.control_frame, text="Limit Oben (100%)", fg_color=COLOR_BTN_OFF,
                                             command=self.toggle_manual_upper)
        self.btn_upper_limit.pack(pady=5, padx=20)

        self.btn_lower_limit = ctk.CTkButton(self.control_frame, text="Limit Unten (0%)", fg_color=COLOR_BTN_OFF,
                                             command=self.toggle_manual_lower)
        self.btn_lower_limit.pack(pady=5, padx=20)

        ctk.CTkLabel(self.control_frame, text="System", font=("Arial", 16, "bold")).pack(pady=(20, 10))

        self.btn_reset = ctk.CTkButton(self.control_frame, text="RESET", fg_color="#cc0000", hover_color="#ff3333",
                                       command=self.trigger_reset)
        self.btn_reset.pack(pady=10, padx=20)

        # --- FEHLER-WARNUNG ---
        self.lbl_error = ctk.CTkLabel(self.control_frame, text="", font=("Arial", 22, "bold"),
                                      text_color=COLOR_DOOR_ERROR)
        self.lbl_error.pack(pady=(10, 0))

        # Positionsanzeige
        self.lbl_pos = ctk.CTkLabel(self.control_frame, text="Position: 0%", font=("Courier", 24, "bold"),
                                    text_color="#00ff00")
        self.lbl_pos.pack(pady=(10, 10))

    # --- MOTOR-EVENTS (Stateful) ---
    def toggle_motor_up(self):
        if not self.error:
            new_state = not self.var_up.get()
            self.var_up.set(new_state)
            if new_state:
                self.var_down.set(False)  # Interlock: Ensure Down is off
            self._sync_buttons()

    def toggle_motor_down(self):
        if not self.error:
            new_state = not self.var_down.get()
            self.var_down.set(new_state)
            if new_state:
                self.var_up.set(False)  # Interlock: Ensure Up is off
            self._sync_buttons()

    # --- SENSOR-EVENTS ---
    def toggle_manual_upper(self):
        self.manual_upper_pressed = not self.manual_upper_pressed

    def toggle_manual_lower(self):
        self.manual_lower_pressed = not self.manual_lower_pressed

    def _sync_buttons(self):
        self.btn_up.configure(fg_color=COLOR_BTN_ON if self.var_up.get() else COLOR_BTN_OFF)
        self.btn_down.configure(fg_color=COLOR_BTN_ON if self.var_down.get() else COLOR_BTN_OFF)
        self.btn_upper_limit.configure(fg_color=COLOR_BTN_ON if self.var_upper_limit.get() else COLOR_BTN_OFF)
        self.btn_lower_limit.configure(fg_color=COLOR_BTN_ON if self.var_lower_limit.get() else COLOR_BTN_OFF)

    # --- SYSTEM-LOGIK ---
    def trigger_reset(self):
        self.error = False
        self.var_up.set(False)
        self.var_down.set(False)
        self.manual_upper_pressed = False
        self.manual_lower_pressed = False
        self.current_speed = 0.0
        self.pos = max(0.0, min(100.0, self.pos))
        self.lbl_error.configure(text="")
        self._sync_buttons()

    def trigger_error(self):
        self.error = True
        self.var_up.set(False)
        self.var_down.set(False)
        self.current_speed = 0.0
        self.lbl_error.configure(text="!!! FEHLER !!!")
        self._sync_buttons()

    def _update_logic(self):
        if self.error:
            self.lbl_pos.configure(text="ERROR", text_color="#ff3333")
            return

        up = self.var_up.get()
        down = self.var_down.get()

        if up and down:
            self.trigger_error()
            return

        # Check sensors (Limit switches trigger at 100% and 0%)
        is_upper = (self.pos >= 100.0) or self.manual_upper_pressed
        is_lower = (self.pos <= 0.0) or self.manual_lower_pressed

        self.var_upper_limit.set(is_upper)
        self.var_lower_limit.set(is_lower)

        # --- Speed Calculation ---
        target_speed = 0.0
        if up: target_speed = 0.3
        if down: target_speed = -0.3

        accel = 0.1

        if self.current_speed < target_speed:
            self.current_speed = min(self.current_speed + accel, target_speed)
        elif self.current_speed > target_speed:
            self.current_speed = max(self.current_speed - accel, target_speed)

        # Move the door
        self.pos += self.current_speed

        # --- Hardware safety limits (Overtravel Fault) ---
        # If the motor isn't turned off by the user or OPC UA after passing 100% or 0%, it crashes.
        if self.pos >= 102.0 or self.pos <= -2.0:
            self.trigger_error()
            return

        self._sync_buttons()
        self.lbl_pos.configure(text=f"Position: {int(self.pos)}%", text_color="#00ff00")

    def _draw_canvas(self):
        self.canvas.delete("all")

        cx, width = 355, 780
        top_y, bottom_y = 30, 630
        rail_w = 25

        x_left = cx - width // 2
        x_right = cx + width // 2

        # 0. HINTERGRUNDBILD
        if hasattr(self, 'bg_photo') and self.bg_photo:
            self.canvas.create_image(cx, top_y + (bottom_y - top_y) // 2, image=self.bg_photo)
        else:
            self.canvas.create_rectangle(x_left, top_y, x_right, bottom_y, fill="#0a0a0a", outline="")

        # 1. Führungsschienen
        self.canvas.create_rectangle(x_left - rail_w, top_y, x_left, bottom_y, fill=COLOR_RAILS, outline="#111")
        self.canvas.create_rectangle(x_right, top_y, x_right + rail_w, bottom_y, fill=COLOR_RAILS, outline="#111")

        # 3. Rolltor
        current_bottom_y = bottom_y - (bottom_y - top_y) * (self.pos / 100.0)
        door_color = COLOR_DOOR_ERROR if self.error else COLOR_DOOR_NORMAL

        if current_bottom_y > top_y:
            self.canvas.create_rectangle(x_left, top_y, x_right, current_bottom_y, fill=door_color, outline="")

            slat_height = 15
            y = top_y + slat_height
            while y < current_bottom_y:
                self.canvas.create_line(x_left, y, x_right, y, fill="#222", width=1)
                y += slat_height

            self.canvas.create_rectangle(x_left, current_bottom_y - 5, x_right, current_bottom_y, fill="#444",
                                         outline="")

        # 2. Sensoren (Endschalter LEDs)
        up_color = COLOR_LED_ON if self.var_upper_limit.get() else COLOR_LED_OFF
        self.canvas.create_rectangle(15, 40, 35, 60, fill=up_color, outline="#111")

        low_color = COLOR_LED_ON if self.var_lower_limit.get() else COLOR_LED_OFF
        self.canvas.create_rectangle(15, 620, 35, 600, fill=low_color, outline="#111")

        # 4. Motor / Gehäuse oben
        motor_powered = (self.var_up.get() or self.var_down.get()) and not self.error
        motor_color = COLOR_MOTOR_ON if motor_powered else COLOR_MOTOR_OFF

        self.canvas.create_rectangle(x_left - rail_w - 10, top_y - 30, x_right + rail_w + 10, top_y, fill="#333",
                                     outline="#111")
        self.canvas.create_oval(cx - 15, top_y - 25, cx + 15, top_y + 5, fill=motor_color, outline="#111", width=2)

    async def async_mainloop(self):
        while self.running:
            self._update_logic()
            self._draw_canvas()
            self.update()
            await asyncio.sleep(0.02)

    def _on_closing(self):
        self.running = False
        self.destroy()


if __name__ == "__main__":
    app = RolltorApp()
    asyncio.run(app.async_mainloop())