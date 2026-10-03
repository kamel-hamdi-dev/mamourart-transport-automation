"""Mamourart Transport Automation - approval interface."""

from pathlib import Path
import csv
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox


BASE_DIR = Path(__file__).parent
APPROVALS_FILE = BASE_DIR / "approvals.csv"
MAIN_FILE = BASE_DIR / "main.py"

FIELDS = [
    "reference",
    "proposed_driver",
    "reason",
    "distance_km",
    "decision",
    "rejected_drivers",
]


def load_approvals():
    if not APPROVALS_FILE.exists():
        return []

    with APPROVALS_FILE.open(
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
            fieldnames=FIELDS,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field: row.get(field, "")
                    for field in FIELDS
                }
            )


class ApprovalApp:
    def __init__(self, root):
        self.root = root

        self.root.title(
            "Mamourart Transport Automation"
        )

        self.root.geometry("950x520")
        self.root.minsize(850, 450)

        title = ttk.Label(
            root,
            text="Transport Mission Approval",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(20, 5))

        subtitle = ttk.Label(
            root,
            text=(
                "Review proposed driver assignments "
                "before final approval"
            ),
            font=("Segoe UI", 10),
        )
        subtitle.pack(pady=(0, 20))

        columns = (
            "reference",
            "driver",
            "reason",
            "distance",
            "decision",
            "rejected",
        )

        self.tree = ttk.Treeview(
            root,
            columns=columns,
            show="headings",
            height=12,
        )

        self.tree.heading(
            "reference",
            text="Mission",
        )
        self.tree.heading(
            "driver",
            text="Proposed Driver",
        )
        self.tree.heading(
            "reason",
            text="Reason",
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
            width=100,
            anchor="center",
        )

        self.tree.column(
            "driver",
            width=130,
            anchor="center",
        )

        self.tree.column(
            "reason",
            width=230,
        )

        self.tree.column(
            "distance",
            width=110,
            anchor="center",
        )

        self.tree.column(
            "decision",
            width=110,
            anchor="center",
        )

        self.tree.column(
            "rejected",
            width=140,
            anchor="center",
        )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=10,
        )

        buttons = ttk.Frame(root)
        buttons.pack(pady=15)

        approve_button = ttk.Button(
            buttons,
            text="Approve",
            command=lambda: self.change_decision(
                "Approved"
            ),
        )

        approve_button.grid(
            row=0,
            column=0,
            padx=10,
        )

        reject_button = ttk.Button(
            buttons,
            text="Reject",
            command=lambda: self.change_decision(
                "Rejected"
            ),
        )

        reject_button.grid(
            row=0,
            column=1,
            padx=10,
        )

        refresh_button = ttk.Button(
            buttons,
            text="Refresh",
            command=self.refresh_table,
        )

        refresh_button.grid(
            row=0,
            column=2,
            padx=10,
        )

        self.status_label = ttk.Label(
            root,
            text="",
            font=("Segoe UI", 10),
        )

        self.status_label.pack(
            pady=(0, 15)
        )

        self.refresh_table()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = load_approvals()

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.get(
                        "reference",
                        "",
                    ),
                    row.get(
                        "proposed_driver",
                        "",
                    ),
                    row.get(
                        "reason",
                        "",
                    ),
                    row.get(
                        "distance_km",
                        "",
                    ),
                    row.get(
                        "decision",
                        "",
                    ),
                    row.get(
                        "rejected_drivers",
                        "",
                    ),
                ),
            )

        self.status_label.config(
            text=f"{len(rows)} approval record(s)"
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
                    "Automation error",
                    result.stderr
                    or "main.py failed.",
                )
                return False

            return True

        except Exception as error:
            messagebox.showerror(
                "Automation error",
                str(error),
            )

            return False

    def change_decision(self, decision):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No mission selected",
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

        rows = load_approvals()

        found = False

        for row in rows:
            if (
                row.get(
                    "reference",
                    ""
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
                "Driver rejected",
                (
                    f"{reference}\n\n"
                    "The driver was rejected.\n"
                    "The system searched "
                    "automatically for an alternative."
                ),
            )

        else:
            messagebox.showinfo(
                "Assignment approved",
                (
                    f"{reference}\n\n"
                    "The driver assignment "
                    "was approved."
                ),
            )


def main():
    root = tk.Tk()
    ApprovalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()