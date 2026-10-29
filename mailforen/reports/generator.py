import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from jinja2 import Template
from ..core.db import db
from ..core.config import settings
from ..core.logger import logger

class ReportGenerator:
    """Generate reports in multiple formats"""
    
    def __init__(self):
        self.reports_dir = settings.data_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, case_id: int, format: str = "html") -> Path:
        """Generate report for a case"""
        case = db.get_case(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        findings = db.get_findings(case_id)
        report_data = {
            "case": case,
            "findings": findings,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tool": "mailforen v0.1.0"
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{case['name'].replace(' ', '_')}_{timestamp}"
        
        if format == "json":
            return self.generate_json(report_data, filename)
        elif format == "markdown" or format == "md":
            return self.generate_markdown(report_data, filename)
        elif format == "html":
            return self.generate_html(report_data, filename)
        elif format == "pdf":
            return self.generate_pdf(report_data, filename)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def generate_json(self, data: Dict, filename: str) -> Path:
        filepath = self.reports_dir / f"{filename}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"JSON report saved: {filepath}")
        return filepath
    
    def generate_markdown(self, data: Dict, filename: str) -> Path:
        filepath = self.reports_dir / f"{filename}.md"
        md = f"""# Investigation Report

**Case:** {data['case']['name']}  
**Target:** {data['case']['target'] or 'N/A'}  
**Status:** {data['case']['status']}  
**Generated:** {data['generated_at']}  
**Tool:** {data['tool']}

## Description
{data['case']['description'] or 'No description provided.'}

## Findings ({len(data['findings'])})

"""
        for i, finding in enumerate(data['findings'], 1):
            md += f"""### {i}. {finding['module']} - {finding['input_data']}
- **Risk Level:** {finding['risk_level'].upper()}
- **Timestamp:** {finding['timestamp']}
- **Tags:** {', '.join(finding['tags']) if finding['tags'] else 'None'}
- **Notes:** {finding['notes'] or 'None'}

**Results:**
```json
{json.dumps(finding['result'], indent=2)}
```

"""
        with open(filepath, 'w') as f:
            f.write(md)
        logger.info(f"Markdown report saved: {filepath}")
        return filepath
    
    def generate_html(self, data: Dict, filename: str) -> Path:
        filepath = self.reports_dir / f"{filename}.html"
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>Investigation Report - {{ case.name }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 40px; }
        h1 { color: #d32f2f; border-bottom: 2px solid #d32f2f; }
        .meta { background: #f0f0f0; padding: 15px; margin: 20px 0; }
        .finding { border: 1px solid #ddd; margin: 20px 0; padding: 20px; }
        .risk-high { border-left: 4px solid #d32f2f; }
        .risk-medium { border-left: 4px solid #ff9800; }
        .risk-low { border-left: 4px solid #4caf50; }
        .risk-info { border-left: 4px solid #2196f3; }
        pre { background: #f5f5f5; padding: 15px; overflow-x: auto; }
        .disclaimer { background: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin-top: 40px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Investigation Report</h1>
        <div class="meta">
            <strong>Case:</strong> {{ case.name }}<br>
            <strong>Target:</strong> {{ case.target or 'N/A' }}<br>
            <strong>Status:</strong> {{ case.status }}<br>
            <strong>Generated:</strong> {{ generated_at }}<br>
            <strong>Tool:</strong> {{ tool }}
        </div>
        <h2>Description</h2>
        <p>{{ case.description or 'No description provided.' }}</p>
        <h2>Findings ({{ findings|length }})</h2>
        {% for finding in findings %}
        <div class="finding risk-{{ finding.risk_level }}">
            <h3>{{ loop.index }}. {{ finding.module }} - {{ finding.input_data }}</h3>
            <p><strong>Risk Level:</strong> {{ finding.risk_level.upper() }} | <strong>Timestamp:</strong> {{ finding.timestamp }}</p>
            <p><strong>Tags:</strong> {{ finding.tags|join(', ') if finding.tags else 'None' }}</p>
            <p><strong>Notes:</strong> {{ finding.notes or 'None' }}</p>
            <h4>Results:</h4>
            <pre>{{ finding.result | tojson(indent=2) }}</pre>
        </div>
        {% endfor %}
        <div class="disclaimer">
            <strong>⚠️ DISCLAIMER:</strong> This report is generated for authorized use only. Use of this tool for unauthorized investigations may be illegal.
        </div>
    </div>
</body>
</html>
        """)
        html = template.render(**data)
        with open(filepath, 'w') as f:
            f.write(html)
        logger.info(f"HTML report saved: {filepath}")
        return filepath
    
    def generate_pdf(self, data: Dict, filename: str) -> Path:
        filepath = self.reports_dir / f"{filename}.pdf"
        # Generate HTML first then convert
        html_path = self.generate_html(data, filename)
        try:
            try:
                from weasyhtml import HTML
                HTML(filename=str(html_path)).write_pdf(str(filepath))
            except ImportError:
                import pdfkit
                pdfkit.from_file(str(html_path), str(filepath))
            logger.info(f"PDF report saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            logger.info(f"HTML report available at: {html_path}")
            return html_path

report_generator = ReportGenerator()
