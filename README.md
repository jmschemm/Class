# Patient Visit Management App

A desktop GUI application for managing and visualizing patient visit data with role-based access and usage logging.

---

## 1. How to Run the Program

This is a Tkinter-based desktop app. The entry point is `main.py`.

### Prerequisites

- Python 3.8+  
- Git (optional, for cloning)

### Option A: Conda (recommended)

1. **Save** the provided `environment.yaml` alongside `main.py`, `functions.py`, etc.  
2. **Create** the environment and install dependencies:
    ```bash
    conda env create -f environment.yaml
    ```
3. **Activate** the environment:
    ```bash
    conda activate ChartEnv
    ```
4. **Launch** the app:
    ```bash
    python app.py
    ```

### Option B: Pip

1. **Install** dependencies from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
2. **Run** the app:
    ```bash
    python app.py
    ```

## 2. Program Overview

- **Login & Roles**  
  Secure credential checks for Admin, Manager, Clinician, and Nurse accounts.

- **Patient Data Retrieval**  
  Button-driven dialogs to fetch fields: visit times, departments, race, gender, ethnicity, age, ZIP codes, insurance, chief complaints.

- **Clinical Notes**  
  View notes by patient ID and date in a scrollable popup.

- **Temporal Trends**  
  Aggregate and plot visit counts by year (or month) in a table plus line chart.

- **Usage Logging**  
  All user actions (logins, field requests, plot views) are appended to `usage_log.csv` for auditing.

## 3. File Structure
```
Final-Project/
├── app.py               # Main entry point
├── functions.py         # GUI callbacks & logging
├── classes.py           # Data models & database interface
├── environment.yaml     # Conda environment spec
├── requirements.txt     # pip dependencies
├── README.md            # This file
└── usage_log.csv        # Auto-generated usage log
```
## 4. Environment Specification

### `environment.yaml`
```yaml
name: ChartEnv
channels:
  - defaults
dependencies:
  - python=3.10       # or 3.9+
  - tk                # ensures tkinter support
  - matplotlib        # for plotting
```

### `requirements.txt`
```text
matplotlib
```
### 5. Important Notes

- **Date format** must be `MM/DD/YYYY` for visit times and notes.  
- **Logging:** `usage_log.csv` is created next to `functions.py` and records:  
  `username, role, timestamp, event, action`.  
- **Extending the app:**  
  - To add additional data columns, update `field_map` in `functions.py` and ensure `classes.PatientDatabase` supports the key.  
  - To change aggregation granularity, modify `show_temporal_trends` in `functions.py`.  
- **Troubleshooting:**  
  - If the GUI doesn’t launch, confirm you’re in the correct environment.  
  - On Linux/macOS, install system Tk if you see errors importing `tkinter`.  
