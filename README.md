# ccu-nurse-rostering

## 資料庫
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
    name NVARCHAR(50) NOT NULL  -- 中文姓名，如 "王小明"
);

-- 3. 每日班次表
CREATE TABLE shifts (
    id VARCHAR(50) PRIMARY KEY, -- 如："SHIFT_260901_01"
    date DATE NOT NULL,         -- 格式 2026-09-01
    shift_type_id VARCHAR(10) NOT NULL, -- 如 "BA"
    expected_patients INT NOT NULL,
    required_nurses INT NOT NULL,
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id)
);

-- 4. 員工需求表
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

-- 5. 排班結果表 (演算法輸出的結果，前端要讀取的表)
CREATE TABLE shift_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shift_id VARCHAR(50) NOT NULL,
    employee_id VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shift_id) REFERENCES shifts(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    UNIQUE KEY unique_assignment (shift_id, employee_id) -- 確保同一個班次不會重複排同一個人
);
