# handlers.py
import csv
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Callable

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, Toplevel, Text, Scrollbar, RIGHT, Y, END

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import models
from models import VisitData, VisitNotes

from hmac import compare_digest

import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USAGE_FILE = os.path.join(BASE_DIR, "usage_log.csv")

USAGE_FIELDS = ["username", "role", "timestamp", "event", "action"]

# ──────────────────────────────────────────────────────────────────────────────
def prompt_date(
    parent: tk.Widget,
    prompt_text: str
) -> Optional[str]:
    """
    prompt for a date in YYYY-MM-DD or YYYY/MM/DD.
    Returns the date formatted as MM/DD/YYYY, or None if cancelled.
    """
    allowed = ["YYYY-MM-DD", "YYYY/MM/DD"]
    prompt_formats = " or ".join(allowed)
    while True:
        raw = simpledialog.askstring(
            "Date",
            f"{prompt_text} ({prompt_formats}):",
            parent=parent
        )
        if raw is None:
            return None
        s = raw.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(s, fmt).date()
                return dt.strftime("%m/%d/%Y")
            except ValueError:
                continue

        # If we get here, none of the formats matched
        messagebox.showerror(
            "Invalid Date",
            f"‘{raw}’ isn’t recognized.\nPlease use {prompt_formats}.",
            parent=parent
        )

# ──────────────────────────────────────────────────────────────────────────────
def prompt_zip_code(parent: tk.Widget) -> str | None:
    """Prompt for a valid 5-digit ZIP code, or return None if cancelled."""
    while True:
        zip_code = simpledialog.askstring(
            "Zip Code",
            "Enter 5-digit ZIP Code:",
            parent=parent
        )

        if zip_code is None:
            return None  # User cancelled

        zip_code = zip_code.strip()

        if zip_code.isdigit() and len(zip_code) == 5:
            return zip_code  # Valid input

        messagebox.showerror(
            "Invalid ZIP",
            "Please enter a valid 5-digit ZIP code.",
            parent=parent
        )

# ──────────────────────────────────────────────────────────────────────────────

def collect_visit_data(
    parent: tk.Widget
) -> Optional[Tuple[VisitData, VisitNotes]]:
    """Prompt for visit details. Returns (visit_data, visit_notes) or None."""
    # 1) Visit date
    visit_time = prompt_date(parent, "Enter Visit Date")
    if visit_time is None:
        return None

    # 2) Department
    dept = simpledialog.askstring(
        "Department",
        "Enter Department (e.g. ER, Cardiology):",
        parent=parent
    )
    if not dept:
        return None

    # 3) Demographics
    race = simpledialog.askstring("Race", "Enter Patient's Race:", parent=parent)
    if not race:
        return None

    gender = simpledialog.askstring(
        "Gender",
        "Enter Patient's Gender (Male, Female, Non-binary, Other):",
        parent=parent
    )
    if not gender:
        return None

    ethnicity = simpledialog.askstring(
        "Ethnicity",
        "Enter Patient's Ethnicity:",
        parent=parent
    )
    if not ethnicity:
        return None

    # 4) Age
    age = simpledialog.askinteger("Age", "Enter Age:", parent=parent)
    if age is None:
        return None

    # 5) Zip code
    zip_code = prompt_zip_code(parent=parent)
    if zip_code is None:
        return None
    
    # 6) Insurance & Complaint
    insurance = simpledialog.askstring(
        "Insurance",
        "Enter Insurance Provider:",
        parent=parent
    )
    if not insurance:
        return None

    complaint = simpledialog.askstring(
        "Chief Complaint",
        "Enter Chief Complaint:",
        parent=parent
    )
    if not complaint:
        return None

    # 7) Note metadata
    note_id = uuid.uuid4().hex
    note_type = simpledialog.askstring("Note Type", "Enter Note Type:", parent=parent)
    if not note_type:
        return None

    note_text = simpledialog.askstring("Visit Notes", "Enter Visit Notes:", parent=parent)
    if note_text is None:
        return None

    visit_data: VisitData = {
        "Visit_time":       visit_time,
        "Visit_department": dept.strip().capitalize(),
        "Race":             race.strip().capitalize(),
        "Gender":           gender.strip().capitalize(),
        "Ethnicity":        ethnicity.strip().capitalize(),
        "Age":              age,
        "Zip_code":         zip_code,
        "Insurance":        insurance.strip().capitalize(),
        "Chief_complaint":  complaint.strip().capitalize(),
        "Note_ID":          note_id,
        "Note_type":        note_type.strip().capitalize(),
    }
    visit_notes: VisitNotes = {
        "Note_ID":   note_id,
        "Note_text": note_text.strip(),
    }
    return visit_data, visit_notes

