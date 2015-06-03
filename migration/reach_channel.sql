﻿-- compute geometry from aw_haltung_geo
WITH haltung_geo AS (SELECT gid, St_SetSRID(ST_GeomFromText('LINESTRING('||string_agg(y1::varchar||' '||x1::varchar, ',' ORDER BY seq)||')'),21781) AS geometry FROM sa.aw_haltung_geo GROUP BY gid)

INSERT INTO qgep.vw_qgep_reach(
  identifier,
  remark,
  length_effective, -- == haltungslaenge oder stranglaenge?
  year_of_construction,
  slope_per_mill, -- == gefaelle?
  progression_geometry,
  function_hierarchic,
  horizontal_positioning,
  clear_height,
  fk_pipe_profile,
  usage_current
)
SELECT
  name2,
  bemerkung,
  haltungslaenge,
  baujahr,
  gefaelle,
  geometry,
  fh.new,
  hp.new,
  NULLIF(COALESCE(profil_hoehe, profil_breite), 0),
  pp.obj_id,
  uc.new
  
FROM sa.aw_haltung haltung
LEFT JOIN haltung_geo geom on geom.gid = haltung.fid
LEFT JOIN sa.map_function_hierarchic fh ON haltung.id_funktion_hierarch = fh.old
LEFT JOIN sa.map_horizontal_positioning hp ON haltung.id_lagegenauigkeit = hp.old
LEFT JOIN sa.map_usage_current uc ON haltung.id_nutzungs_art = uc.old
LEFT JOIN sa.aw_profilart_tbd pa ON pa.id = haltung.id_profilart
-- Join the profile based on it's type and the height/width-ratio
-- This code has to match the code in profiles.sql
LEFT JOIN qgep.od_pipe_profile pp ON pp.profile_type =
  CASE WHEN pa.id=1 THEN 5377
     WHEN pa.id=2 THEN 3350
     WHEN pa.id=3 THEN 3353
     WHEN pa.id=4 THEN 5377
     WHEN pa.id=5 THEN 3357
     WHEN pa.id=6 THEN 3351
     WHEN pa.id=7 THEN 3353
  END
  AND pp.height_width_ratio = COALESCE(round(NULLIF(haltung.profil_hoehe, 0)/haltung.profil_breite, 2),1)
WHERE haltung.deleted <> 1;