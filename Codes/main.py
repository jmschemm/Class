import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os

import models
import handlers


class PatientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Patient Management System")

        # inside PatientApp.__init__ before creating the StringVar:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_creds = os.path.join(base_dir, "Credentials.csv")
        default_notes = os.path.join(base_dir, "Notes.csv")
        default_data  = os.path.join(base_dir, "Patient_data.csv")

        # Default file paths
        self.data_file  = tk.StringVar(value=default_data)
        self.notes_file = tk.StringVar(value=default_notes)
        self.users_file = tk.StringVar(value=default_creds)

        # Username / Password labels & entries
        tk.Label(root, text="Username:").grid(row=0, column=0, sticky="e")
        tk.Label(root, text="Password:").grid(row=1, column=0, sticky="e")
        self.username_entry = tk.Entry(root)
        self.password_entry = tk.Entry(root, show="*")
        self.username_entry.grid(row=0, column=1, padx=5, pady=2)
        self.password_entry.grid(row=1, column=1, padx=5, pady=2)

        # Login button
        tk.Button(root, text="Login", command=self.authenticate)\
            .grid(row=2, column=0, columnspan=2, pady=10)

    def authenticate(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        try:
            cm = models.CredentialsManager(self.users_file.get(), delimiter=",")
        except (FileNotFoundError, ValueError) as e:
            messagebox.showerror("Error", str(e), parent=self.root)
            handlers.record_event(username, "", "login_failed", action="load_credentials_error")
            return

        # Authenticate
        role = cm.authenticate(username, password)
        if not role:
            messagebox.showerror("Login Failed", "Invalid credentials.", parent=self.root)
            handlers.record_event(username, "", "login_failed")
            return

        # successful login
        handlers.record_event(username, role, "login_success")
        self.dispatch_user(username, role.lower(), cm.credentials)

    def dispatch_user(self, username, role, credentials):
        ROLE_MAP = {
            "management": models.ManagerUser,
            "admin":      models.AdminUser,
            "clinician":  models.ClinicianUser,
            "nurse":      models.NurseUser,
        }
        cls = ROLE_MAP.get(role)
        if not cls:
            messagebox.showerror("Error", f"Unsupported role '{role}'", parent=self.root)
            handlers.record_event(username, role, "login_failed", action="unsupported_role")
            return

        # instantiate user
        self.user_obj = cls(username, credentials[username.lower()])

        # Load data
        self.db = models.PatientDatabase()
        self.db.load_data(self.data_file.get())
        self.db.load_notes_data(self.notes_file.get())

        # Store fieldnames once
        self.data_fieldnames = [
            "Patient_ID","Visit_ID","Visit_time","Visit_department",
            "Race","Gender","Ethnicity","Age","Zip_code",
            "Insurance","Chief_complaint","Note_ID","Note_type"
        ]
        self.notes_fieldnames = ["Patient_ID","Visit_ID","Note_ID","Note_text"]

        # Show action buttons
        self.show_actions()

    def show_actions(self):
        # Clear login widgets
        for w in self.root.winfo_children():
            w.destroy()

        tk.Label(
            self.root,
            text=f"Welcome, {self.user_obj.username} ({self.user_obj.role})"
        ).grid(row=0, column=0, columnspan=2, pady=10)

        if isinstance(self.user_obj, (models.ClinicianUser, models.NurseUser)):
            actions = self.user_obj.get_actions()
        else:
            actions = self.user_obj.get_actions()

        # Create buttons for each action
        for i, action in enumerate(actions, start=1):
            btn = tk.Button(
                self.root,
                text=action.replace("_", " ").title(),
                command=lambda a=action: self.execute_action(a)
            )
            btn.grid(row=i, column=0, sticky="we", padx=10, pady=5)

        # Add Exit button after all actions
        exit_button = tk.Button(
            self.root,
            text="Exit",
            command=self.root.destroy
        )
        exit_button.grid(row=len(actions) + 1, column=0, sticky="we", padx=10, pady=10)

    def execute_action(self, action: str):
        # log the attempted action
        handlers.record_event(self.user_obj.username, self.user_obj.role, "action", action)

        if action == "add_patient":
            handlers.add_patient(
                parent=self.root,
                db=self.db,
                data_file=self.data_file.get(),
                notes_file=self.notes_file.get(),
                data_fieldnames=self.data_fieldnames,
                notes_fieldnames=self.notes_fieldnames
            )
        elif action == "remove_patient":
            handlers.remove_patient(
                parent=self.root,
                db=self.db,
                data_file=self.data_file.get(),
                notes_file=self.notes_file.get(),
                data_fieldnames=self.data_fieldnames,
                notes_fieldnames=self.notes_fieldnames
            )
        elif action == "retrieve_patient":
            handlers.retrieve_patient(
                parent=self.root,
                db=self.db
            )
        elif action == "count_visits":
            handlers.count_visits(
                parent=self.root,
                db=self.db
            )
        elif action == "view_note":
            handlers.view_notes(
                parent=self.root,
                db=self.db
            )
        elif action == "show_temporal_trends":
            handlers.show_temporal_trends(
                parent=self.root,
                db=self.db
            )
        else:
            messagebox.showerror(
                "Error",
                f"No handler for action '{action}'.",
                parent=self.root
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = PatientApp(root)
    root.mainloop()