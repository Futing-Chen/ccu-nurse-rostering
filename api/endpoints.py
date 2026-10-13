from datetime import date as date_type, datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional
# 匯入 SQL 連線函數
from models.database import get_db_connection

router = APIRouter()

# ==========================================
# 1. Pydantic 資料模型 
# ==========================================

class ShiftType(BaseModel):
    id: str
    name: str
    startTime: str
    endTime: str
    nurseToPatientRatio: int

class MasterData(BaseModel):
    shiftTypes: List[ShiftType]

class Employee(BaseModel):
    id: str
    name: str

class Shift(BaseModel):
    id: str
    date: str
    shiftTypeId: str
    expectedPatients: int
    requiredNurses: int

class RequestItem(BaseModel):
    employeeId: str
    date: str
    shiftId: Optional[str] = None  # shiftOff/shiftOn 時填入班次ID，對應 target_shift_id (其餘為 None)
    weight: int = 10

class RequestsData(BaseModel):
    dayOff: List[RequestItem] = []
    dayOn: List[RequestItem] = []
    shiftOff: List[RequestItem] = []
    shiftOn: List[RequestItem] = []

class SchedulePayload(BaseModel):
    masterData: MasterData
    employees: List[Employee]
    shifts: List[Shift]
    requests: RequestsData

class RequestCreate(BaseModel):
    employeeId: str
    requestType: Literal["DAY_OFF", "DAY_ON", "SHIFT_OFF", "SHIFT_ON"]
    targetDate: Optional[date_type] = None    # DAY_OFF / DAY_ON 必填
    targetShiftId: Optional[str] = None       # SHIFT_OFF / SHIFT_ON 必填
    weight: int = Field(default=10, ge=1)

class EmployeeCreate(BaseModel):
    # 自動去掉前後空白，避免 " 1001" 和 "1001" 被當成不同人
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=50)

class EmployeeUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    isActive: Optional[bool] = None    # False = 停用 (離職)，True = 重新啟用 (復職)

class WardCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=50)

class RosterUpdate(BaseModel):
    startDate: date_type
    endDate: date_type
    employeeIds: List[str]    # 這段期間負責該病房的護理師，空陣列代表清空名單

class AssignmentItem(BaseModel):
    shiftId: str
    employeeId: str

# ==========================================
# 共用工具
# ==========================================

# 一次設定病房名單的天數上限，避免打錯年份時寫入大量資料
MAX_ROSTER_DAYS = 92

def require_param(name: str, value: Optional[str]) -> str:
    """確認必要的查詢參數有提供，缺少時回 400。"""
    if not value:
        raise HTTPException(status_code=400, detail={
            "message": f"缺少必要的查詢參數：{name}",
            "details": f"請提供 {name}"
        })
    return value

def get_ward_or_404(cursor, ward_id: str) -> dict:
    """查出病房資料，不存在時回 404。"""
    cursor.execute("SELECT id, name FROM wards WHERE id = %s", (ward_id,))
    ward = cursor.fetchone()
    if ward is None:
        raise HTTPException(status_code=404, detail={
            "message": "找不到該病房資料",
            "details": {"ward_id": ward_id}
        })
    return ward

def parse_date_param(name: str, value: Optional[str]) -> date_type:
    """把 YYYY-MM-DD 的查詢參數轉成日期，缺少或格式錯誤時回 400。"""
    if not value:
        raise HTTPException(status_code=400, detail={
            "message": f"缺少必要的查詢參數：{name}",
            "details": "請提供 YYYY-MM-DD 格式的日期"
        })
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "message": f"查詢參數 {name} 格式錯誤",
            "details": "請提供 YYYY-MM-DD 格式的日期"
        })

# ==========================================
# 2. API 路由 (Endpoints)
# ==========================================

@router.get("/ping")
def ping_server():
    return {"status": "success", "message": "護理排班 API 伺服器運作中！"}

@router.get("/db-check")
def db_check():
    """
    確認 FastAPI 能否連上 MySQL，並回傳資料庫版本與現有的資料表。
    """
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version, DATABASE() AS db_name")
            info = cursor.fetchone()
            cursor.execute("SHOW TABLES")
            tables = [list(row.values())[0] for row in cursor.fetchall()]

        return {
            "status": "success",
            "message": "成功連上 MySQL！",
            "version": info["version"],
            "database": info["db_name"],
            "tables": tables
        }

    finally:
        conn.close()

