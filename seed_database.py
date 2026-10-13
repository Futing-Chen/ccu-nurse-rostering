"""
將假資料 (ccu_nurse_rostering_testing.json) 匯入 MySQL。

使用方式 (在專案根目錄執行)：
    python seed_database.py
    python seed_database.py 其他資料.json

假資料 JSON 沒有病房的資訊，所以匯入時會建立一個預設病房 (W01)，
把所有班次歸到這個病房，並把所有護理師放進這個病房在班次日期範圍內的名單。

注意：執行時會先「清空」7 張資料表再重新匯入，包含 shift_assignments 裡的排班結果、
以及透過 API 建立的病房與名單。
"""
import json
import sys
from pathlib import Path

from models.database import get_db_connection

DEFAULT_JSON_PATH = Path(__file__).resolve().parent / "ccu_nurse_rostering_testing.json"

# JSON 的需求分類 -> 資料表 requests.request_type 的值
REQUEST_TYPES = {
    "dayOff": "DAY_OFF",
    "dayOn": "DAY_ON",
    "shiftOff": "SHIFT_OFF",
    "shiftOn": "SHIFT_ON",
}

# 清空順序：先刪有外鍵指向別人的表，才不會被外鍵擋下
TABLES_IN_DELETE_ORDER = [
    "shift_assignments", "requests", "ward_rosters", "shifts", "wards", "employees", "shift_types",
]

# 假資料 JSON 沒有病房的資訊，全部歸到這個預設病房
DEFAULT_WARD_ID = "W01"
DEFAULT_WARD_NAME = "預設病房"


def build_request_rows(requests_data):
    """把 JSON 的四類需求攤平成 requests 資料表的資料列。"""
    rows = []
    for json_key, request_type in REQUEST_TYPES.items():
        for item in requests_data.get(json_key, []):
            if request_type in ("DAY_OFF", "DAY_ON"):
                # 整天的需求：只記日期
                target_date, target_shift_id = item["date"], None
            else:
                # 指定班次的需求：只記班次 ID (日期可由 shifts 表查回)
                target_date, target_shift_id = None, item["shiftId"]
            rows.append((item["employeeId"], request_type, target_date, target_shift_id, item.get("weight", 10)))
    return rows


def seed(json_path):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    shift_type_rows = [
        (s["id"], s["name"], s["startTime"], s["endTime"], s["nurseToPatientRatio"])
        for s in data["masterData"]["shiftTypes"]
    ]
    employee_rows = [(e["id"], e["name"]) for e in data["employees"]]
    shift_rows = [
        (s["id"], DEFAULT_WARD_ID, s["date"], s["shiftTypeId"], s["expectedPatients"], s["requiredNurses"])
        for s in data["shifts"]
    ]
    request_rows = build_request_rows(data["requests"])
    # 名單：有班次的每一天，所有護理師都在預設病房的名單內
    shift_dates = sorted({s["date"] for s in data["shifts"]})
    roster_rows = [(DEFAULT_WARD_ID, d, e["id"]) for d in shift_dates for e in data["employees"]]

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for table in TABLES_IN_DELETE_ORDER:
                cursor.execute(f"DELETE FROM {table}")

            # 匯入順序：先匯入被別人參照的表
            cursor.executemany(
                "INSERT INTO shift_types (id, name, start_time, end_time, nurse_to_patient_ratio) "
                "VALUES (%s, %s, %s, %s, %s)",
                shift_type_rows,
            )
            cursor.executemany("INSERT INTO employees (id, name) VALUES (%s, %s)", employee_rows)
            cursor.execute("INSERT INTO wards (id, name) VALUES (%s, %s)", (DEFAULT_WARD_ID, DEFAULT_WARD_NAME))
            cursor.executemany(
                "INSERT INTO shifts (id, ward_id, date, shift_type_id, expected_patients, required_nurses) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                shift_rows,
            )
            if roster_rows:
                cursor.executemany(
                    "INSERT INTO ward_rosters (ward_id, date, employee_id) VALUES (%s, %s, %s)",
                    roster_rows,
                )
            if request_rows:
                cursor.executemany(
                    "INSERT INTO requests (employee_id, request_type, target_date, target_shift_id, weight) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    request_rows,
                )
        # 全部成功才一次寫入，中途出錯就整批退回
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f"匯入完成：{json_path}")
    print(f"  shift_types: {len(shift_type_rows)} 筆")
    print(f"  employees:   {len(employee_rows)} 筆")
    print(f"  wards:       1 筆 ({DEFAULT_WARD_ID})")
    print(f"  shifts:      {len(shift_rows)} 筆")
    print(f"  ward_rosters:{len(roster_rows)} 筆")
    print(f"  requests:    {len(request_rows)} 筆")


if __name__ == "__main__":
    seed(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON_PATH)