# ──────────────────────────────────────────────────────────────────────────────
def show_temporal_trends(
    parent: tk.Widget,
    db: models.PatientDatabase
) -> None:
    """Show a table and plot of visits aggregated by year."""

    # Aggregate by year
    year_counts: Dict[int, int] = {}
    for row in db.get_visit_data_rows():
        vs = row.get("Visit_time")
        if vs:
            try:
                visit_date = datetime.strptime(vs.strip(), "%m/%d/%Y")
                year = visit_date.year
                year_counts[year] = year_counts.get(year, 0) + 1
            except ValueError:
                continue  # skip bad date formats

    if not year_counts:
        messagebox.showinfo("No Data", "No valid visit dates found.", parent=parent)
        return

    years = sorted(year_counts)
    counts = [year_counts[y] for y in years]

    # Create popup window
    win = tk.Toplevel(parent)
    win.title("Yearly Visit Trends")
    win.grab_set()

    # Table
    tv = ttk.Treeview(win, columns=("Year", "#Visits"), show="headings", height=10)
    tv.heading("Year", text="Year")
    tv.heading("#Visits", text="# Visits")

    for y, c in zip(years, counts):
        tv.insert("", "end", values=(y, c))
    tv.pack(fill="both", expand=True, padx=10, pady=10)

    # Plot
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(years, counts, marker="o", linestyle="-")
    ax.set_title("Visits per Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("# Visits")
    ax.set_xticks(years)
    fig.tight_layout()

    fc = FigureCanvasTkAgg(fig, master=win)
    fc.draw()
    fc.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

# ──────────────────────────────────────────────────────────────────────────────
def add_patient(
    parent: tk.Widget,
    db: models.PatientDatabase,
    data_file: str,
    notes_file: str,
    data_fieldnames: List[str],
    notes_fieldnames: List[str]
) -> None:
    pid = simpledialog.askstring("Patient ID", "Enter Patient ID:", parent=parent)
    if not pid:
        return
    if db.get_patient(pid):
        messagebox.showinfo("Patient Found", f"Adding visit for {pid}", parent=parent)
    else:
        messagebox.showinfo("New Patient", f"Creating record for {pid}", parent=parent)
        db.patients[pid] = models.PatientRecord(pid)

    pair = collect_visit_data(parent)
    if not pair:
        return
    visit_data, visit_notes = pair
    vid = uuid.uuid4().hex
    rec = db.get_patient(pid)
    rec.add_visit(vid, data=visit_data, notes=visit_notes)
    db.save_visit_data(data_file, fieldnames=data_fieldnames)
    db.save_visit_notes(notes_file)
    messagebox.showinfo("Success", f"Visit {vid} added for {pid}", parent=parent)

# ──────────────────────────────────────────────────────────────────────────────
def remove_patient(
    parent: tk.Widget,
    db: models.PatientDatabase,
    data_file: str,
    notes_file: str,
    data_fieldnames: List[str],
    notes_fieldnames: List[str]
) -> None:
    pid = simpledialog.askstring("Patient ID", "Enter Patient ID to remove:", parent=parent)
    if not pid:
        return
    if not messagebox.askyesno("Confirm", f"Remove {pid}?", parent=parent):
        return
    removed = db.remove_patient(pid)
    db.save_visit_data(data_file, fieldnames=data_fieldnames)
    db.save_visit_notes(notes_file)
    if removed:
        messagebox.showinfo("Removed", f"{pid} removed", parent=parent)
    else:
        messagebox.showwarning("Not Found", f"No record for {pid}", parent=parent)

# ──────────────────────────────────────────────────────────────────────────────
def retrieve_patient(
    parent: tk.Widget,
    db: models.PatientDatabase
) -> None:
    pid = simpledialog.askstring("Patient ID", "Enter Patient ID:", parent=parent)
    if not pid:
        return

    # Mapping from button text to actual field names
    field_map = {
        "Visit times": "Visit_time",
        "Visit Departments": "Visit_department",
        "Race": "Race",
        "Gender": "Gender",
        "Ethnicity": "Ethnicity",
        "Ages": "Age",
        "Zip Codes": "Zip_code",
        "Insurances": "Insurance",
        "Chief Complaints": "Chief_complaint"
    }

    # Callback when a field is selected
    def on_field_select(label: str):
        field = field_map[label]
        res = db.retrieve_patient_info(pid, field)
        if res is None:
            messagebox.showerror("Error", f"No patient {pid}", parent=parent)
        elif not res:
            messagebox.showinfo("No Data", f"No {label} for {pid}", parent=parent)
        else:
            messagebox.showinfo("Data", f"{label}:\n" + "\n".join(map(str, res)), parent=parent)
        popup.destroy()

    # Create popup
    popup = tk.Toplevel(parent)
    popup.title("Select Field")
    popup.grab_set()

    label = tk.Label(popup, text="Select a field to retrieve:")
    label.pack(pady=(10, 5))

    for label_text in field_map:
        btn = tk.Button(popup, text=label_text, width=25, command=lambda lbl=label_text: on_field_select(lbl))
        btn.pack(padx=10, pady=2)

    cancel_btn = tk.Button(popup, text="Cancel", command=popup.destroy)
    cancel_btn.pack(pady=(5, 10))

# ──────────────────────────────────────────────────────────────────────────────
def count_visits(
    parent: tk.Widget,
    db: models.PatientDatabase
) -> None:
    ds = prompt_date(parent, "Enter date for visit count")
    if ds is None:
        return
    cnt = db.count_visits_in_day(ds)
    if cnt is None:
        messagebox.showerror("Error", f"Bad date: {ds}", parent=parent)
    else:
        messagebox.showinfo("Visit Count", f"{cnt} visits on {ds}", parent=parent)

# ──────────────────────────────────────────────────────────────────────────────
def view_notes(
    parent: tk.Widget,
    db: models.PatientDatabase
) -> None:
    # Prompt for Patient ID
    pid = simpledialog.askstring("Patient ID", "Enter Patient ID:", parent=parent)
    if not pid:
        return

    rec = db.get_patient(pid.strip())
    if not rec:
        messagebox.showerror("Error", f"No records found for patient {pid}", parent=parent)
        return

    # Prompt for date
    ds = prompt_date(parent, "Enter date to view notes")
    if ds is None:
        return

    try:
        target_date = datetime.strptime(ds.strip(), "%m/%d/%Y").date()
    except ValueError:
        messagebox.showerror("Invalid Date", f"Could not parse date '{ds}'. Use MM/DD/YYYY format.", parent=parent)
        return

    notes_text = []
    for vid, visit in rec.visits.items():
        visit_time = visit.data.get("Visit_time", "").strip()

        try:
            month, day, year = map(int, visit_time.split("/"))
            visit_date = date(year, month, day)
        except (ValueError, Exception):
            continue

        if visit_date == target_date and visit.notes:
            note_type = visit.data.get("Note_type", "N/A")
            for note in visit.notes:
                notes_text.append(
                    f"Visit ID: {vid}\n"
                    f"  Note ID: {note.get('Note_ID', 'N/A')}\n"
                    f"  Type:    {note_type}\n"
                    f"  Text:    {note.get('Note_text', '').strip()}\n"
                )

    if not notes_text:
        messagebox.showinfo("No Notes", f"No notes found for {pid} on {ds}.", parent=parent)
        return

    # Show results in scrollable window
    top = Toplevel(parent)
    top.title(f"Notes for {pid} on {ds}")

    scrollbar = Scrollbar(top)
    scrollbar.pack(side=RIGHT, fill=Y)

    text_widget = Text(top, wrap="word", yscrollcommand=scrollbar.set, width=80, height=25)
    text_widget.insert(END, "\n\n".join(notes_text))
    text_widget.config(state="disabled")
    text_widget.pack(padx=10, pady=10)

    scrollbar.config(command=text_widget.yview)
# ──────────────────────────────────────────────────────────────────────────────
def clinician_nurse(
    parent: tk.Widget,
    db: models.PatientDatabase,
    data_file: str,
    notes_file: str,
    data_fieldnames: List[str],
    notes_fieldnames: List[str]
) -> None:
    win = tk.Toplevel(parent)
    win.title("Clinician / Nurse Menu")
    win.grab_set()

    actions: List[Tuple[str, Callable]] = [
        ("Add Patient",     add_patient),
        ("Remove Patient",  remove_patient),
        ("Retrieve Patient",retrieve_patient),
        ("Count Visits",    count_visits),
        ("View Notes",      view_notes),
        ("Close",           win.destroy),
    ]
    for i, (label, func) in enumerate(actions):
        btn = tk.Button(
            win,
            text=label,
            width=20,
            command=(func if func is win.destroy else
                     lambda f=func: _wrap(f, parent, db, data_file, notes_file,
                                          data_fieldnames, notes_fieldnames))
        )
        btn.grid(row=i, column=0, padx=10, pady=5)

def _wrap(
    func: Callable,
    parent, db, data_file, notes_file, data_fieldnames, notes_fieldnames
):
    """Helper to call a GUI handler with either 2 or 6 arguments."""
    try:
        func(parent, db, data_file, notes_file, data_fieldnames, notes_fieldnames)
    except TypeError:
        func(parent, db)

# ──────────────────────────────────────────────────────────────────────────────

def record_event(username: str, role: str, event: str, action: str = ""):
    """
    Append a row to USAGE_FILE. Creates the file with header if needed.
    event: e.g. "login_success", "login_failed", "action"
    action: name of the action (only for event="action")
    """
    # ensure file exists with header
    try:
        with open(USAGE_FILE, "x", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=USAGE_FIELDS)
            writer.writeheader()
    except FileExistsError:
        pass

    # append the event
    with open(USAGE_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=USAGE_FIELDS)
        writer.writerow({
            "username":  username,
            "role":      role,
            "timestamp": datetime.now().isoformat(),
            "event":     event,
            "action":    action
        })