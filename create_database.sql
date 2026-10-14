CREATE DATABASE IF NOT EXISTS ccu_nurse_rostering;
USE ccu_nurse_rostering;
-- 1. 班別表
CREATE TABLE shift_types (
    id VARCHAR(10) PRIMARY KEY, -- 如 "BA", "CG", "AA"
    name NVARCHAR(20) NOT NULL, -- 中文班別名稱，如 "白班"
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    nurse_to_patient_ratio INT NOT NULL -- 護病比，如 1:7, 1:11, 1:13
);

-- 2. 護理師人員表
CREATE TABLE employees (
    id VARCHAR(20) PRIMARY KEY, -- 如 "1001"
    name NVARCHAR(50) NOT NULL, -- 中文姓名，如 "王小明"
    is_active BOOLEAN NOT NULL DEFAULT TRUE -- 是否在職，離職時設為 FALSE (不刪除資料，復職時改回 TRUE)
);

-- 3. 病房表
CREATE TABLE wards (
    id VARCHAR(20) PRIMARY KEY, -- 如 "W01"
    name NVARCHAR(50) NOT NULL, -- 病房名稱
    max_patients INT NOT NULL   -- 病房最大容量，產生班次時用來計算需求人數 (修改後只影響之後產生的班次)
);

-- 4. 每日班次表 (每個班次屬於一個病房)
CREATE TABLE shifts (
    id VARCHAR(50) PRIMARY KEY, -- 如："SHIFT_260901_01" (不同病房的班次 ID 不可重複)
    ward_id VARCHAR(20) NOT NULL, -- 如 "W01"
    date DATE NOT NULL,         -- 格式 2026-09-01
    shift_type_id VARCHAR(10) NOT NULL, -- 如 "BA"
    expected_patients INT NOT NULL, -- 排班時預設的病人數 (產生班次當時的病房最大容量)
    actual_patients INT,            -- 實際病人數，由護理長事後填入 (未填為 NULL)
    required_nurses INT NOT NULL,   -- 依 expected_patients 與護病比算出的需求人數
    FOREIGN KEY (ward_id) REFERENCES wards(id),
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id)
);

-- 5. 員工需求表
CREATE TABLE requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    request_type VARCHAR(20) NOT NULL, -- 'DAY_OFF', 'DAY_ON', 'SHIFT_OFF', 'SHIFT_ON'
    target_date DATE,                  -- 如果是 DAY_OFF/DAY_ON，填入日期 (其餘為NULL)
    target_shift_id VARCHAR(50),       -- 如果是 SHIFT_OFF/SHIFT_ON，填入班次ID (其餘為NULL)
    weight INT NOT NULL DEFAULT 10,    -- 需求權重
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (target_shift_id) REFERENCES shifts(id)
);

-- 6. 排班結果表 (演算法輸出的結果，前端要讀取的表)
CREATE TABLE shift_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shift_id VARCHAR(50) NOT NULL,
    employee_id VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shift_id) REFERENCES shifts(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    UNIQUE KEY unique_assignment (shift_id, employee_id) -- 確保同一個班次不會重複排同一個人
);

-- 7. 病房名單表 (哪一天、哪些護理師負責哪個病房)
-- 一列代表「某病房、某一天、某位護理師在名單內」，同一位護理師同一天可以在多個病房的名單內
-- 在名單內: 當天有被排班 = 值班，沒被排班 = 休假；不在名單內 = 不啟用
CREATE TABLE ward_rosters (
    ward_id VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    employee_id VARCHAR(20) NOT NULL,
    PRIMARY KEY (ward_id, date, employee_id),
    FOREIGN KEY (ward_id) REFERENCES wards(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
