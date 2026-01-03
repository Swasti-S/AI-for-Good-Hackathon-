-----------------------------------------------------------
-- 1. Calculate Risk Score Per Room
-----------------------------------------------------------

CREATE OR REPLACE TABLE ROOM_RISK_SCORE_TABLE AS
WITH image_defects AS (
  SELECT
    ir.PROPERTY_ID,
    ir.ROOM_NAME,
    d.value::string AS defect
  FROM IMAGE_ISSUES i
  JOIN IMAGE_RAW ir 
    ON i.IMAGE_NAME = ir.IMAGE_NAME
  , LATERAL FLATTEN(input => i.IMAGE_DEFECT:labels) d
),
note_defects AS (
  SELECT
    il.PROPERTY_ID,
    il.ROOM_NAME,
    n.value::string AS defect
  FROM INSPECTION_LOGS_ISSUES ili
  JOIN INSPECTION_LOGS il 
    ON ili.INSPECTION_ID = il.INSPECTION_ID
  , LATERAL FLATTEN(input => ili.NOTE_DEFECT:labels) n
),
all_defects AS (
  SELECT * FROM image_defects
  UNION ALL
  SELECT * FROM note_defects
),
defect_weights AS (
  SELECT 'exposed_wiring' AS defect, 5 AS severity
  UNION ALL SELECT 'leak', 4
  UNION ALL SELECT 'crack', 3
  UNION ALL SELECT 'termite', 4
  UNION ALL SELECT 'mold', 2
  UNION ALL SELECT 'no damage', 0
)
SELECT
  a.PROPERTY_ID,
  a.ROOM_NAME,
  SUM(w.severity) AS ROOM_SEVERITY_SCORE
FROM all_defects a
JOIN defect_weights w 
  ON a.defect = w.defect
GROUP BY a.PROPERTY_ID, a.ROOM_NAME;

-----------------------------------------------------------
-- 2. Calculate Total Risk Score Per Property
-----------------------------------------------------------

CREATE OR REPLACE TABLE PROPERTY_RISK_SCORE_TABLE AS
SELECT
  PROPERTY_ID,
  SUM(ROOM_SEVERITY_SCORE) AS TOTAL_PROPERTY_SEVERITY_SCORE,
  CASE
    WHEN SUM(ROOM_SEVERITY_SCORE) >= 20 THEN 'High'
    WHEN SUM(ROOM_SEVERITY_SCORE) >= 10 THEN 'Medium'
    ELSE 'Low'
  END AS RISK_CATEGORY
FROM ROOM_RISK_SCORE_TABLE
GROUP BY PROPERTY_ID;

-----------------------------------------------------------
-- 3. Update Master Properties List
-----------------------------------------------------------

INSERT INTO PROPERTIES (PROPERTY_ID)
SELECT DISTINCT PROPERTY_ID
FROM ROOMS
WHERE PROPERTY_ID NOT IN (SELECT PROPERTY_ID FROM PROPERTIES);
