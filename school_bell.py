import tkinter as tk
from tkinter import messagebox, filedialog
import datetime
import threading
import time
import json
from playsound import playsound
import sys
import os

# ---------------- Helper for resource path ----------------
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ---------------- Data ----------------
weekly_schedule = {
    "Monday": ["08:00", "09:00", "10:00"],
    "Tuesday": ["08:00", "09:00", "10:00"],
    "Wednesday": ["08:00", "09:00", "10:00"],
    "Thursday": ["08:00", "09:00", "10:00"],
    "Friday": ["08:00", "09:00", "10:00"],
    "Saturday": [],
    "Sunday": []
}
special_days = {}
holidays = []
already_rang = set()
monitoring = False
muted = False

# ---------------- Bell Logic ----------------
def ring_bell():
    if muted:
        print("🔇 Bell muted.")
        return
    try:
        bell_path = resource_path("bell.mp3")
        playsound(bell_path)
    except Exception as e:
        print("Bell Error:", e)

def start_bell_monitor():
    global monitoring, already_rang
    monitoring = True
    update_status("Running...")

    while monitoring:
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        weekday = now.strftime("%A")
        current_time = now.strftime("%H:%M")

        # Holiday check
        if today_str in holidays:
            time.sleep(30)
            continue

        # Get today's schedule
        schedule = special_days.get(today_str, weekly_schedule.get(weekday, []))

        if current_time in schedule and current_time not in already_rang:
            ring_bell()
            already_rang.add(current_time)

        # Reset bell if day changes
        if now.strftime("%H:%M") == "00:00":
            already_rang.clear()

        time.sleep(5)
    update_status("Stopped")

# ---------------- GUI Actions ----------------
def on_start():
    if not monitoring:
        threading.Thread(target=start_bell_monitor, daemon=True).start()

def on_stop():
    global monitoring
    monitoring = False

def toggle_mute():
    global muted
    muted = not muted
    mute_button.config(text="🔈 Unmute" if muted else "🔇 Mute")

def add_time():
    time_val = entry_time.get().strip()
    day = selected_day.get()
    if validate_time(time_val):
        if time_val not in weekly_schedule[day]:
            weekly_schedule[day].append(time_val)
            refresh_listbox()
        entry_time.delete(0, tk.END)

def delete_time():
    day = selected_day.get()
    selected = listbox.curselection()
    if selected:
        t = listbox.get(selected[0])
        weekly_schedule[day].remove(t)
        refresh_listbox()

def delete_all_schedule():
    weekly_schedule[selected_day.get()] = []
    refresh_listbox()

def refresh_listbox():
    day = selected_day.get()
    listbox.delete(0, tk.END)
    for t in sorted(weekly_schedule.get(day, [])):
        listbox.insert(tk.END, t)

def validate_time(t):
    try:
        datetime.datetime.strptime(t, "%H:%M")
        return True
    except:
        return False

def add_holiday():
    date = entry_holiday.get().strip()
    if validate_date(date) and date not in holidays:
        holidays.append(date)
        update_holiday_list()
        entry_holiday.delete(0, tk.END)

def remove_selected_holiday():
    selected = listbox_holidays.curselection()
    if selected:
        date = listbox_holidays.get(selected[0])
        holidays.remove(date)
        update_holiday_list()

def update_holiday_list():
    listbox_holidays.delete(0, tk.END)
    for date in sorted(holidays):
        listbox_holidays.insert(tk.END, date)

def add_special_day():
    date = entry_special_date.get().strip()
    time_val = entry_special_time.get().strip()
    if validate_date(date) and validate_time(time_val):
        if date not in special_days:
            special_days[date] = []
        if time_val not in special_days[date]:
            special_days[date].append(time_val)
            update_special_day_list()
        entry_special_time.delete(0, tk.END)

def remove_selected_special():
    selected = listbox_specials.curselection()
    if selected:
        display = listbox_specials.get(selected[0])
        date, time_val = display.split(" ")
        special_days[date].remove(time_val)
        if not special_days[date]:
            del special_days[date]
        update_special_day_list()

def update_special_day_list():
    listbox_specials.delete(0, tk.END)
    for date, times in special_days.items():
        for t in times:
            listbox_specials.insert(tk.END, f"{date} {t}")

def validate_date(d):
    try:
        datetime.datetime.strptime(d, "%Y-%m-%d")
        return True
    except:
        return False

def save_schedule():
    file_path = filedialog.asksaveasfilename(defaultextension=".json")
    if file_path:
        data = {
            "weekly_schedule": weekly_schedule,
            "holidays": holidays,
            "special_days": special_days
        }
        with open(file_path, "w") as f:
            json.dump(data, f)
        messagebox.showinfo("Saved", "Schedule saved.")

def load_schedule():
    global weekly_schedule, holidays, special_days
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, "r") as f:
            data = json.load(f)
            weekly_schedule = data.get("weekly_schedule", {})
            holidays = data.get("holidays", [])
            special_days = data.get("special_days", {})
        refresh_listbox()
        update_holiday_list()
        update_special_day_list()
        messagebox.showinfo("Loaded", "Schedule loaded.")

