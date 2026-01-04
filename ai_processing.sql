

-----------------------------------------------------------
-- 1. AI Room Classification (Inspection Logs)
-----------------------------------------------------------

UPDATE INSPECTION_LOGS
SET ROOM_NAME = classified.room_label
FROM (
  SELECT
    INSPECTION_ID,
    AI_CLASSIFY(
      INSPECTOR_NOTES,
      ['Kitchen', 'Living Room', 'Bedroom', 'Balcony', 'Bathroom']
    ):labels[0] AS room_label
  FROM INSPECTION_LOGS
  WHERE ROOM_NAME IS NULL OR ROOM_NAME = ''
) classified
WHERE INSPECTION_LOGS.INSPECTION_ID = classified.INSPECTION_ID;

-----------------------------------------------------------
-- 2. AI defect classification (notes)
-----------------------------------------------------------

INSERT INTO INSPECTION_LOGS_ISSUES (INSPECTION_ID, INSPECTOR_NOTES, NOTE_DEFECT, NOTE_SENTIMENT)
SELECT 
    INSPECTION_ID,
    INSPECTOR_NOTES,
    -- Multi-label classification for defects
    AI_CLASSIFY(
        INSPECTOR_NOTES,
        ['crack','mold','leak','exposed_wiring','no damage','termite'],
        {'output_mode': 'multi'}
    ) AS NOTE_DEFECT,
    -- Sentiment analysis
    AI_SENTIMENT(INSPECTOR_NOTES):categories[0].sentiment AS NOTE_SENTIMENT
FROM INSPECTION_LOGS;

-----------------------------------------------------------
-- 3. Image Path Normalization
-----------------------------------------------------------

UPDATE IMAGE_RAW AS r
SET IMAGE_PATH = CONCAT('@RAW_DATA_IMAGES/', d.relative_path)
FROM DIRECTORY(@RAW_DATA_IMAGES) AS d
WHERE r.IMAGE_NAME = d.relative_path;

-----------------------------------------------------------
-- 4. AI Room Classification (Images)
-----------------------------------------------------------

UPDATE IMAGE_RAW AS r
SET ROOM_NAME = classified.room_label
FROM (
    SELECT
      d.relative_path AS image_filename,
      AI_CLASSIFY(
        TO_FILE('@RAW_DATA_IMAGES', d.relative_path),
        ['Kitchen', 'Living Room', 'Bedroom', 'Balcony', 'Bathroom']
      ):labels[0] AS room_label
    FROM DIRECTORY(@RAW_DATA_IMAGES) AS d
) AS classified
WHERE r.IMAGE_NAME = classified.image_filename;

-----------------------------------------------------------
-- 5. AI Defect classification (Images)
-----------------------------------------------------------


INSERT INTO IMAGE_ISSUES (IMAGE_PATH, IMAGE_NAME, IMAGE_DEFECT)
SELECT
   IMAGE_PATH,
   IMAGE_NAME,
   AI_CLASSIFY(
     TO_FILE('@RAW_DATA_IMAGES', IMAGE_NAME),
     ['crack','mold','leak','exposed_wiring','no damage','termite'],
     {'output_mode': 'multi'}
   ) AS IMAGE_DEFECT
FROM IMAGE_RAW
WHERE IMAGE_PATH IS NOT NULL;
