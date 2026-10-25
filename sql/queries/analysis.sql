-- Question: What is the average earthquake magnitude and count per location?
-- Result grain: One row per location (location_source_id).
-- Aggregations apply to event records linked via location_source_id foreign key.

SELECT 
    l.source_id AS location_id,
    l.elevation AS location_elevation_meters,
    COUNT(e.event_id) AS total_earthquakes,
    ROUND(AVG(e.magnitude), 2) AS average_magnitude,
    ROUND(MAX(e.magnitude), 2) AS max_magnitude
FROM elevation_locations l
LEFT JOIN earthquake_events e ON l.source_id = e.location_source_id
GROUP BY l.source_id, l.elevation;