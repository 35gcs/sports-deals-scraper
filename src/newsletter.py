"""Newsletter generation system using Jinja2 templates."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import Deal, NewsletterConfig, Sport, Category
from .ranker import DealRanker


class NewsletterGenerator:
    """Generates HTML and Markdown newsletters from deals data."""
    
    def __init__(self, config: NewsletterConfig):
        """Initialize newsletter generator with configuration."""
        self.config = config
        self.ranker = DealRanker(min_discount=config.min_discount_pct)
        
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates" / "newsletter"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['format_price'] = self._format_price
        self.env.filters['format_discount'] = self._format_discount
        self.env.filters['format_date'] = self._format_date
        self.env.filters['truncate'] = self._truncate_text
        self.env.filters['safe_url'] = self._safe_url
    
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
        template = self.env.get_template('newsletter.html')
        return template.render(**context)
    
    def _generate_markdown(self, context: Dict[str, Any]) -> str:
        """Generate Markdown newsletter."""
        template = self.env.get_template('newsletter.md')
        return template.render(**context)
    
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
    
    def _format_price(self, price: float) -> str:
        """Format price for display."""
        return f"${price:.2f}"
    
    def _format_discount(self, discount: float) -> str:
        """Format discount percentage."""
        return f"{discount:.0f}%"
    
    def _format_date(self, date: datetime) -> str:
        """Format date for display."""
        return date.strftime("%B %d, %Y")
    
    def _truncate_text(self, text: str, length: int = 100) -> str:
        """Truncate text to specified length."""
        if len(text) <= length:
            return text
        return text[:length-3] + "..."
    
    def _safe_url(self, url: str) -> str:
        """Ensure URL is safe for use in templates."""
        if not url:
            return "#"
        return str(url)
    
    def generate_deal_card_html(self, deal: Deal) -> str:
        """Generate HTML for a single deal card."""
        template = self.env.get_template('deal_card.html')
        return template.render(deal=deal)
    
    def generate_deal_card_markdown(self, deal: Deal) -> str:
        """Generate Markdown for a single deal card."""
        template = self.env.get_template('deal_card.md')
        return template.render(deal=deal)
    
    def generate_sport_section_html(self, sport: str, deals: List[Deal]) -> str:
        """Generate HTML for a sport section."""
        template = self.env.get_template('sport_section.html')
        return template.render(sport=sport, deals=deals)
    
    def generate_sport_section_markdown(self, sport: str, deals: List[Deal]) -> str:
        """Generate Markdown for a sport section."""
        template = self.env.get_template('sport_section.md')
        return template.render(sport=sport, deals=deals)
    
    def generate_category_section_html(self, category: str, deals: List[Deal]) -> str:
        """Generate HTML for a category section."""
        template = self.env.get_template('category_section.html')
        return template.render(category=category, deals=deals)
    
    def generate_category_section_markdown(self, category: str, deals: List[Deal]) -> str:
        """Generate Markdown for a category section."""
        template = self.env.get_template('category_section.md')
        return template.render(category=category, deals=deals)
    
    def generate_summary_html(self, summary: Dict[str, Any]) -> str:
        """Generate HTML for newsletter summary."""
        template = self.env.get_template('summary.html')
        return template.render(summary=summary)
    
    def generate_summary_markdown(self, summary: Dict[str, Any]) -> str:
        """Generate Markdown for newsletter summary."""
        template = self.env.get_template('summary.md')
        return template.render(summary=summary)
    
    def generate_header_html(self, title: str, subtitle: Optional[str], week: str) -> str:
        """Generate HTML for newsletter header."""
        template = self.env.get_template('header.html')
        return template.render(title=title, subtitle=subtitle, week=week)
    
    def generate_header_markdown(self, title: str, subtitle: Optional[str], week: str) -> str:
        """Generate Markdown for newsletter header."""
        template = self.env.get_template('header.md')
        return template.render(title=title, subtitle=subtitle, week=week)
    
    def generate_footer_html(self) -> str:
        """Generate HTML for newsletter footer."""
        template = self.env.get_template('footer.html')
        return template.render()
    
    def generate_footer_markdown(self) -> str:
        """Generate Markdown for newsletter footer."""
        template = self.env.get_template('footer.md')
        return template.render()
    
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
