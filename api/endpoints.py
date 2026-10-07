from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
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
