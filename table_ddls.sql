-- 1. Properties Table
create or replace TABLE AI_FOR_GOOD.AI_HOME_INSPECTION.PROPERTIES (
	PROPERTY_ID VARCHAR(16777216),
	ADDRESS VARCHAR(16777216),
	OWNER_NAME VARCHAR(16777216)
);

-- 2. Rooms Table
CREATE OR REPLACE TABLE ROOMS
AS
WITH 
-- Count distinct images per property and room type
image_room_counts AS (
  SELECT 
    property_id,
    room_name,
    COUNT(DISTINCT image_name) AS image_count
  FROM image_raw
  GROUP BY property_id, room_name
),
-- Count distinct inspection records per property and room type
inspection_room_counts AS (
  SELECT 
    property_id,
    room_name,
    COUNT(DISTINCT inspection_id) AS inspection_count
  FROM inspection_logs
  GROUP BY property_id, room_name
)
-- Take the MAXIMUM count from both sources for most accurate room count
SELECT 
  COALESCE(irc.property_id, ilc.property_id) AS property_id,
  COALESCE(irc.room_name, ilc.room_name) AS room_name,
  GREATEST(
    COALESCE(irc.image_count, 0),
    COALESCE(ilc.inspection_count, 0)
  ) AS room_count,
  irc.image_count AS image_based_count,
  ilc.inspection_count AS inspection_based_count
FROM image_room_counts irc
FULL OUTER JOIN inspection_room_counts ilc
  ON irc.property_id = ilc.property_id
  AND irc.room_name = ilc.room_name;


-- 3. Inspection Logs (Raw Text)
create or replace TABLE AI_FOR_GOOD.AI_HOME_INSPECTION.INSPECTION_LOGS (
	INSPECTION_ID NUMBER(38,0),
	PROPERTY_ID VARCHAR(16777216),
	ROOM_NAME VARCHAR(16777216),
	INSPECTOR_NOTES VARCHAR(16777216)
)COMMENT='INSPECTION NOTES RAW'
;


-- 4. Inspection Issues (Sentiment/AI Results)
create or replace TABLE AI_FOR_GOOD.AI_HOME_INSPECTION.INSPECTION_LOGS_ISSUES (
	INSPECTION_ID NUMBER(38,0),
	INSPECTOR_NOTES VARCHAR(16777216),
	NOTE_SENTIMENT VARCHAR(16777216),
	NOTE_DEFECT VARIANT
)COMMENT='Sentiment & Classification Detection of Inspection notes'
;


-- 5. Raw Images Table
create or replace TABLE AI_FOR_GOOD.AI_HOME_INSPECTION.IMAGE_RAW (
	IMAGE_PATH VARCHAR(16777216),
	PROPERTY_ID VARCHAR(16777216),
	ROOM_NAME VARCHAR(16777216),
	IMAGE_NAME VARCHAR(16777216)
);


-- 6. Image Issues (AI Results)
create or replace TABLE AI_FOR_GOOD.AI_HOME_INSPECTION.IMAGE_ISSUES (
	IMAGE_PATH VARCHAR(16777216),
	IMAGE_NAME VARCHAR(16777216),
	IMAGE_DEFECT VARIANT
);




-- 7A. Streams
CREATE OR REPLACE STREAM IMAGE_RAW_STREAM
    ON TABLE IMAGE_RAW
    APPEND_ONLY = TRUE;

CREATE OR REPLACE STREAM INSPECTION_LOGS_STREAM
    ON TABLE INSPECTION_LOGS
    APPEND_ONLY = TRUE;


-- 7B. Tasks for AI Processing
CREATE OR REPLACE TASK TASK_PROCESS_IMAGES
    WAREHOUSE = AI_INSPECTION_WH
    SCHEDULE = '60 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('IMAGE_RAW_STREAM')
AS
    -- Insert your AI model processing here
    MERGE INTO IMAGE_ISSUES AS target
    USING (
        SELECT
           image_path,
           image_name,
           AI_CLASSIFY(
             TO_FILE('@RAW_DATA_IMAGES', image_name),
             ['crack','mold','leak','exposed_wiring','no damage','termite'],{'output_mode': 'multi'}
           ) AS image_defect
        FROM IMAGE_RAW_STREAM
    ) AS source
    ON target.IMAGE_NAME = source.IMAGE_NAME
    WHEN MATCHED THEN UPDATE SET 
        target.IMAGE_PATH = source.IMAGE_PATH,
        target.IMAGE_DEFECT = source.IMAGE_DEFECT
    WHEN NOT MATCHED THEN INSERT (IMAGE_NAME, IMAGE_PATH, IMAGE_DEFECT)
        VALUES (source.IMAGE_NAME, source.IMAGE_PATH, source.IMAGE_DEFECT);

