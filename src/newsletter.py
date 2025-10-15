"""Newsletter generation system that avoids external template dependencies."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Deal, NewsletterConfig, Sport, Category
from .ranker import DealRanker


class NewsletterGenerator:
    """Generates HTML and Markdown newsletters from deals data."""
    
    def __init__(self, config: NewsletterConfig):
        """Initialize newsletter generator with configuration."""
        self.config = config
        self.ranker = DealRanker(min_discount=config.min_discount_pct)
        
    def generate_newsletter(self, deals: List[Deal], week: str) -> Dict[str, str]:
        """Generate newsletter in all configured formats."""
        # Filter and rank deals
        filtered_deals = self._filter_deals(deals)
        ranked_deals = self.ranker.rank_deals(filtered_deals)
        
        # Group deals
        grouped_deals = self._group_deals(ranked_deals)
        
        # Prepare template context
        context = self._prepare_context(grouped_deals, week)
        
        # Generate newsletters
        newsletters = {}
        
        if 'html' in self.config.formats:
            newsletters['html'] = self._generate_html(context)

        if 'markdown' in self.config.formats:
            newsletters['markdown'] = self._generate_markdown(context)
        
        return newsletters
    
    def _filter_deals(self, deals: List[Deal]) -> List[Deal]:
        """Filter deals based on configuration."""
        filtered = deals
        
        # Filter by minimum discount
        if self.config.min_discount_pct > 0:
            filtered = [
                deal for deal in filtered 
                if deal.discount_pct is None or deal.discount_pct >= self.config.min_discount_pct
            ]
        
        # Filter by youth only
        if self.config.show_youth_only:
            filtered = [deal for deal in filtered if deal.youth_flag]
        
        # Limit total deals
        if self.config.max_deals_total > 0:
            filtered = filtered[:self.config.max_deals_total]
        
        return filtered
    
    def _group_deals(self, deals: List[Deal]) -> Dict[str, Any]:
        """Group deals by sport and category."""
        grouped = {}
        
        if self.config.group_by_sport:
            # Group by sport first
            sport_groups = self.ranker.get_top_deals_by_sport(deals, self.config.top_per_sport)
            
            for sport, sport_deals in sport_groups.items():
                if self.config.group_by_category:
                    # Group by category within sport
                    category_groups = self.ranker.get_top_deals_by_category(sport_deals, 5)
                    grouped[sport.value] = {
                        'sport': sport.value,
                        'categories': category_groups
                    }
                else:
                    grouped[sport.value] = {
                        'sport': sport.value,
                        'deals': sport_deals
                    }
        else:
            # Group by category only
            category_groups = self.ranker.get_top_deals_by_category(deals, self.config.top_per_sport)
            grouped['all'] = {
                'categories': category_groups
            }
        
        return grouped
    
    def _prepare_context(self, grouped_deals: Dict[str, Any], week: str) -> Dict[str, Any]:
        """Prepare template context."""
        # Calculate summary statistics
        all_deals = []
        for group in grouped_deals.values():
            if 'deals' in group:
                all_deals.extend(group['deals'])
            elif 'categories' in group:
                for category_deals in group['categories'].values():
                    all_deals.extend(category_deals)
        
        summary = self.ranker.get_deals_summary(all_deals)
        
        return {
            'title': self.config.title,
            'subtitle': self.config.subtitle,
            'week': week,
            'generated_at': datetime.utcnow(),
            'grouped_deals': grouped_deals,
            'summary': summary,
            'config': self.config,
            'total_deals': len(all_deals),
            'youth_deals': summary.get('youth_deals', 0),
            'avg_discount': summary.get('avg_discount', 0),
            'avg_price': summary.get('avg_price', 0),
        }
    
    def _generate_html(self, context: Dict[str, Any]) -> str:
        """Generate HTML newsletter."""
        lines = [
            "<html>",
            "  <head>",
            f"    <title>{context['title']} - Week {context['week']}</title>",
            "  </head>",
            "  <body>",
            f"    <h1>{context['title']}</h1>",
        ]

        if context.get('subtitle'):
            lines.append(f"    <h2>{context['subtitle']}</h2>")

        lines.append(f"    <p><strong>Week {context['week']}</strong></p>")
        lines.append("    <section>")
        lines.append("      <h3>Highlights</h3>")
        lines.append("      <ul>")
        lines.append(f"        <li>Total deals: {context['total_deals']}</li>")
        lines.append(f"        <li>Youth deals: {context['youth_deals']}</li>")
        lines.append(f"        <li>Average discount: {context['avg_discount']:.1f}%</li>")
        lines.append(f"        <li>Average price: ${context['avg_price']:.2f}</li>")
        lines.append("      </ul>")
        lines.append("    </section>")

        for sport_key, group in context['grouped_deals'].items():
            lines.append(f"    <section>")
            lines.append(f"      <h2>{sport_key.title()}</h2>")

            if 'categories' in group:
                for category, deals in group['categories'].items():
                    lines.append(f"      <h3>{category.title()}</h3>")
                    lines.extend(self._html_deal_list(deals))
            elif 'deals' in group:
                lines.extend(self._html_deal_list(group['deals']))

            lines.append("    </section>")

        lines.append("  </body>")
        lines.append("</html>")
        return "\n".join(lines)

    def _generate_markdown(self, context: Dict[str, Any]) -> str:
        """Generate Markdown newsletter."""
        lines = [f"# {context['title']}"]

        if context.get('subtitle'):
            lines.append(f"## {context['subtitle']}")

        lines.append(f"**Week {context['week']}**")
        lines.append("")
        lines.append("### Highlights")
        lines.append(f"- Total deals: {context['total_deals']}")
        lines.append(f"- Youth deals: {context['youth_deals']}")
        lines.append(f"- Average discount: {context['avg_discount']:.1f}%")
        lines.append(f"- Average price: ${context['avg_price']:.2f}")
        lines.append("")

        for sport_key, group in context['grouped_deals'].items():
            lines.append(f"## {sport_key.title()}")
            if 'categories' in group:
                for category, deals in group['categories'].items():
                    lines.append(f"### {category.title()}")
                    lines.extend(self._markdown_deal_list(deals))
            elif 'deals' in group:
                lines.extend(self._markdown_deal_list(group['deals']))
            lines.append("")

        return "\n".join(lines)
    
    def save_newsletter(self, newsletters: Dict[str, str], week: str) -> Dict[str, Path]:
        """Save newsletters to files."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        for format_name, content in newsletters.items():
            filename = f"digest-{week}.{format_name}"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files[format_name] = filepath
        
        return saved_files

    def _html_deal_list(self, deals: List[Deal]) -> List[str]:
        lines = ["      <ul>"]
        for deal in deals:
            price = self._format_price(float(deal.price))
            discount = self._format_discount(deal.discount_pct)
            lines.append(
                f"        <li><strong>{deal.title}</strong> - {price} ({discount}) at {deal.retailer}</li>"
            )
        lines.append("      </ul>")
        return lines

    def _markdown_deal_list(self, deals: List[Deal]) -> List[str]:
        lines: List[str] = []
        for deal in deals:
            price = self._format_price(float(deal.price))
            discount = self._format_discount(deal.discount_pct)
            lines.append(
                f"- **{deal.title}** — {price} ({discount}) at {deal.retailer}"
            )
        return lines

    def _format_price(self, price: float) -> str:
        """Format price for display."""
        return f"${price:.2f}"

    def _format_discount(self, discount: Optional[float]) -> str:
        """Format discount percentage."""
        if discount is None:
            return "N/A"
        return f"{discount:.0f}%"

    
    def generate_deal_card_html(self, deal: Deal) -> str:
        """Generate HTML for a single deal card."""
        return (
            f"<div class=\"deal-card\">"
            f"<h3>{deal.title}</h3>"
            f"<p><strong>Price:</strong> ${float(deal.price):.2f}</p>"
            f"<p><strong>Retailer:</strong> {deal.retailer}</p>"
            "</div>"
        )
    
    def generate_deal_card_markdown(self, deal: Deal) -> str:
        """Generate Markdown for a single deal card."""
        lines = [f"### {deal.title}"]
        lines.append(f"- Price: ${float(deal.price):.2f}")
        lines.append(f"- Retailer: {deal.retailer}")
        return "\n".join(lines)
    
    def generate_sport_section_html(self, sport: str, deals: List[Deal]) -> str:
        """Generate HTML for a sport section."""
        lines = [f"<section><h2>{sport}</h2>"]
        lines.extend(self._html_deal_list(deals))
        lines.append("</section>")
        return "\n".join(lines)
    
    def generate_sport_section_markdown(self, sport: str, deals: List[Deal]) -> str:
        """Generate Markdown for a sport section."""
        lines = [f"## {sport}"]
        lines.extend(self._markdown_deal_list(deals))
        return "\n".join(lines)
    
    def generate_category_section_html(self, category: str, deals: List[Deal]) -> str:
        """Generate HTML for a category section."""
        lines = [f"<section><h3>{category}</h3>"]
        lines.extend(self._html_deal_list(deals))
        lines.append("</section>")
        return "\n".join(lines)
    
    def generate_category_section_markdown(self, category: str, deals: List[Deal]) -> str:
        """Generate Markdown for a category section."""
        lines = [f"### {category}"]
        lines.extend(self._markdown_deal_list(deals))
        return "\n".join(lines)
    
    def generate_summary_html(self, summary: Dict[str, Any]) -> str:
        """Generate HTML for newsletter summary."""
        lines = ["<section>"]
        lines.append("  <h2>Summary</h2>")
        lines.append("  <ul>")
        for key, value in summary.items():
            lines.append(f"    <li>{key.replace('_', ' ').title()}: {value}</li>")
        lines.append("  </ul>")
        lines.append("</section>")
        return "\n".join(lines)
    
    def generate_summary_markdown(self, summary: Dict[str, Any]) -> str:
        """Generate Markdown for newsletter summary."""
        lines = ["## Summary"]
        for key, value in summary.items():
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        return "\n".join(lines)
    
    def generate_header_html(self, title: str, subtitle: Optional[str], week: str) -> str:
        """Generate HTML for newsletter header."""
        subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
        return f"<header><h1>{title}</h1>{subtitle_html}<p>Week {week}</p></header>"
    
    def generate_header_markdown(self, title: str, subtitle: Optional[str], week: str) -> str:
        """Generate Markdown for newsletter header."""
        lines = [f"# {title}"]
        if subtitle:
            lines.append(f"## {subtitle}")
        lines.append(f"**Week {week}**")
        return "\n".join(lines)
    
    def generate_footer_html(self) -> str:
        """Generate HTML for newsletter footer."""
        return "<footer><p>Generated by Sports Deals Scraper</p></footer>"
    
    def generate_footer_markdown(self) -> str:
        """Generate Markdown for newsletter footer."""
        return "---\nGenerated by Sports Deals Scraper"
    
    def generate_newsletter_preview(self, deals: List[Deal], week: str) -> str:
        """Generate a preview of the newsletter."""
        # Generate full newsletter
        newsletters = self.generate_newsletter(deals, week)
        
        # Return HTML preview
        if 'html' in newsletters:
            return newsletters['html']
        elif 'markdown' in newsletters:
            return newsletters['markdown']
        else:
            return "No newsletter generated"
    
    def get_newsletter_stats(self, deals: List[Deal]) -> Dict[str, Any]:
        """Get statistics for newsletter generation."""
        filtered_deals = self._filter_deals(deals)
        grouped_deals = self._group_deals(filtered_deals)
        
        # Count deals by sport
        sport_counts = {}
        for sport, group in grouped_deals.items():
            if 'deals' in group:
                sport_counts[sport] = len(group['deals'])
            elif 'categories' in group:
                total = sum(len(deals) for deals in group['categories'].values())
                sport_counts[sport] = total
        
        # Count deals by category
        category_counts = {}
        for group in grouped_deals.values():
            if 'categories' in group:
                for category, deals in group['categories'].items():
                    category_counts[category] = category_counts.get(category, 0) + len(deals)
        
        return {
            'total_deals': len(filtered_deals),
            'sport_counts': sport_counts,
            'category_counts': category_counts,
            'sports_covered': len(sport_counts),
            'categories_covered': len(category_counts),
        }