@router.get("/employees")
def get_employees(include_inactive: bool = False):
    """
    取得護理師名單。預設只回傳在職的護理師，
    include_inactive=true 時連已停用的也一起回傳 (管理頁面用)。
    """
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, is_active FROM employees WHERE (%s OR is_active) ORDER BY id",
                (include_inactive,),
            )
            return [
                {"id": row["id"], "name": row["name"], "isActive": bool(row["is_active"])}
                for row in cursor.fetchall()
            ]

    finally:
        conn.close()

@router.post("/employees")
def create_employee(payload: EmployeeCreate):
    """
    新增一位護理師。id 為員工編號，不可與現有的重複 (包含已停用的)。
    """
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT is_active FROM employees WHERE id = %s", (payload.id,))
            existing = cursor.fetchone()
            if existing is not None:
                raise HTTPException(status_code=409, detail={
                    "message": "該員工編號已存在",
                    "details": {
                        "employee_id": payload.id,
                        "is_active": bool(existing["is_active"]),
                        "hint": "若是已停用的護理師復職，請改用 PATCH /api/employees/{id} 重新啟用"
                    }
                })

            cursor.execute("INSERT INTO employees (id, name) VALUES (%s, %s)", (payload.id, payload.name))
        conn.commit()

        return {"status": "success", "message": "護理師已新增"}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

@router.patch("/employees/{employee_id}")
def update_employee(employee_id: str, payload: EmployeeUpdate):
    """
    修改護理師資料：改姓名、停用 (isActive=false) 或重新啟用 (isActive=true)。
    只需要帶要修改的欄位。
    停用只是做記號，不會刪除任何資料，過去的班表與需求都會保留，復職時重新啟用即可。
    """
    if payload.name is None and payload.isActive is None:
        raise HTTPException(status_code=400, detail={
            "message": "沒有提供要修改的欄位",
            "details": "請至少提供 name 或 isActive 其中一項"
        })

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM employees WHERE id = %s", (employee_id,))
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail={
                    "message": "找不到該護理師資料",
                    "details": {"employee_id": employee_id}
                })

            # COALESCE(%s, 欄位)：有帶值就更新，沒帶 (NULL) 就維持原值
            cursor.execute(
                "UPDATE employees SET name = COALESCE(%s, name), is_active = COALESCE(%s, is_active) WHERE id = %s",
                (payload.name, payload.isActive, employee_id),
            )
        conn.commit()

        return {"status": "success", "message": "護理師資料已更新"}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

@router.get("/wards")
def get_wards():
    """
    取得所有病房。
    """
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM wards ORDER BY id")
            return cursor.fetchall()

    finally:
        conn.close()

@router.post("/wards")
def create_ward(payload: WardCreate):
    """
    新增一個病房。id 為病房代碼，不可與現有的重複。
    """
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM wards WHERE id = %s", (payload.id,))
            if cursor.fetchone() is not None:
                raise HTTPException(status_code=409, detail={
                    "message": "該病房代碼已存在",
                    "details": {"ward_id": payload.id}
                })

            cursor.execute("INSERT INTO wards (id, name) VALUES (%s, %s)", (payload.id, payload.name))
        conn.commit()

        return {"status": "success", "message": "病房已新增"}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

