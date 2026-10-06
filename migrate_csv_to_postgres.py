import csv
import re
from pathlib import Path

from database import get_connection


BASE_DIR = Path(__file__).resolve().parent

DRIVERS_FILE = BASE_DIR / "drivers.csv"
MISSIONS_FILE = BASE_DIR / "data" / "missions.csv"
APPROVALS_FILE = BASE_DIR / "data" / "approvals.csv"


def make_driver_code(name):
    code = re.sub(r"[^A-Za-z0-9]+", "-", name.strip().upper())
    return f"DRV-{code}"


def import_drivers(conn):
    driver_ids = {}

    with DRIVERS_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            name = row["name"].strip()
            city = row["city"].strip()
            available = row["available"].strip().lower()

            status = "Available" if available == "yes" else "Unavailable"
            driver_code = make_driver_code(name)

            result = conn.execute(
                """
                INSERT INTO drivers (
                    driver_code,
                    full_name,
                    current_city,
                    status
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (driver_code)
                DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    current_city = EXCLUDED.current_city,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
                """,
                (driver_code, name, city, status),
            )

            driver_ids[name] = result.fetchone()[0]

    return driver_ids


def import_missions(conn, driver_ids):
    mission_ids = {}

    with MISSIONS_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)

        for row in reader:
            if not row:
                continue

            if row[0].strip().lower() == "reference":
                continue

            if len(row) < 8:
                print("Mission ignorée, ligne invalide:", row)
                continue

            reference = row[0].strip()
            pickup_city = row[1].strip()
            delivery_city = row[2].strip()
            mission_date = row[3].strip()
            driver_name = row[4].strip()
            status = row[6].strip()
            distance_text = row[7].strip()

            driver_id = driver_ids.get(driver_name)
            distance_km = int(distance_text) if distance_text else None

            result = conn.execute(
                """
                INSERT INTO missions (
                    reference,
                    pickup_city,
                    delivery_city,
                    mission_date,
                    assigned_driver_id,
                    distance_km,
                    status,
                    source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (reference)
                DO UPDATE SET
                    pickup_city = EXCLUDED.pickup_city,
                    delivery_city = EXCLUDED.delivery_city,
                    mission_date = EXCLUDED.mission_date,
                    assigned_driver_id = EXCLUDED.assigned_driver_id,
                    distance_km = EXCLUDED.distance_km,
                    status = EXCLUDED.status,
                    source = EXCLUDED.source,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
                """,
                (
                    reference,
                    pickup_city,
                    delivery_city,
                    mission_date,
                    driver_id,
                    distance_km,
                    status,
                    "CSV Migration",
                ),
            )

            mission_ids[reference] = result.fetchone()[0]

    return mission_ids


def approval_exists(conn, mission_id, driver_id, status):
    result = conn.execute(
        """
        SELECT id
        FROM approvals
        WHERE mission_id = %s
          AND driver_id = %s
          AND status = %s
        LIMIT 1;
        """,
        (mission_id, driver_id, status),
    )

    return result.fetchone() is not None


def import_approvals(conn, driver_ids, mission_ids):
    with APPROVALS_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            reference = row["reference"].strip()
            proposed_driver = row["proposed_driver"].strip()
            reason = row["reason"].strip()
            distance_text = row["distance_km"].strip()
            decision = row["decision"].strip()
            rejected_text = row["rejected_drivers"].strip()

            mission_id = mission_ids.get(reference)
            driver_id = driver_ids.get(proposed_driver)

            if not mission_id or not driver_id:
                print("Approval ignorée:", reference, proposed_driver)
                continue

            distance_km = int(distance_text) if distance_text else None

            if not approval_exists(conn, mission_id, driver_id, decision):
                conn.execute(
                    """
                    INSERT INTO approvals (
                        mission_id,
                        driver_id,
                        proposed_distance_km,
                        proposal_reason,
                        status,
                        decided_at
                    )
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP);
                    """,
                    (
                        mission_id,
                        driver_id,
                        distance_km,
                        reason,
                        decision,
                    ),
                )

            if rejected_text:
                rejected_names = [
                    name.strip()
                    for name in rejected_text.split(";")
                    if name.strip()
                ]

                for rejected_name in rejected_names:
                    rejected_driver_id = driver_ids.get(rejected_name)

                    if not rejected_driver_id:
                        continue

                    if approval_exists(
                        conn,
                        mission_id,
                        rejected_driver_id,
                        "Rejected",
                    ):
                        continue

                    conn.execute(
                        """
                        INSERT INTO approvals (
                            mission_id,
                            driver_id,
                            proposal_reason,
                            status,
                            decided_at
                        )
                        VALUES (%s, %s, %s, 'Rejected', CURRENT_TIMESTAMP);
                        """,
                        (
                            mission_id,
                            rejected_driver_id,
                            "Migrated from rejected_drivers CSV history",
                        ),
                    )


def main():
    with get_connection() as conn:
        driver_ids = import_drivers(conn)
        mission_ids = import_missions(conn, driver_ids)
        import_approvals(conn, driver_ids, mission_ids)

    print("CSV -> PostgreSQL migration completed.")
    print(f"Drivers: {len(driver_ids)}")
    print(f"Missions: {len(mission_ids)}")


if __name__ == "__main__":
    main()