def update_status(text):
    status_label.config(text=f"Status: {text}")

def update_countdown():
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    weekday = now.strftime("%A")

    if today in holidays:
        countdown_label.config(text="🎉 It's a holiday!")
    else:
        schedule = special_days.get(today, weekly_schedule.get(weekday, []))
        upcoming = [t for t in schedule if t > current_time]
        if upcoming:
            next_bell = min(upcoming)
            h, m = map(int, next_bell.split(":"))
            next_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            delta = next_dt - now
            mins, secs = divmod(int(delta.total_seconds()), 60)
            countdown_label.config(text=f"⏳ Next bell in {mins}m {secs}s")
        else:
            countdown_label.config(text="✅ All bells done for today!")

    root.after(1000, update_countdown)

# ---------------- GUI ----------------
root = tk.Tk()
root.title("🔔 School Bell System")
root.geometry("850x600")
root.configure(bg="white")

main_frame = tk.Frame(root, bg="white")
main_frame.pack(pady=10, fill="both", expand=True)

# Left Panel (Main Controls)
left_frame = tk.Frame(main_frame, bg="white")
left_frame.pack(side="left", padx=20, fill="y", expand=True, anchor="center")

tk.Label(left_frame, text="📅 Select Day", font=("Helvetica", 12, "bold")).pack()
selected_day = tk.StringVar(value="Monday")
tk.OptionMenu(left_frame, selected_day, *weekly_schedule.keys(), command=lambda _: refresh_listbox()).pack(pady=5)

entry_time = tk.Entry(left_frame, font=("Helvetica", 12))
entry_time.pack()
entry_time.insert(0, "HH:MM")

tk.Button(left_frame, text="➕ Add Time", command=add_time).pack(pady=2)
tk.Button(left_frame, text="❌ Delete Selected", command=delete_time).pack(pady=2)
tk.Button(left_frame, text="🗑️ Delete All Times", command=delete_all_schedule).pack(pady=2)

listbox = tk.Listbox(left_frame, height=6, font=("Helvetica", 12))
listbox.pack(pady=5)

tk.Button(left_frame, text="▶️ Start", bg="green", fg="white", command=on_start).pack(pady=3)
tk.Button(left_frame, text="⏹️ Stop", bg="red", fg="white", command=on_stop).pack(pady=3)
mute_button = tk.Button(left_frame, text="🔇 Mute", command=toggle_mute)
mute_button.pack(pady=3)

tk.Button(left_frame, text="💾 Save Schedule", command=save_schedule).pack(pady=2)
tk.Button(left_frame, text="📂 Load Schedule", command=load_schedule).pack(pady=2)

countdown_label = tk.Label(left_frame, text="", font=("Helvetica", 10, "italic"), fg="blue", bg="white")
countdown_label.pack(pady=10)

status_label = tk.Label(left_frame, text="Status: Stopped", font=("Helvetica", 10, "bold"), bg="white")
status_label.pack(pady=5)

#Right Panel (Holidays and Special Days)
right_frame = tk.Frame(main_frame, bg="white")
right_frame.pack(side="left", padx=20, fill="y", expand=True, anchor="center")

#Holidays
tk.Label(right_frame, text="📅 Holidays (No Bell)", font=("Helvetica", 12, "bold")).pack()
entry_holiday = tk.Entry(right_frame, font=("Helvetica", 12))
entry_holiday.pack(pady=2)
entry_holiday.insert(0, "YYYY-MM-DD")

tk.Button(right_frame, text="➕ Add Holiday", command=add_holiday).pack(pady=2)
tk.Button(right_frame, text="❌ Remove Selected Holiday", command=remove_selected_holiday).pack(pady=2)

listbox_holidays = tk.Listbox(right_frame, height=6, font=("Helvetica", 12))
listbox_holidays.pack(pady=5)

#Special Days
tk.Label(right_frame, text="⭐ Special Days", font=("Helvetica", 12, "bold")).pack(pady=(20, 0))
entry_special_date = tk.Entry(right_frame, font=("Helvetica", 12))
entry_special_date.pack(pady=2)
entry_special_date.insert(0, "YYYY-MM-DD")

entry_special_time = tk.Entry(right_frame, font=("Helvetica", 12))
entry_special_time.pack(pady=2)
entry_special_time.insert(0, "HH:MM")

tk.Button(right_frame, text="➕ Add Special Day Time", command=add_special_day).pack(pady=2)
tk.Button(right_frame, text="❌ Remove Selected Special", command=remove_selected_special).pack(pady=2)

listbox_specials = tk.Listbox(right_frame, height=6, font=("Helvetica", 12))
listbox_specials.pack(pady=5)

#Initialize lists
refresh_listbox()
update_holiday_list()
update_special_day_list()
update_countdown()

root.mainloop()