@router.put("/wards/{ward_id}/roster")
def set_ward_roster(ward_id: str, payload: RosterUpdate):
    """
    設定某個病房在一段期間內 (含頭尾) 的名單，也就是這段期間由哪些護理師負責這個病房。
    該期間原本的名單會被整個取代；期間以外的名單不受影響。
    同一位護理師可以同時在多個病房的名單內。已停用 (離職) 的護理師不能加入名單。
    """
    if payload.startDate > payload.endDate:
        raise HTTPException(status_code=400, detail={
            "message": "startDate 不可晚於 endDate",
            "details": {"startDate": str(payload.startDate), "endDate": str(payload.endDate)}
        })
    days = (payload.endDate - payload.startDate).days + 1
    if days > MAX_ROSTER_DAYS:
        raise HTTPException(status_code=400, detail={
            "message": "一次設定的期間過長",
            "details": f"一次最多設定 {MAX_ROSTER_DAYS} 天，請分次設定"
        })

    # 去掉重複的編號，保留原本的順序
    employee_ids = list(dict.fromkeys(payload.employeeIds))

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            get_ward_or_404(cursor, ward_id)

            if employee_ids:
                placeholders = ", ".join(["%s"] * len(employee_ids))
                cursor.execute(f"SELECT id, is_active FROM employees WHERE id IN ({placeholders})", employee_ids)
                found = {row["id"]: row["is_active"] for row in cursor.fetchall()}
                missing = [e for e in employee_ids if e not in found]
                if missing:
                    raise HTTPException(status_code=404, detail={
                        "message": "找不到該護理師資料",
                        "details": {"employee_ids": missing}
                    })
                inactive = [e for e in employee_ids if not found[e]]
                if inactive:
                    raise HTTPException(status_code=400, detail={
                        "message": "已停用的護理師不能加入病房名單",
                        "details": {"employee_ids": inactive}
                    })

            cursor.execute(
                "DELETE FROM ward_rosters WHERE ward_id = %s AND date >= %s AND date <= %s",
                (ward_id, payload.startDate, payload.endDate),
            )
            rows = [
                (ward_id, payload.startDate + timedelta(days=offset), employee_id)
                for offset in range(days)
                for employee_id in employee_ids
            ]
            if rows:
                cursor.executemany(
                    "INSERT INTO ward_rosters (ward_id, date, employee_id) VALUES (%s, %s, %s)",
                    rows,
                )
        # 刪除與寫入全部成功才一次寫入，中途出錯就整批退回
        conn.commit()

        return {"status": "success", "message": "病房名單已更新"}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

