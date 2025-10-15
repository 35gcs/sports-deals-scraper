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
