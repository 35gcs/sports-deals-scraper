#### {{ deal.title|truncate(80) }}
{% if deal.brand %}**Brand:** {{ deal.brand }}{% endif %}
**Price:** {{ deal.price|format_price }}{% if deal.msrp %} (was {{ deal.msrp|format_price }}){% endif %}{% if deal.discount_pct %} - **{{ deal.discount_pct|format_discount }} OFF**{% endif %}
**Retailer:** {{ deal.retailer }}
{% if deal.sizes %}**Sizes:** {{ deal.sizes|join(', ') }}{% endif %}
{% if deal.coupon_code and config.include_coupons %}**Coupon Code:** {{ deal.coupon_code }}{% endif %}
{% if deal.youth_flag %}**👶 Youth Item**{% endif %}
{% if deal.stock_level == 'limited' %}**⚠️ Limited Stock**{% endif %}
{% if deal.alternate_retailers %}**Also at:** {{ deal.alternate_retailers|join(', ') }}{% endif %}

[**View Deal →**]({{ deal.canonical_url|safe_url }})