@router.get("/wards/{ward_id}/roster")
def get_ward_roster(ward_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """
    查詢某個病房在日期區間內 (含頭尾) 的名單。
    每位護理師會列出她在名單內的日期 (dates)，
    以及她在這些日期同時還負責哪些其他病房 (otherWards，沒有則為空陣列)，供前端標註。
    """
    start = parse_date_param("start_date", start_date)
    end = parse_date_param("end_date", end_date)
    if start > end:
        raise HTTPException(status_code=400, detail={
            "message": "start_date 不可晚於 end_date",
            "details": {"start_date": start_date, "end_date": end_date}
        })

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            get_ward_or_404(cursor, ward_id)

            cursor.execute("""
                SELECT e.id, e.name, e.is_active, DATE_FORMAT(wr.date, '%%Y-%%m-%%d') AS date
                FROM ward_rosters wr
                JOIN employees e ON e.id = wr.employee_id
                WHERE wr.ward_id = %s AND wr.date >= %s AND wr.date <= %s
                ORDER BY e.id, wr.date
            """, (ward_id, start, end))
            roster = {}
            for row in cursor.fetchall():
                entry = roster.setdefault(row["id"], {
                    "id": row["id"],
                    "name": row["name"],
                    "isActive": bool(row["is_active"]),
                    "dates": [],
                    "otherWards": []
                })
                entry["dates"].append(row["date"])

            # 同一天也在其他病房名單內的護理師 (同一位護理師、同一天、不同病房)
            cursor.execute("""
                SELECT DISTINCT wr.employee_id AS employeeId, w.id, w.name
                FROM ward_rosters wr
                JOIN ward_rosters other ON other.employee_id = wr.employee_id
                                       AND other.date = wr.date
                                       AND other.ward_id <> wr.ward_id
                JOIN wards w ON w.id = other.ward_id
                WHERE wr.ward_id = %s AND wr.date >= %s AND wr.date <= %s
                ORDER BY wr.employee_id, w.id
            """, (ward_id, start, end))
            for row in cursor.fetchall():
                roster[row["employeeId"]]["otherWards"].append({"id": row["id"], "name": row["name"]})

        return list(roster.values())

    finally:
        conn.close()

@router.get("/solver/dataset")
def get_solver_dataset(year_month: Optional[str] = None, ward_id: Optional[str] = None):
    """
    將資料庫的表組合成演算法所需的完整 JSON (格式同 ccu_nurse_rostering_testing.json)。
    year_month 格式為 YYYY-MM，例如 2026-09；ward_id 為要排班的病房。
    只回傳該病房的班次，以及該月份在該病房名單內的在職護理師。
    另外多回傳 ward (病房資料) 與 roster (每位護理師哪幾天在名單內，不在名單內的日子不可排班)。
    """
    if not year_month:
        raise HTTPException(status_code=400, detail={
            "message": "缺少必要的查詢參數：year_month",
            "details": "請提供 YYYY-MM 格式的月份"
        })
    require_param("ward_id", ward_id)
    try:
        month_start = datetime.strptime(year_month, "%Y-%m").date()
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "message": "查詢參數 year_month 格式錯誤",
            "details": "請提供 YYYY-MM 格式的月份"
        })
    # 下個月的 1 號，查詢範圍為 [month_start, next_month_start)
    next_month_start = (month_start + timedelta(days=32)).replace(day=1)

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            # TIME_FORMAT 直接轉成 "HH:MM" 字串，否則 pymysql 會回傳 timedelta
            # (這句沒有帶參數所以 % 寫一個就好；下面有帶參數的查詢要寫成 %%)
            cursor.execute("""
                SELECT id, name,
                       TIME_FORMAT(start_time, '%H:%i') AS startTime,
                       TIME_FORMAT(end_time, '%H:%i') AS endTime,
                       nurse_to_patient_ratio AS nurseToPatientRatio
                FROM shift_types
                ORDER BY id
            """)
            shift_types = cursor.fetchall()

            ward = get_ward_or_404(cursor, ward_id)

            # 這個月在該病房名單內的在職護理師，一列是「某位護理師、某一天」
            cursor.execute("""
                SELECT e.id, e.name, DATE_FORMAT(wr.date, '%%Y-%%m-%%d') AS date
                FROM ward_rosters wr
                JOIN employees e ON e.id = wr.employee_id AND e.is_active
                WHERE wr.ward_id = %s AND wr.date >= %s AND wr.date < %s
                ORDER BY e.id, wr.date
            """, (ward_id, month_start, next_month_start))
            roster_dates = {}
            employee_names = {}
            for row in cursor.fetchall():
                employee_names[row["id"]] = row["name"]
                roster_dates.setdefault(row["id"], []).append(row["date"])
            employees = [{"id": i, "name": n} for i, n in employee_names.items()]
            roster = [{"employeeId": i, "dates": d} for i, d in roster_dates.items()]

            cursor.execute("""
                SELECT id,
                       DATE_FORMAT(date, '%%Y-%%m-%%d') AS date,
                       shift_type_id AS shiftTypeId,
                       expected_patients AS expectedPatients,
                       required_nurses AS requiredNurses
                FROM shifts
                WHERE ward_id = %s AND date >= %s AND date < %s
                ORDER BY date, id
            """, (ward_id, month_start, next_month_start))
            shifts = cursor.fetchall()

            # SHIFT_OFF / SHIFT_ON 的 target_date 是 NULL，日期要從 shifts 表查回來
            # 只取名單內護理師的需求；指定班次的需求只取這個病房的班次
            cursor.execute("""
                SELECT r.employee_id AS employeeId,
                       r.request_type AS requestType,
                       DATE_FORMAT(COALESCE(r.target_date, s.date), '%%Y-%%m-%%d') AS date,
                       r.target_shift_id AS shiftId,
                       r.weight
                FROM requests r
                LEFT JOIN shifts s ON s.id = r.target_shift_id
                WHERE COALESCE(r.target_date, s.date) >= %s
                  AND COALESCE(r.target_date, s.date) < %s
                  AND (r.target_shift_id IS NULL OR s.ward_id = %s)
                ORDER BY r.id
            """, (month_start, next_month_start, ward_id))
            request_rows = [row for row in cursor.fetchall() if row["employeeId"] in employee_names]

        requests = {"dayOff": [], "dayOn": [], "shiftOff": [], "shiftOn": []}
        request_keys = {"DAY_OFF": "dayOff", "DAY_ON": "dayOn", "SHIFT_OFF": "shiftOff", "SHIFT_ON": "shiftOn"}
        for row in request_rows:
            item = {"employeeId": row["employeeId"], "date": row["date"]}
            # 只有指定班次的需求才帶 shiftId，與假資料 JSON 的格式一致
            if row["shiftId"] is not None:
                item["shiftId"] = row["shiftId"]
            item["weight"] = row["weight"]
            requests[request_keys[row["requestType"]]].append(item)

        return {
            "masterData": {"shiftTypes": shift_types},
            "ward": ward,
            "employees": employees,
            "roster": roster,
            "shifts": shifts,
            "requests": requests
        }

    finally:
        conn.close()

