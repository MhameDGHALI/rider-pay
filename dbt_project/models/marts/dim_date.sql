-- Dimension calendrier : une ligne par jour entre start_date et end_date (variables dbt).
with days as (
    select day_value as date_day
    from unnest(
        generate_date_array(
            date '{{ var("start_date") }}',
            date '{{ var("end_date") }}'
        )
    ) as day_value
)

select
    cast(format_date('%Y%m%d', date_day) as int64)   as date_key,
    date_day,
    extract(year from date_day)                      as calendar_year,
    extract(month from date_day)                     as calendar_month,
    format_date('%B', date_day)                      as month_name,
    extract(day from date_day)                       as day_of_month,
    extract(dayofweek from date_day)                 as day_of_week,      -- 1 = dimanche, 7 = samedi
    format_date('%A', date_day)                      as day_name,
    extract(dayofweek from date_day) in (1, 7)       as is_weekend,
    date_trunc(date_day, week(monday))               as week_start_date
from days