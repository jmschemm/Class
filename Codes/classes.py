"""Data models for patient records and database management."""

from __future__ import annotations
import csv
from os import path
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict
import csv
from hmac import compare_digest

# Type aliases
VisitData  = Dict[str, Any]
VisitNotes = Dict[str, Any]


@dataclass
class VisitRecord:
    """
    Holds both the core visit data and _all_ associated notes.

    Attributes:
      data: All non-note fields (e.g., Visit_time, Department, etc.).
      notes: List of note dicts (each with Note_ID, Note_text).
    """
    data: VisitData
    notes: List[VisitNotes] = field(default_factory=list)

@dataclass
class PatientRecord:
    """
    Represents a single patient and all of their visits.

    Attributes:
      patient_id: Unique identifier for the patient.
      visits: Maps each visit_id to a VisitRecord.
    """
    patient_id: str
    visits: Dict[str, VisitRecord] = field(default_factory=dict)

    def add_visit(
        self,
        visit_id: str,
        data: VisitData,
        notes: Optional[VisitNotes] = None
    ) -> None:
        """
        Create or update a VisitRecord.
        Merges incoming data into .data and appends notes to the list.
        """
        if visit_id not in self.visits:
            self.visits[visit_id] = VisitRecord(data={}, notes=[])

        # Merge new data fields
        self.visits[visit_id].data.update(data)

        # Append note dict so past notes persist
        if notes:
            self.visits[visit_id].notes.append(notes)

    def add_notes_to_visit(
        self,
        visit_id: str,
        notes: VisitNotes
    ) -> bool:
        """
        Append notes to an existing visit.

        Returns True if visit exists and was updated, False otherwise.
        """
        record = self.visits.get(visit_id)
        if not record:
            return False
        record.notes.append(notes)
        return True

@dataclass
class PatientDatabase:
    """
    In-memory database of PatientRecord objects, keyed by patient_id.

    Contains methods for loading/saving CSVs, querying, and counting visits.
    """
    patients: Dict[str, PatientRecord] = field(default_factory=dict)

    def load_data(self, file_path: str) -> None:
        """
        Load patient & visit data from CSV (excluding notes).
        Expects 'Patient_ID', 'Visit_ID', and any visit-related fields except notes.
        """

        if not path.exists(file_path):
            return

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("Patient_ID")
                vid = row.get("Visit_ID")
                if not pid or not vid:
                    continue

                data = {
                    k: v for k, v in row.items() 
                    if k not in ("Patient_ID", "Visit_ID")
                }

                rec = self.patients.setdefault(pid, PatientRecord(pid))
                rec.add_visit(visit_id=vid, data=data)

    
    def load_notes_data(self, file_path: str) -> None:
        """
        Load existing notes data from a CSV file into the PatientDatabase.
        """

        if not path.exists(file_path):
            return

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("Patient_ID")
                vid = row.get("Visit_ID")
                note_id = row.get("Note_ID")
                note_text = row.get("Note_text")

                if not (pid and vid and note_id):
                    continue  # Essential fields must be present

                notes = {
                    "Note_ID": note_id,
                    "Note_text": note_text
                }

                patient = self.patients.setdefault(pid, PatientRecord(pid))
                visit = patient.visits.setdefault(vid, VisitRecord(data={}))
                visit.notes.append(notes)


    def get_visit_data_rows(self) -> List[Dict[str, Any]]:
        """
        Get flat rows of visit data (no notes) for CSV export.
        """
        rows: List[Dict[str, Any]] = []
        for pr in self.patients.values():
            for vid, vr in pr.visits.items():
                rows.append({
                    "Patient_ID": pr.patient_id,
                    "Visit_ID":   vid,
                    **vr.data
                })
        return rows

    def get_visit_notes_rows(self) -> List[Dict[str, Any]]:
        """
        Get flat rows of visit notes (no data) for CSV export.
        """
        rows: List[Dict[str, Any]] = []
        for pr in self.patients.values():
            for vid, vr in pr.visits.items():
                for note in vr.notes:
                    rows.append({
                        "Patient_ID": pr.patient_id,
                        "Visit_ID":   vid,
                        **note
                    })
        return rows

    def save_visit_data(
        self,
        file_path: str,
        fieldnames: List[str]
    ) -> None:
        """
        Write visit data rows (no notes) to CSV.
        """
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.get_visit_data_rows())

    def save_visit_notes(
        self,
        file_path: str,
    ) -> None:
        """
        Write visit notes rows (no data) to CSV.
        """

        # Define the fieldnames explicitly
        fieldnames = ['Patient_ID', 'Visit_ID', 'Note_ID', 'Note_text']

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for patient in self.patients.values():
                for visit_id, visit in patient.visits.items():
                    for note in visit.notes:
                        writer.writerow({
                            "Patient_ID": patient.patient_id,
                            "Visit_ID": visit_id,
                            **note
                        })

    def list_patient_ids(self) -> List[str]:
        """Return all patient IDs."""
        return list(self.patients.keys())

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        """Retrieve a PatientRecord or None if not found."""
        return self.patients.get(patient_id)

    def remove_patient(self, patient_id: str) -> bool:
        """Delete a patient; return True if removed."""
        return self.patients.pop(patient_id, None) is not None

    def retrieve_patient_info(
        self,
        patient_id: str,
        info_key: str
    ) -> Optional[List[Any]]:
        """
        Return a list of values for a given field across all visits and notes.
        """
        record = self.get_patient(patient_id)
        if not record:
            return None
        result: List[Any] = []
        for vr in record.visits.values():
            if info_key in vr.data:
                result.append(vr.data[info_key])
            for note in vr.notes:
                if info_key in note:
                    result.append(note[info_key])
        return result

    def count_visits_in_day(self, day_str: str) -> Optional[int]:
        """
        Count visits on a specific date (M/D/YYYY).
        """

        try:
            target = datetime.strptime(day_str.strip(), "%m/%d/%Y").date()
        except ValueError:
            return None

        total = 0
        for pr in self.patients.values():
            for vr in pr.visits.values():
                vt = vr.data.get("Visit_time", "").strip()
                try:
                    visit_date = datetime.strptime(vt, "%m/%d/%Y").date()
                except ValueError:
                    continue
                if visit_date == target:
                    total += 1
        return total

