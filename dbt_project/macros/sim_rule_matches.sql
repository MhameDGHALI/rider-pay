{% macro sim_rule_matches(seg, rule) %}
    (
        (
            {{ rule }}.snow_condition = 'any'
            or ({{ rule }}.snow_condition = 'snow' and {{ seg }}.is_snowing)
        )
        and (
            {{ rule }}.day_type = 'any'
            or ({{ rule }}.day_type = 'weekend' and {{ seg }}.is_weekend)
            or ({{ rule }}.day_type = 'weekday' and not {{ seg }}.is_weekend)
        )
        and {{ seg }}.pickup_hour between {{ rule }}.hour_from and {{ rule }}.hour_to
        and (
            {{ rule }}.zone_condition = 'any'
            or ({{ rule }}.zone_condition = 'high_fee_zone' and {{ seg }}.is_high_fee_zone)
        )
        and (
            {{ rule }}.airport_condition = 'any'
            or ({{ rule }}.airport_condition = 'airport' and {{ seg }}.is_airport_trip)
        )
        and (
            {{ rule }}.operator = 'any'
            or {{ rule }}.operator = {{ seg }}.license_num
        )
    )
{% endmacro %}