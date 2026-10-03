"""Mamourart Transport Automation - professional desktop interface."""

from pathlib import Path
import csv
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox


BASE_DIR = Path(__file__).parent

APPROVALS_FILE = BASE_DIR / "approvals.csv"
MISSIONS_FILE = BASE_DIR / "missions.csv"
MAIN_FILE = BASE_DIR / "main.py"

APPROVAL_FIELDS = [
    "reference",
    "proposed_driver",
    "reason",
    "distance_km",
    "decision",
    "rejected_drivers",
]


def load_csv(file_path):
    if not file_path.exists():
        return []

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def save_approvals(rows):
    with APPROVALS_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=APPROVAL_FIELDS,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field: row.get(field, "")
                    for field in APPROVAL_FIELDS
                }
            )


class TransportApp:
    def __init__(self, root):
        self.root = root

        self.root.title(
            "Mamourart Transport Automation"
        )

        self.root.geometry("1200x620")
        self.root.minsize(1050, 520)

        self.create_header()
        self.create_table()
        self.create_buttons()
        self.create_status_bar()

        self.refresh_table()

    def create_header(self):
        title = ttk.Label(
            self.root,
            text="Mamourart Transport Automation",
            font=("Segoe UI", 20, "bold"),
        )

        title.pack(
            pady=(20, 5)
        )

        subtitle = ttk.Label(
            self.root,
            text=(
                "Driver Assignment & Human Approval Dashboard"
            ),
            font=("Segoe UI", 11),
        )

        subtitle.pack(
            pady=(0, 18)
        )

    def create_table(self):
        columns = (
            "reference",
            "pickup",
            "delivery",
            "driver",
            "reason",
            "distance",
            "decision",
            "rejected",
        )

        frame = ttk.Frame(
            self.root
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=20,
        )

        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
        )

        self.tree.heading(
            "reference",
            text="Mission",
        )

        self.tree.heading(
            "pickup",
            text="Pickup",
        )

        self.tree.heading(
            "delivery",
            text="Delivery",
        )

        self.tree.heading(
            "driver",
            text="Proposed Driver",
        )

        self.tree.heading(
            "reason",
            text="Assignment Reason",
        )

        self.tree.heading(
            "distance",
            text="Distance (km)",
        )

        self.tree.heading(
            "decision",
            text="Decision",
        )

        self.tree.heading(
            "rejected",
            text="Rejected Drivers",
        )

        self.tree.column(
            "reference",
            width=90,
            anchor="center",
        )

        self.tree.column(
            "pickup",
            width=100,
            anchor="center",
        )

        self.tree.column(
            "delivery",
            width=100,
            anchor="center",
        )

        self.tree.column(
            "driver",
            width=120,
            anchor="center",
        )

        self.tree.column(
            "reason",
            width=220,
        )

        self.tree.column(
            "distance",
            width=100,
            anchor="center",
        )

        self.tree.column(
            "decision",
            width=100,
            anchor="center",
        )

        self.tree.column(
            "rejected",
            width=160,
            anchor="center",
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.tree.yview,
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        # Status colours
        self.tree.tag_configure(
            "pending",
            background="#fff4cc",
        )

        self.tree.tag_configure(
            "approved",
            background="#d9f7df",
        )

        self.tree.tag_configure(
            "rejected",
            background="#ffd9d9",
        )

    def create_buttons(self):
        buttons = ttk.Frame(
            self.root
        )

        buttons.pack(
            pady=18
        )

        ttk.Button(
            buttons,
            text="Approve",
            command=lambda: self.change_decision(
                "Approved"
            ),
        ).grid(
            row=0,
            column=0,
            padx=7,
        )

        ttk.Button(
            buttons,
            text="Reject",
            command=lambda: self.change_decision(
                "Rejected"
            ),
        ).grid(
            row=0,
            column=1,
            padx=7,
        )

        ttk.Button(
            buttons,
            text="Run Automation",
            command=self.run_automation_button,
        ).grid(
            row=0,
            column=2,
            padx=7,
        )

        ttk.Button(
            buttons,
            text="Open Missions",
            command=self.open_missions,
        ).grid(
            row=0,
            column=3,
            padx=7,
        )

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.refresh_table,
        ).grid(
            row=0,
            column=4,
            padx=7,
        )

    def create_status_bar(self):
        self.status_label = ttk.Label(
            self.root,
            text="",
            font=("Segoe UI", 10),
        )

        self.status_label.pack(
            pady=(0, 15)
        )

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        approvals = load_csv(
            APPROVALS_FILE
        )

        missions = load_csv(
            MISSIONS_FILE
        )

        missions_by_reference = {
            row.get("reference", ""): row
            for row in missions
        }

        pending_count = 0
        approved_count = 0

        for approval in approvals:
            reference = approval.get(
                "reference",
                "",
            )

            mission = missions_by_reference.get(
                reference,
                {},
            )

            decision = approval.get(
                "decision",
                "",
            )

            decision_lower = (
                decision.strip().casefold()
            )

            if decision_lower == "pending":
                tag = "pending"
                pending_count += 1

            elif decision_lower == "approved":
                tag = "approved"
                approved_count += 1

            elif decision_lower == "rejected":
                tag = "rejected"

            else:
                tag = ""

            self.tree.insert(
                "",
                "end",
                values=(
                    reference,
                    mission.get(
                        "pickup",
                        "",
                    ),
                    mission.get(
                        "delivery",
                        "",
                    ),
                    approval.get(
                        "proposed_driver",
                        "",
                    ),
                    approval.get(
                        "reason",
                        "",
                    ),
                    approval.get(
                        "distance_km",
                        "",
                    ),
                    decision,
                    approval.get(
                        "rejected_drivers",
                        "",
                    ),
                ),
                tags=(tag,),
            )

        self.status_label.config(
            text=(
                f"Total: {len(approvals)}   |   "
                f"Pending: {pending_count}   |   "
                f"Approved: {approved_count}"
            )
        )

    def run_assignment_engine(self):
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(MAIN_FILE),
                ],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                messagebox.showerror(
                    "Automation Error",
                    result.stderr
                    or "main.py failed.",
                )

                return False

            return True

        except Exception as error:
            messagebox.showerror(
                "Automation Error",
                str(error),
            )

            return False

    def run_automation_button(self):
        success = self.run_assignment_engine()

        if success:
            self.refresh_table()

            messagebox.showinfo(
                "Automation completed",
                (
                    "Transport automation "
                    "completed successfully."
                ),
            )

    def change_decision(self, decision):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Mission Selected",
                "Please select a mission first.",
            )

            return

        item = self.tree.item(
            selected[0]
        )

        values = item["values"]

        if not values:
            return

        reference = str(
            values[0]
        )

        rows = load_csv(
            APPROVALS_FILE
        )

        found = False

        for row in rows:
            if (
                row.get(
                    "reference",
                    "",
                ).strip()
                == reference.strip()
            ):
                row["decision"] = decision
                found = True
                break

        if not found:
            messagebox.showerror(
                "Error",
                "Mission not found.",
            )

            return

        save_approvals(rows)

        success = self.run_assignment_engine()

        self.refresh_table()

        if not success:
            return

        if decision == "Rejected":
            messagebox.showinfo(
                "Driver Rejected",
                (
                    f"Mission {reference}\n\n"
                    "Driver rejected.\n"
                    "The system searched automatically "
                    "for another available driver."
                ),
            )

        else:
            messagebox.showinfo(
                "Assignment Approved",
                (
                    f"Mission {reference}\n\n"
                    "Driver assignment approved."
                ),
            )

    def open_missions(self):
        if not MISSIONS_FILE.exists():
            messagebox.showwarning(
                "File Not Found",
                "missions.csv does not exist yet.",
            )

            return

        try:
            os.startfile(
                MISSIONS_FILE
            )

        except Exception as error:
            messagebox.showerror(
                "Open File Error",
                str(error),
            )


def main():
    root = tk.Tk()

    TransportApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()