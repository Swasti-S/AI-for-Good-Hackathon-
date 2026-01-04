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