--SUSPEND TASK_PROCESS_IMAGES
ALTER TASK IF EXISTS TASK_PROCESS_IMAGES SUSPEND;
CREATE OR REPLACE TASK TASK_PROCESS_INSPECTION_LOGS
    WAREHOUSE = AI_INSPECTION_WH
    SCHEDULE = '60 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('INSPECTION_LOGS_STREAM')
AS
    MERGE INTO INSPECTION_LOGS_ISSUES AS target
    USING (
        SELECT inspection_id,
               inspector_notes,
               AI_CLASSIFY(inspector_notes,['crack','mold','leak','exposed_wiring','no damage','termite'],
               {'output_mode': 'multi'}) AS note_defect,
               AI_SENTIMENT(inspector_notes):categories[0].sentiment AS note_sentiment
        FROM INSPECTION_LOGS_STREAM
    ) AS source
    ON target.INSPECTION_ID = source.INSPECTION_ID
    WHEN MATCHED THEN UPDATE SET 
        target.INSPECTOR_NOTES = source.INSPECTOR_NOTES,
        target.NOTE_DEFECT = source.NOTE_DEFECT,
        target.NOTE_SENTIMENT = source.NOTE_SENTIMENT
    WHEN NOT MATCHED THEN INSERT 
        (INSPECTION_ID, INSPECTOR_NOTES, NOTE_DEFECT, NOTE_SENTIMENT)
        VALUES (source.INSPECTION_ID, source.INSPECTOR_NOTES, 
                source.NOTE_DEFECT, source.NOTE_SENTIMENT);




-- 8. Dynamic Tables for Risk Aggregation
-- Room-level risk scores (aggregates from processed issues)
CREATE OR REPLACE DYNAMIC TABLE ROOM_RISK_SCORE_DT
    TARGET_LAG = '1 HOUR'
    WAREHOUSE = AI_INSPECTION_WH
    COMMENT = 'Calculates normalized risk scores per room type for each property.'
AS
WITH 
-- Extract all defects from images
image_defects AS (
  SELECT
    ir.property_id,
    ir.room_name,
    d.value::string AS defect
  FROM image_issues i
  JOIN image_raw ir
    ON i.image_name = ir.image_name
  , LATERAL FLATTEN(input => i.image_defect:labels) d
),
-- Extract all defects from inspection notes
note_defects AS (
  SELECT
    il.property_id,
    il.room_name,
    n.value::string AS defect
  FROM inspection_logs_issues ili
  JOIN inspection_logs il
    ON ili.inspection_id = il.inspection_id
  , LATERAL FLATTEN(input => ili.note_defect:labels) n
),
-- Combine defects from both sources, removing duplicates
all_defects AS (
  SELECT * FROM image_defects
  UNION 
  SELECT * FROM note_defects
),
-- Define severity weights for each defect type
defect_weights AS (
  SELECT 'exposed_wiring' AS defect, 5 AS severity
  UNION ALL SELECT 'leak', 4
  UNION ALL SELECT 'crack', 3
  UNION ALL SELECT 'termite', 4
  UNION ALL SELECT 'mold', 2
  UNION ALL SELECT 'no damage', 0
),
-- Calculate raw severity scores
raw_scores AS (
  SELECT
    a.property_id,
    a.room_name,
    SUM(w.severity) AS raw_severity_score
  FROM all_defects a
  JOIN defect_weights w
    ON LOWER(a.defect) = LOWER(w.defect)
  GROUP BY a.property_id, a.room_name
)
-- Final output with normalized scores
SELECT
  rs.property_id,
  rs.room_name,
  ROUND(rs.raw_severity_score / NULLIF(r.room_count, 0), 2) AS room_severity_score,
  r.room_count AS rooms_of_this_type,
  rs.raw_severity_score AS raw_score_before_normalization
FROM raw_scores rs
JOIN ROOMS r 
  ON rs.property_id = r.property_id
  AND rs.room_name = r.room_name;

-- Property-level risk scores (aggregates from room scores)
CREATE OR REPLACE DYNAMIC TABLE PROPERTY_RISK_SCORE_DT
    TARGET_LAG = '2 HOURS'
    WAREHOUSE = AI_INSPECTION_WH
AS
SELECT
  property_id,
  SUM(room_severity_score) AS total_property_severity_score,
  CASE
    WHEN SUM(room_severity_score) >= 20 THEN 'High'
    WHEN SUM(room_severity_score) >= 10 THEN 'Medium'
    ELSE 'Low'
  END AS risk_category
FROM ROOM_RISK_SCORE_DT
GROUP BY property_id;