@router.post("/requests")
def create_request(payload: RequestCreate):
    """
    新增一筆員工需求 (預假 / 指定上班)。
    DAY_OFF、DAY_ON 需填 targetDate；SHIFT_OFF、SHIFT_ON 需填 targetShiftId。
    """
    is_day_request = payload.requestType in ("DAY_OFF", "DAY_ON")

    if is_day_request and payload.targetDate is None:
        raise HTTPException(status_code=400, detail={
            "message": "缺少必要的欄位：targetDate",
            "details": f"{payload.requestType} 需要提供 YYYY-MM-DD 格式的 targetDate"
        })
    if not is_day_request and not payload.targetShiftId:
        raise HTTPException(status_code=400, detail={
            "message": "缺少必要的欄位：targetShiftId",
            "details": f"{payload.requestType} 需要提供 targetShiftId"
        })

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT is_active FROM employees WHERE id = %s", (payload.employeeId,))
            employee = cursor.fetchone()
            if employee is None:
                raise HTTPException(status_code=404, detail={
                    "message": "找不到該護理師資料",
                    "details": {"employee_id": payload.employeeId}
                })
            if not employee["is_active"]:
                raise HTTPException(status_code=400, detail={
                    "message": "該護理師已停用，無法送出需求",
                    "details": {"employee_id": payload.employeeId}
                })

            if is_day_request:
                # 整天的需求：只記日期
                target_date, target_shift_id = payload.targetDate, None
            else:
                cursor.execute("SELECT date FROM shifts WHERE id = %s", (payload.targetShiftId,))
                shift = cursor.fetchone()
                if shift is None:
                    raise HTTPException(status_code=404, detail={
                        "message": "找不到該班次資料",
                        "details": {"shift_id": payload.targetShiftId}
                    })
                if payload.targetDate is not None and payload.targetDate != shift["date"]:
                    raise HTTPException(status_code=400, detail={
                        "message": "targetDate 與班次的日期不一致",
                        "details": {"targetDate": str(payload.targetDate), "shiftDate": str(shift["date"])}
                    })
                # 指定班次的需求：只記班次 ID (日期可由 shifts 表查回)
                target_date, target_shift_id = None, payload.targetShiftId

            # 同一位護理師對同一天 (或同一個班次) 只能有一筆需求，避免權重被疊加
            # 不分類型：已經有 DAY_OFF 就不能再送 DAY_OFF 或 DAY_ON
            if is_day_request:
                cursor.execute(
                    "SELECT id, request_type FROM requests WHERE employee_id = %s AND target_date = %s LIMIT 1",
                    (payload.employeeId, target_date),
                )
            else:
                cursor.execute(
                    "SELECT id, request_type FROM requests WHERE employee_id = %s AND target_shift_id = %s LIMIT 1",
                    (payload.employeeId, target_shift_id),
                )
            existing = cursor.fetchone()
            if existing is not None:
                raise HTTPException(status_code=409, detail={
                    "message": "該護理師已對同一天提出過需求" if is_day_request else "該護理師已對同一個班次提出過需求",
                    "details": {
                        "existing_request_id": existing["id"],
                        "existing_request_type": existing["request_type"],
                        "hint": "如需修改，請先收回原本的需求再重新送出"
                    }
                })

            cursor.execute(
                "INSERT INTO requests (employee_id, request_type, target_date, target_shift_id, weight) "
                "VALUES (%s, %s, %s, %s, %s)",
                (payload.employeeId, payload.requestType, target_date, target_shift_id, payload.weight),
            )
            request_id = cursor.lastrowid
        conn.commit()

        # requestId 之後收回需求 (DELETE /api/requests/{id}) 時會用到
        return {"status": "success", "message": "需求已建立", "requestId": request_id}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

