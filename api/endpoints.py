from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# 建立 API 路由器
router = APIRouter()

# ==========================================
# 1. Pydantic 資料模型 (嚴格把關 JSON 格式)
# 這裡的變數名稱必須跟統一定義的 JSON 完全一模一樣
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
    weight: int = 10

class RequestsData(BaseModel):
    dayOff: List[RequestItem] = []
    dayOn: List[RequestItem] = []
    shiftOff: List[RequestItem] = []
    shiftOn: List[RequestItem] = []

# 這是最外層的 JSON 總包裝
class SchedulePayload(BaseModel):
    masterData: MasterData
    employees: List[Employee]
    shifts: List[Shift]
    requests: RequestsData

# ==========================================
# 2. API 路由 (Endpoints)
# ==========================================

# 測試用 API：前端 跟 n8n 確認伺服器有沒有活著
@router.get("/ping")
def ping_server():
    return {"status": "success", "message": "護理排班 API 伺服器運作中！"}

# 核心 API：接收前端傳來的排班 JSON，準備進行運算
@router.post("/generate-schedule")
def generate_schedule(payload: SchedulePayload):
    """
    接收完整的 JSON 資料。
    FastAPI 會自動幫我們比對 payload 的格式，
    如果前端少傳欄位或拼錯字 (例如把 id 拼成 nurseId)，FastAPI 會直接報錯擋下！
    """
    try:
        # TODO: 1. 可以在這裡寫 SQLAlchemy 語法，把 payload 存進 MySQL
        # TODO: 2. 呼叫寫好的 OR-Tools 排班演算法
        # TODO: 3. 將排班結果整理成 JSON 格式回傳給前端
        
        # 這裡先回傳假結果測試用
        return {
            "status": "success",
            "message": f"成功接收資料！共收到 {len(payload.employees)} 位護理師與 {len(payload.shifts)} 個班次需求。",
            "data": "這裡未來會放演算法算出來的最終班表"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
