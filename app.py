"""Mamourart Transport Automation - complete mission dashboard."""

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

        self.root.geometry("1280x700")
        self.root.minsize(1100, 600)

        self.root.configure(
            bg="#f3f4f6"
        )

        self.create_header()
        self.create_stats()
        self.create_table()
        self.create_buttons()
        self.create_status_bar()

        self.refresh_table()

    def create_header(self):
        header = tk.Frame(
            self.root,
            bg="#f3f4f6",
        )

        header.pack(
            fill="x",
            pady=(18, 8),
        )

        tk.Label(
            header,
            text="Mamourart Transport Automation",
            font=("Segoe UI", 22, "bold"),
            bg="#f3f4f6",
        ).pack()

        tk.Label(
            header,
            text=(
                "Driver Assignment & "
                "Human Approval Dashboard"
            ),
            font=("Segoe UI", 11),
            bg="#f3f4f6",
            fg="#555555",
        ).pack(
            pady=(4, 0)
        )

    def create_stats(self):
        stats_frame = tk.Frame(
            self.root,
            bg="#f3f4f6",
        )

        stats_frame.pack(
            fill="x",
            padx=25,
            pady=(10, 15),
        )

        for column in range(4):
            stats_frame.grid_columnconfigure(
                column,
                weight=1,
            )

        self.total_value = self.create_stat_card(
            stats_frame,
            0,
            "Total Missions",
        )

        self.pending_value = self.create_stat_card(
            stats_frame,
            1,
            "Pending",
        )

        self.approved_value = self.create_stat_card(
            stats_frame,
            2,
            "Approved",
        )

        self.review_value = self.create_stat_card(
            stats_frame,
            3,
            "Needs Review",
        )

    def create_stat_card(
        self,
        parent,
        column,
        title,
    ):
        card = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid",
        )

        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=8,
            ipady=8,
        )

        value_label = tk.Label(
            card,
            text="0",
            font=("Segoe UI", 22, "bold"),
            bg="white",
        )

        value_label.pack(
            pady=(8, 0)
        )

        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 10),
            bg="white",
            fg="#555555",
        ).pack(
            pady=(0, 8)
        )

        return value_label

    def create_table(self):
        columns = (
            "reference",
            "date",
            "pickup",
            "delivery",
            "driver",
            "reason",
            "distance",
            "status",
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

        headings = {
            "reference": "Mission",
            "date": "Date",
            "pickup": "Pickup",
            "delivery": "Delivery",
            "driver": "Driver",
            "reason": "Assignment Reason",
            "distance": "Distance (km)",
            "status": "Status",
            "rejected": "Rejected Drivers",
        }

        for column, title in headings.items():
            self.tree.heading(
                column,
                text=title,
            )

        self.tree.column(
            "reference",
            width=85,
            anchor="center",
        )

        self.tree.column(
            "date",
            width=105,
            anchor="center",
        )

        self.tree.column(
            "pickup",
            width=95,
            anchor="center",
        )

        self.tree.column(
            "delivery",
            width=95,
            anchor="center",
        )

        self.tree.column(
            "driver",
            width=115,
            anchor="center",
        )

        self.tree.column(
            "reason",
            width=210,
        )

        self.tree.column(
            "distance",
            width=100,
            anchor="center",
        )

        self.tree.column(
            "status",
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

        # Colours for mission status
        self.tree.tag_configure(
            "assigned",
            background="#dbeafe",
        )

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

        self.tree.tag_configure(
            "review",
            background="#ffe4c7",
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
        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 10),
            bg="#f3f4f6",
            fg="#444444",
        )

        self.status_label.pack(
            pady=(0, 15)
        )

    def update_stats(
        self,
        missions,
        approvals,
    ):
        total_missions = len(
            missions
        )

        pending = sum(
            1
            for row in approvals
            if row.get(
                "decision",
                "",
            ).strip().casefold()
            == "pending"
        )

        approved = sum(
            1
            for row in missions
            if row.get(
                "status",
                "",
            ).strip().casefold()
            == "approved"
        )

        needs_review = sum(
            1
            for row in missions
            if row.get(
                "status",
                "",
            ).strip().casefold()
            == "needs review"
        )

        self.total_value.config(
            text=str(total_missions)
        )

        self.pending_value.config(
            text=str(pending)
        )

        self.approved_value.config(
            text=str(approved)
        )

        self.review_value.config(
            text=str(needs_review)
        )

    def get_display_status(
        self,
        mission,
        approval,
    ):
        if approval:
            decision = approval.get(
                "decision",
                "",
            ).strip()

            if decision.casefold() == "pending":
                return "Pending"

            if decision.casefold() == "approved":
                return "Approved"

            if decision.casefold() == "rejected":
                return "Rejected"

        return mission.get(
            "status",
            "",
        )

    def get_status_tag(
        self,
        status,
    ):
        status_lower = (
            status.strip().casefold()
        )

        if status_lower == "assigned":
            return "assigned"

        if status_lower == "pending":
            return "pending"

        if status_lower == "approved":
            return "approved"

        if status_lower == "rejected":
            return "rejected"

        if status_lower == "needs review":
            return "review"

        return ""

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        missions = load_csv(
            MISSIONS_FILE
        )

        approvals = load_csv(
            APPROVALS_FILE
        )

        approvals_by_reference = {
            row.get(
                "reference",
                "",
            ): row
            for row in approvals
        }

        for mission in missions:
            reference = mission.get(
                "reference",
                "",
            )

            approval = approvals_by_reference.get(
                reference
            )

            status = self.get_display_status(
                mission,
                approval,
            )

            tag = self.get_status_tag(
                status
            )

            if approval:
                driver = approval.get(
                    "proposed_driver",
                    "",
                )

                reason = approval.get(
                    "reason",
                    "",
                )

                distance = approval.get(
                    "distance_km",
                    "",
                )

                rejected = approval.get(
                    "rejected_drivers",
                    "",
                )

            else:
                driver = mission.get(
                    "driver",
                    "",
                )

                reason = (
                    "Driver provided in email"
                    if driver
                    else ""
                )

                distance = mission.get(
                    "distance_km",
                    "",
                )

                rejected = ""

            # Approved missions use final driver
            if status.casefold() == "approved":
                driver = mission.get(
                    "driver",
                    "",
                ) or driver

            self.tree.insert(
                "",
                "end",
                values=(
                    reference,
                    mission.get(
                        "date",
                        "",
                    ),
                    mission.get(
                        "pickup",
                        "",
                    ),
                    mission.get(
                        "delivery",
                        "",
                    ),
                    driver,
                    reason,
                    distance,
                    status,
                    rejected,
                ),
                tags=(tag,),
            )

        self.update_stats(
            missions,
            approvals,
        )

        self.status_label.config(
            text=(
                f"Showing {len(missions)} "
                f"transport mission(s)"
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
        success = (
            self.run_assignment_engine()
        )

        if success:
            self.refresh_table()

            messagebox.showinfo(
                "Automation Completed",
                (
                    "Transport automation "
                    "completed successfully."
                ),
            )

    def change_decision(
        self,
        decision,
    ):
        selected = (
            self.tree.selection()
        )

        if not selected:
            messagebox.showwarning(
                "No Mission Selected",
                (
                    "Please select "
                    "a mission first."
                ),
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
                row[
                    "decision"
                ] = decision

                found = True
                break

        if not found:
            messagebox.showwarning(
                "No Approval Required",
                (
                    f"Mission {reference} "
                    "does not have an approval record.\n\n"
                    "The driver was already provided "
                    "in the original transport email."
                ),
            )

            return

        save_approvals(
            rows
        )

        success = (
            self.run_assignment_engine()
        )

        self.refresh_table()

        if not success:
            return

        if decision == "Rejected":
            messagebox.showinfo(
                "Driver Rejected",
                (
                    f"Mission {reference}\n\n"
                    "Driver rejected.\n"
                    "The system searched "
                    "automatically for "
                    "another available driver."
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
                (
                    "missions.csv "
                    "does not exist yet."
                ),
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

    TransportApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()