@router.get("/requests")
def get_requests(employee_id: Optional[str] = None):
    """
    查詢已送出的需求 (含每筆的 id，收回需求時會用到)。
    帶 employee_id 只查該護理師的需求，不帶則回傳全部。
    """
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            if employee_id is not None:
                cursor.execute("SELECT id FROM employees WHERE id = %s", (employee_id,))
                if cursor.fetchone() is None:
                    raise HTTPException(status_code=404, detail={
                        "message": "找不到該護理師資料",
                        "details": {"employee_id": employee_id}
                    })

            # SHIFT_OFF / SHIFT_ON 的 target_date 是 NULL，日期要從 shifts 表查回來
            # (%s IS NULL OR ...) 讓同一句 SQL 同時處理「有帶」與「沒帶」employee_id 兩種情況
            cursor.execute("""
                SELECT r.id,
                       r.employee_id AS employeeId,
                       r.request_type AS requestType,
                       DATE_FORMAT(COALESCE(r.target_date, s.date), '%%Y-%%m-%%d') AS targetDate,
                       r.target_shift_id AS targetShiftId,
                       r.weight
                FROM requests r
                LEFT JOIN shifts s ON s.id = r.target_shift_id
                WHERE (%s IS NULL OR r.employee_id = %s)
                ORDER BY COALESCE(r.target_date, s.date), r.id
            """, (employee_id, employee_id))
            return cursor.fetchall()

    finally:
        conn.close()

@router.delete("/requests/{request_id}")
def delete_request(request_id: int):
    """
    收回 (刪除) 一筆已送出的需求。request_id 可由 GET /api/requests 查到。
    """
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            deleted = cursor.execute("DELETE FROM requests WHERE id = %s", (request_id,))
            if deleted == 0:
                raise HTTPException(status_code=404, detail={
                    "message": "找不到該筆需求",
                    "details": {"request_id": request_id}
                })
        conn.commit()

        return {"status": "success", "message": "需求已收回"}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

@router.post("/solver/assignments")
def upload_assignments(items: List[AssignmentItem]):
    """
    把演算法的排班結果存進 shift_assignments。
    注意：上傳的班次所屬「病房 + 月份」的舊排班結果會先被清掉再寫入 (整月取代)，
    這樣重新排班時才不會留下舊資料。其他病房的排班結果不受影響。
    護理師必須在該班次所屬病房當天的名單內，否則回 400。
    """
    if not items:
        raise HTTPException(status_code=400, detail={
            "message": "排班結果不可為空",
            "details": "請至少提供一筆 { shiftId, employeeId }"
        })

    pairs = [(item.shiftId, item.employeeId) for item in items]
    duplicates = sorted({pair for pair in pairs if pairs.count(pair) > 1})
    if duplicates:
        raise HTTPException(status_code=400, detail={
            "message": "排班結果中有重複的配對",
            "details": [{"shiftId": s, "employeeId": e} for s, e in duplicates]
        })

    shift_ids = sorted({s for s, _ in pairs})
    employee_ids = sorted({e for _, e in pairs})

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            placeholders = ", ".join(["%s"] * len(shift_ids))
            cursor.execute(
                "SELECT id, ward_id, date, DATE_FORMAT(date, '%%Y-%%m') AS month "
                f"FROM shifts WHERE id IN ({placeholders})",
                shift_ids,
            )
            shift_info = {row["id"]: row for row in cursor.fetchall()}
            missing_shifts = [s for s in shift_ids if s not in shift_info]
            if missing_shifts:
                raise HTTPException(status_code=404, detail={
                    "message": "找不到該班次資料",
                    "details": {"shift_ids": missing_shifts}
                })

            placeholders = ", ".join(["%s"] * len(employee_ids))
            cursor.execute(f"SELECT id FROM employees WHERE id IN ({placeholders})", employee_ids)
            found_employees = {row["id"] for row in cursor.fetchall()}
            missing_employees = [e for e in employee_ids if e not in found_employees]
            if missing_employees:
                raise HTTPException(status_code=404, detail={
                    "message": "找不到該護理師資料",
                    "details": {"employee_ids": missing_employees}
                })

            # 護理師必須在該班次所屬病房當天的名單內才能被排班 (不在名單內 = 不啟用)
            ward_dates = sorted({(info["ward_id"], info["date"]) for info in shift_info.values()})
            placeholders = ", ".join(["(%s, %s)"] * len(ward_dates))
            cursor.execute(
                f"SELECT ward_id, date, employee_id FROM ward_rosters WHERE (ward_id, date) IN ({placeholders})",
                [value for pair in ward_dates for value in pair],
            )
            on_roster = {(row["ward_id"], row["date"], row["employee_id"]) for row in cursor.fetchall()}
            not_on_roster = [
                {"shiftId": s, "employeeId": e}
                for s, e in pairs
                if (shift_info[s]["ward_id"], shift_info[s]["date"], e) not in on_roster
            ]
            if not_on_roster:
                raise HTTPException(status_code=400, detail={
                    "message": "有護理師不在該班次所屬病房當天的名單內",
                    "details": not_on_roster
                })

            # 先清掉這些「病房 + 月份」的舊排班結果，不會動到其他病房
            ward_months = sorted({(info["ward_id"], info["month"]) for info in shift_info.values()})
            placeholders = ", ".join(["(%s, %s)"] * len(ward_months))
            cursor.execute(
                "DELETE sa FROM shift_assignments sa "
                "JOIN shifts s ON s.id = sa.shift_id "
                f"WHERE (s.ward_id, DATE_FORMAT(s.date, '%%Y-%%m')) IN ({placeholders})",
                [value for pair in ward_months for value in pair],
            )

            cursor.executemany(
                "INSERT INTO shift_assignments (shift_id, employee_id) VALUES (%s, %s)",
                pairs,
            )
        # 刪除與寫入全部成功才一次寫入，中途出錯就整批退回
        conn.commit()

        return {"status": "success", "message": "排班結果已寫入資料庫"}

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

