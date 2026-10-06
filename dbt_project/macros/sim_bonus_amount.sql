{% macro sim_bonus_amount(seg, rule) %}
    case {{ rule }}.bonus_type
        when 'pct_of_pay'    then {{ rule }}.bonus_value * {{ seg }}.driver_pay_usd
        when 'flat_per_trip' then {{ rule }}.bonus_value * {{ seg }}.nb_trips
    end
{% endmacro %}