"""
Stracture-Master - Charts Module
Generate visual charts and diagrams for project analysis.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import base64


@dataclass
class ChartData:
    """Data for a chart."""
    chart_type: str
    title: str
    labels: List[str]
    values: List[float]
    colors: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.chart_type,
            'title': self.title,
            'labels': self.labels,
            'values': self.values,
            'colors': self.colors,
        }


class ChartGenerator:
    """
    Generate charts and visualizations.
    Supports HTML/SVG output and optional matplotlib.
    """
    
    # Color palettes
    PALETTE_DEFAULT = [
        '#667eea', '#764ba2', '#f59e0b', '#10b981', '#ef4444',
        '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16',
        '#f97316', '#14b8a6', '#a855f7', '#22c55e', '#eab308',
    ]
    
    PALETTE_DARK = [
        '#7c3aed', '#a855f7', '#f472b6', '#fb923c', '#4ade80',
        '#38bdf8', '#e879f9', '#f87171', '#34d399', '#fbbf24',
    ]
    
    def __init__(self, palette: Optional[List[str]] = None):
        """
        Initialize chart generator.
        
        Args:
            palette: Custom color palette
        """
        self.palette = palette or self.PALETTE_DEFAULT
        self._matplotlib_available = self._check_matplotlib()
    
    def _check_matplotlib(self) -> bool:
        """Check if matplotlib is available."""
        try:
            import matplotlib
            return True
        except ImportError:
            return False
    
    def pie_chart(self, 
                  data: Dict[str, float],
                  title: str = "Distribution",
                  output_path: Optional[Path] = None) -> str:
        """
        Generate a pie chart.
        
        Args:
            data: Dict of labels and values
            title: Chart title
            output_path: Optional file path to save
            
        Returns:
            SVG string or file path
        """
        labels = list(data.keys())
        values = list(data.values())
        total = sum(values)
        
        if total == 0:
            return self._empty_chart("No data")
        
        # Generate SVG
        svg = self._generate_pie_svg(labels, values, title)
        
        if output_path:
            output_path.write_text(svg, encoding='utf-8')
            return str(output_path)
        
        return svg
    
    def bar_chart(self,
                  data: Dict[str, float],
                  title: str = "Comparison",
                  horizontal: bool = False,
                  output_path: Optional[Path] = None) -> str:
        """
        Generate a bar chart.
        
        Args:
            data: Dict of labels and values
            title: Chart title
            horizontal: Horizontal bars
            output_path: Optional file path
            
        Returns:
            SVG string or file path
        """
        labels = list(data.keys())
        values = list(data.values())
        
        if not values:
            return self._empty_chart("No data")
        
        svg = self._generate_bar_svg(labels, values, title, horizontal)
        
        if output_path:
            output_path.write_text(svg, encoding='utf-8')
            return str(output_path)
        
        return svg
    
    def treemap(self,
                data: Dict[str, float],
                title: str = "Size Distribution",
                output_path: Optional[Path] = None) -> str:
        """
        Generate a treemap visualization.
        
        Args:
            data: Dict of labels and values (sizes)
            title: Chart title
            output_path: Optional file path
            
        Returns:
            SVG string or HTML
        """
        svg = self._generate_treemap_svg(data, title)
        
        if output_path:
            output_path.write_text(svg, encoding='utf-8')
            return str(output_path)
        
        return svg
    
    def line_chart(self,
                   data: Dict[str, List[float]],
                   labels: List[str],
                   title: str = "Trend",
                   output_path: Optional[Path] = None) -> str:
        """
        Generate a line chart.
        
        Args:
            data: Dict of series name to values
            labels: X-axis labels
            title: Chart title
            output_path: Optional file path
        """
        svg = self._generate_line_svg(data, labels, title)
        
        if output_path:
            output_path.write_text(svg, encoding='utf-8')
            return str(output_path)
        
        return svg
    
    def _generate_pie_svg(self, 
                          labels: List[str], 
                          values: List[float],
                          title: str) -> str:
        """Generate SVG pie chart."""
        width, height = 500, 400
        cx, cy = 200, 200
        radius = 150
        
        total = sum(values)
        
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            f'<style>text {{ font-family: Arial, sans-serif; }}</style>',
            f'<text x="{width/2}" y="30" text-anchor="middle" font-size="18" font-weight="bold">{title}</text>',
        ]
        
        # Draw pie slices
        start_angle = 0
        for i, (label, value) in enumerate(zip(labels, values)):
            if value == 0:
                continue
            
            percentage = value / total
            angle = percentage * 360
            end_angle = start_angle + angle
            
            # Calculate path
            large_arc = 1 if angle > 180 else 0
            
            import math
            x1 = cx + radius * math.cos(math.radians(start_angle - 90))
            y1 = cy + radius * math.sin(math.radians(start_angle - 90))
            x2 = cx + radius * math.cos(math.radians(end_angle - 90))
            y2 = cy + radius * math.sin(math.radians(end_angle - 90))
            
            color = self.palette[i % len(self.palette)]
            
            path = f'M {cx},{cy} L {x1},{y1} A {radius},{radius} 0 {large_arc},1 {x2},{y2} Z'
            svg_parts.append(f'<path d="{path}" fill="{color}" stroke="white" stroke-width="2"/>')
            
            start_angle = end_angle
        
        # Legend
        legend_x = 360
        legend_y = 80
        
        for i, (label, value) in enumerate(zip(labels[:10], values[:10])):
            color = self.palette[i % len(self.palette)]
            pct = (value / total * 100) if total > 0 else 0
            
            svg_parts.append(
                f'<rect x="{legend_x}" y="{legend_y + i*25}" '
                f'width="15" height="15" fill="{color}"/>'
            )
            svg_parts.append(
                f'<text x="{legend_x + 22}" y="{legend_y + i*25 + 12}" '
                f'font-size="11">{label[:15]} ({pct:.1f}%)</text>'
            )
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _generate_bar_svg(self,
                          labels: List[str],
                          values: List[float],
                          title: str,
                          horizontal: bool) -> str:
        """Generate SVG bar chart."""
        width, height = 600, 400
        margin = 60
        max_val = max(values) if values else 1
        
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            f'<style>text {{ font-family: Arial, sans-serif; }}</style>',
            f'<text x="{width/2}" y="30" text-anchor="middle" font-size="18" font-weight="bold">{title}</text>',
        ]
        
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin - 20
        
        bar_count = len(values)
        bar_width = (chart_width / bar_count) * 0.7
        bar_gap = (chart_width / bar_count) * 0.3
        
        for i, (label, value) in enumerate(zip(labels, values)):
            bar_height = (value / max_val) * chart_height if max_val > 0 else 0
            
            x = margin + i * (bar_width + bar_gap)
            y = margin + 20 + (chart_height - bar_height)
            
            color = self.palette[i % len(self.palette)]
            
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" '
                f'fill="{color}" rx="4"/>'
            )
            
            # Value label
            svg_parts.append(
                f'<text x="{x + bar_width/2}" y="{y - 5}" '
                f'text-anchor="middle" font-size="10">{value:.0f}</text>'
            )
            
            # Category label
            svg_parts.append(
                f'<text x="{x + bar_width/2}" y="{height - 10}" '
                f'text-anchor="middle" font-size="9" '
                f'transform="rotate(-45, {x + bar_width/2}, {height - 10})">'
                f'{label[:10]}</text>'
            )
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _generate_treemap_svg(self,
                              data: Dict[str, float],
                              title: str) -> str:
        """Generate SVG treemap."""
        width, height = 600, 400
        
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            f'<style>text {{ font-family: Arial, sans-serif; }}</style>',
            f'<text x="{width/2}" y="25" text-anchor="middle" font-size="18" font-weight="bold">{title}</text>',
        ]
        
        # Simple squarified treemap layout
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:20]
        total = sum(v for _, v in sorted_items)
        
        if total == 0:
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)
        
        # Simple row-based layout
        y = 40
        remaining_height = height - 50
        x = 10
        remaining_width = width - 20
        
        current_row_items = []
        current_row_width = 0
        row_height = 60
        
        for i, (label, value) in enumerate(sorted_items):
            item_width = (value / total) * (width - 20)
            
            if current_row_width + item_width > remaining_width:
                # Draw current row
                if current_row_items:
                    x_pos = 10
                    for j, (lbl, val, w) in enumerate(current_row_items):
                        color = self.palette[(i - len(current_row_items) + j) % len(self.palette)]
                        svg_parts.append(
                            f'<rect x="{x_pos}" y="{y}" width="{w-2}" height="{row_height-2}" '
                            f'fill="{color}" rx="4" stroke="white" stroke-width="1"/>'
                        )
                        if w > 50:
                            svg_parts.append(
                                f'<text x="{x_pos + w/2}" y="{y + row_height/2}" '
                                f'text-anchor="middle" font-size="10" fill="white">'
                                f'{lbl[:12]}</text>'
                            )
                        x_pos += w
                
                y += row_height
                current_row_items = []
                current_row_width = 0
            
            current_row_items.append((label, value, item_width))
            current_row_width += item_width
        
        # Draw remaining items
        if current_row_items:
            x_pos = 10
            for j, (lbl, val, w) in enumerate(current_row_items):
                color = self.palette[j % len(self.palette)]
                svg_parts.append(
                    f'<rect x="{x_pos}" y="{y}" width="{w-2}" height="{row_height-2}" '
                    f'fill="{color}" rx="4" stroke="white" stroke-width="1"/>'
                )
                if w > 50:
                    svg_parts.append(
                        f'<text x="{x_pos + w/2}" y="{y + row_height/2}" '
                        f'text-anchor="middle" font-size="10" fill="white">'
                        f'{lbl[:12]}</text>'
                    )
                x_pos += w
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _generate_line_svg(self,
                           data: Dict[str, List[float]],
                           labels: List[str],
                           title: str) -> str:
        """Generate SVG line chart."""
        width, height = 600, 400
        margin = 60
        
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            f'<style>text {{ font-family: Arial, sans-serif; }}</style>',
            f'<text x="{width/2}" y="30" text-anchor="middle" font-size="18" font-weight="bold">{title}</text>',
        ]
        
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin - 20
        
        # Find max value
        all_values = [v for series in data.values() for v in series]
        max_val = max(all_values) if all_values else 1
        
        # Draw grid lines
        for i in range(5):
            y = margin + 20 + (i * chart_height / 4)
            svg_parts.append(
                f'<line x1="{margin}" y1="{y}" x2="{width - margin}" y2="{y}" '
                f'stroke="#e5e7eb" stroke-width="1"/>'
            )
        
        # Draw lines
        for series_idx, (series_name, values) in enumerate(data.items()):
            color = self.palette[series_idx % len(self.palette)]
            points = []
            
            for i, value in enumerate(values):
                x = margin + (i / (len(values) - 1)) * chart_width if len(values) > 1 else margin
                y = margin + 20 + chart_height - (value / max_val) * chart_height
                points.append(f'{x},{y}')
            
            svg_parts.append(
                f'<polyline points="{" ".join(points)}" '
                f'fill="none" stroke="{color}" stroke-width="2"/>'
            )
            
            # Draw points
            for point in points:
                x, y = point.split(',')
                svg_parts.append(
                    f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>'
                )
        
        # X-axis labels
        for i, label in enumerate(labels):
            x = margin + (i / (len(labels) - 1)) * chart_width if len(labels) > 1 else margin
            svg_parts.append(
                f'<text x="{x}" y="{height - 10}" text-anchor="middle" font-size="10">'
                f'{label}</text>'
            )
        
        # Legend
        legend_y = 50
        for i, series_name in enumerate(data.keys()):
            color = self.palette[i % len(self.palette)]
            svg_parts.append(
                f'<rect x="{margin}" y="{legend_y + i*20}" '
                f'width="15" height="10" fill="{color}"/>'
            )
            svg_parts.append(
                f'<text x="{margin + 20}" y="{legend_y + i*20 + 9}" '
                f'font-size="11">{series_name}</text>'
            )
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)
    
    def _empty_chart(self, message: str) -> str:
        """Generate empty chart with message."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200">
            <text x="200" y="100" text-anchor="middle" font-family="Arial" 
                  font-size="16" fill="#666">{message}</text>
        </svg>'''
    
    def generate_html_report(self, 
                             charts: List[str],
                             title: str = "Project Analysis") -> str:
        """
        Generate HTML report with multiple charts.
        
        Args:
            charts: List of SVG strings
            title: Report title
            
        Returns:
            HTML string
        """
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #0f0f1a;
            color: #fff;
            margin: 0;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            color: #7c3aed;
        }}
        .charts-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .chart-card {{
            background: #1e1e38;
            border-radius: 16px;
            padding: 20px;
            border: 1px solid #3d3d5c;
        }}
        svg {{
            width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="charts-container">
'''
        
        for chart in charts:
            html += f'<div class="chart-card">{chart}</div>\n'
        
        html += '''    </div>
</body>
</html>'''
        
        return html


# Singleton instance
charts = ChartGenerator()
