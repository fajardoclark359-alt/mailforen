#!/usr/bin/env python3
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from typing import Optional

from .core.config import settings
from .core.db import db
from .core.logger import logger

app = typer.Typer(
    name="mailforen",
    help="Advanced OSINT toolkit for email forensics and digital investigations",
    add_completion=False
)
console = Console()

# Sub-apps
case_app = typer.Typer(help="Case management")
email_app = typer.Typer(help="Email forensics and analysis")
domain_app = typer.Typer(help="Domain intelligence")
ip_app = typer.Typer(help="IP intelligence")
ct_app = typer.Typer(help="Certificate Transparency")
url_app = typer.Typer(help="URL analysis and tracing")
user_app = typer.Typer(help="Username/identity pivoting")
file_app = typer.Typer(help="File metadata analysis")
report_app = typer.Typer(help="Report generation")

app.add_typer(case_app, name="case")
app.add_typer(email_app, name="email")
app.add_typer(domain_app, name="domain")
app.add_typer(ip_app, name="ip")
app.add_typer(ct_app, name="ct")
app.add_typer(url_app, name="url")
app.add_typer(user_app, name="user")
app.add_typer(file_app, name="file")
app.add_typer(report_app, name="report")

@app.command()
def version():
    """Show version information"""
    console.print(Panel.fit(
        "[bold cyan]mailforen[/bold cyan] v0.1.0\n"
        "[yellow]Advanced OSINT toolkit for email forensics and digital investigations[/yellow]\n\n"
        "[red]⚠️  For authorized use only[/red]",
        title="Version"
    ))

@app.command()
def disclaimer():
    """Show disclaimer"""
    disclaimer_path = Path(__file__).parent.parent / "DISCLAIMER.md"
    if disclaimer_path.exists():
        console.print(disclaimer_path.read_text())
    else:
        console.print("[red]Disclaimer not found[/red]")

# Case commands
@case_app.command("new")
def case_new(
    name: str,
    target: Optional[str] = typer.Option(None, "--target", "-t", help="Target domain/email/IP"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Case description")
):
    """Create a new investigation case"""
    try:
        case_id = db.create_case(name, target, description)
        console.print(f"[green]✓[/green] Created case [bold]{name}[/bold] (ID: {case_id})")
    except Exception as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)

@case_app.command("list")
def case_list():
    """List all cases"""
    cases = db.list_cases()
    if not cases:
        console.print("[yellow]No cases found[/yellow]")
        return
    
    table = Table(title="Investigation Cases")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Target")
    table.add_column("Status")
    table.add_column("Created")
    
    for case in cases:
        table.add_row(
            str(case['id']),
            case['name'],
            case['target'] or "-",
            case['status'],
            case['created_at']
        )
    
    console.print(table)

@case_app.command("show")
def case_show(case_id: int):
    """Show case details and findings"""
    case = db.get_case(case_id)
    if not case:
        console.print(f"[red]✗[/red] Case {case_id} not found")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        f"[bold]{case['name']}[/bold]\n"
        f"Target: {case['target'] or 'N/A'}\n"
        f"Status: {case['status']}\n"
        f"Created: {case['created_at']}\n\n"
        f"{case['description'] or ''}",
        title=f"Case #{case['id']}"
    ))
    
    findings = db.get_findings(case_id)
    if findings:
        console.print(f"\n[bold]Findings ({len(findings)})[/bold]")
        for f in findings:
            risk_color = {"high": "red", "medium": "yellow", "low": "green", "info": "cyan"}.get(f['risk_level'], "white")
            console.print(f"  [{risk_color}]●[/] [{risk_color}]{f['risk_level'].upper()}[/] {f['module']} - {f['input_data']} ({f['timestamp']})")
    else:
        console.print("\n[yellow]No findings yet[/yellow]")

# Placeholder commands for modules
@email_app.command("headers")
def email_headers(analyze: bool = typer.Option(False), file: Optional[Path] = None):
    """Analyze email headers"""
    console.print("[yellow]Email header analysis - coming soon[/yellow]")
    console.print("[cyan]Use: mailforen email headers analyze <file.eml>[/cyan]")

@domain_app.command("intel")
def domain_intel(domain: str):
    """Domain intelligence gathering"""
    console.print(f"[yellow]Domain intelligence for {domain} - coming soon[/yellow]")

@ip_app.command("intel")
def ip_intel(ip: str):
    """IP intelligence gathering"""
    console.print(f"[yellow]IP intelligence for {ip} - coming soon[/yellow]")

@ct_app.command("search")
def ct_search(domain: str):
    """Search Certificate Transparency logs"""
    console.print(f"[yellow]CT search for {domain} - coming soon[/yellow]")

@url_app.command("trace")
def url_trace(url: str):
    """Trace URL redirects"""
    console.print(f"[yellow]URL tracing for {url} - coming soon[/yellow]")

@user_app.command("pivot")
def user_pivot(username: str):
    """Pivot on username across platforms"""
    console.print(f"[yellow]Username pivot for {username} - coming soon[/yellow]")

@file_app.command("meta")
def file_meta(file: Path):
    """Extract file metadata"""
    console.print(f"[yellow]File metadata extraction for {file} - coming soon[/yellow]")

@report_app.command("generate")
def report_generate(
    case_id: int = typer.Option(..., "--case-id"),
    format: str = typer.Option("html", "--format", "-f", help="Report format (html, markdown, pdf, json)")
):
    """Generate investigation report"""
    console.print(f"[yellow]Generating {format} report for case {case_id} - coming soon[/yellow]")

if __name__ == "__main__":
    app()