@router.get("/schedule")
def get_schedule(start_date: Optional[str] = None, end_date: Optional[str] = None, ward_id: Optional[str] = None):
    """
    查詢某個病房在日期區間內 (含頭尾) 的最終班表，日期格式為 YYYY-MM-DD。
    尚未排人的班次也會回傳，assignedNurses 為空陣列。
    """
    start = parse_date_param("start_date", start_date)
    end = parse_date_param("end_date", end_date)
    require_param("ward_id", ward_id)
    if start > end:
        raise HTTPException(status_code=400, detail={
            "message": "start_date 不可晚於 end_date",
            "details": {"start_date": start_date, "end_date": end_date}
        })

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            get_ward_or_404(cursor, ward_id)

            cursor.execute("""
                SELECT s.id AS shiftId,
                       DATE_FORMAT(s.date, '%%Y-%%m-%%d') AS date,
                       s.shift_type_id AS shiftTypeId,
                       st.name AS shiftName,
                       e.id AS employeeId,
                       e.name AS employeeName
                FROM shifts s
                JOIN shift_types st ON st.id = s.shift_type_id
                LEFT JOIN shift_assignments sa ON sa.shift_id = s.id
                LEFT JOIN employees e ON e.id = sa.employee_id
                WHERE s.ward_id = %s AND s.date >= %s AND s.date <= %s
                ORDER BY s.date, s.id, e.id
            """, (ward_id, start, end))
            rows = cursor.fetchall()

        # 一個班次有幾位護理師就有幾列，這裡把同一個班次的列合併成一筆
        schedule = {}
        for row in rows:
            entry = schedule.setdefault(row["shiftId"], {
                "date": row["date"],
                "shiftTypeId": row["shiftTypeId"],
                "shiftName": row["shiftName"],
                "assignedNurses": []
            })
            if row["employeeId"] is not None:
                entry["assignedNurses"].append({"id": row["employeeId"], "name": row["employeeName"]})

        return list(schedule.values())

    finally:
        conn.close()

@router.post("/generate-schedule")
def generate_schedule(payload: SchedulePayload):
    """
    接收完整的 JSON 資料並進行處理。
    """
    # 每次請求進來時，手動開啟資料庫連線
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            # TODO: 可以在這裡寫原生 SQL，把 payload 存進 MySQL
            # 範例寫法 (記得要用參數化查詢防止 SQL 注入)：
            # sql = "INSERT INTO employees (employee_id, name) VALUES (%s, %s)"
            # cursor.executemany(sql, [(e.id, e.name) for e in payload.employees])
            # conn.commit()  <-- 重要：執行 INSERT 或 UPDATE 後一定要 commit 才會寫入

            # TODO: 2. 呼叫寫好的 OR-Tools 排班演算法
            
            # TODO: 3. 將排班結果整理成 JSON 格式回傳給前端
            pass

        return {
            "status": "success",
            "message": f"成功接收資料！共收到 {len(payload.employees)} 位護理師與 {len(payload.shifts)} 個班次需求。",
            "data": "這裡未來會放演算法算出來的最終班表"
        }
        
    except Exception as e:
        # 如果發生任何錯誤（包含 SQL 語法寫錯），退回所有尚未 commit 的變更
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # 防雷：無論成功或失敗，絕對要關閉連線，否則連線池會塞爆
        conn.close()
