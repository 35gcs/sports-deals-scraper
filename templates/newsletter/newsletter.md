# {{ title }}

{% if subtitle %}
## {{ subtitle }}
{% endif %}

**Week {{ week }}** • Generated on {{ generated_at|format_date }}

---

## 📊 This Week's Highlights

- **{{ summary.total_deals }}** total deals found
- **{{ summary.youth_deals }}** youth items
- **{{ summary.avg_discount }}%** average discount
- **${{ summary.avg_price }}** average price

{% if summary.top_sports %}
**Top Sports:** {{ summary.top_sports|map(attribute='0')|join(', ') }}
{% endif %}

{% if summary.top_brands %}
**Top Brands:** {{ summary.top_brands|map(attribute='0')|join(', ') }}
{% endif %}

---

{% for sport, group in grouped_deals.items() %}
## 🏈 {{ sport|title }} Deals

{% if group.categories %}
    {% for category, deals in group.categories.items() %}
### {{ category|title }}

{% for deal in deals %}
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

---
{% endfor %}
    {% endfor %}
{% else %}
{% for deal in group.deals %}
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

---
{% endfor %}
{% endif %}

{% endfor %}

---

## 📝 About This Newsletter

This newsletter is automatically generated from deals found across multiple sports retailers. All prices and availability are subject to change - always verify details on the retailer's website before making a purchase.

**Week {{ week }}** • {{ total_deals }} deals found • Generated on {{ generated_at|format_date }}

---

*Prices and availability subject to change. Always verify details on retailer websites.*
