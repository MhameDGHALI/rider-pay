{% macro yn_to_bool(column_name) %}
    case {{ column_name }}
        when 'Y' then true
        when 'N' then false
    end
{% endmacro %}