class User(ABC):
    """
    Abstract base for all user types.
    """
    def __init__(self, username: str, credential: Credential) -> None:
        self.username: str = username
        self.role: str = credential['role']
    
    @abstractmethod
    def get_actions(self) -> List[str]:
        """List of commands this user can execute."""
        ...

    def can_execute(self, cmd: str) -> bool:
        return cmd in self.get_actions()

    def __repr__(self) -> str:
        return f"<User username={self.username!r} role={self.role!r}>"


class AdminUser(User):
    def get_actions(self) -> List[str]:
        return ['count_visits']


class ManagerUser(User):
    def get_actions(self) -> List[str]:
        return ['show_temporal_trends']


class ClinicianUser(User):
    def get_actions(self) -> List[str]:
        return ['add_patient', 'remove_patient', 'retrieve_patient', 'count_visits', 'view_note']


class NurseUser(ClinicianUser):
    pass

class Credential(TypedDict):
    password: str
    role: str


class Credential(TypedDict):
    password: str
    role:     str

class CredentialsManager:
    """
    Load and authenticate users from a credentials CSV.
    Automatically handles extra columns (e.g. an index column)
    and normalizes usernames to lowercase.
    """

    def __init__(self, file_path: str, delimiter: str = ','):
        self.file_path = file_path
        self.delimiter = delimiter
        self.credentials: Dict[str, Credential] = {}
        self._load()

    def _load(self):
        with open(self.file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            # ensure required columns
            required = {"username", "password", "role"}
            if not required.issubset(reader.fieldnames or []):
                missing = required - set(reader.fieldnames or [])
                raise ValueError(f"Missing columns in credentials file: {missing}")
            for row in reader:
                user = row["username"].strip().lower()
                pwd  = row["password"].strip()
                role = row["role"].strip()
                if user and pwd and role:
                    self.credentials[user] = {"password": pwd, "role": role}

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Timing-safe check of username & password.
        Returns the role on success, or None on failure.
        """
        key = username.strip().lower()
        cred = self.credentials.get(key)
        if cred and compare_digest(cred["password"], password):
            return cred["role"]
        return None