#!/usr/bin/env python3
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .core.db import db
from .modules.email.auth import auth_checker
from .modules.email.headers import header_analyzer
from .modules.forensic.ct import ct_search
from .modules.forensic.domain import domain_intel
from .modules.forensic.filemeta import file_meta
from .modules.forensic.ip import ip_intel
from .modules.forensic.urltrace import url_tracer
from .reports.generator import report_generator

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
        f"[bold cyan]mailforen[/bold cyan] v{__version__}\n"
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
    target: str | None = typer.Option(None, "--target", "-t", help="Target domain/email/IP"),
    description: str | None = typer.Option(None, "--desc", "-d", help="Case description")
):
    """Create a new investigation case"""
    try:
        case_id = db.create_case(name, target, description)
        console.print(f"[green]✓[/green] Created case [bold]{name}[/bold] (ID: {case_id})")
    except Exception as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1) from e

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

# Email commands
@email_app.command("headers")
def email_headers(file: Path = typer.Argument(..., help="Path to .eml file"), 
                   case_id: int | None = typer.Option(None, "--case-id", "-c")):
    """Analyze email headers from .eml file"""
    if not file.exists():
        console.print(f"[red]✗[/red] File not found: {file}")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Analyzing headers from {file}...[/cyan]")
    results = header_analyzer.analyze_file(file)
    
    if "error" in results:
        console.print(f"[red]✗[/red] {results['error']}")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        f"[bold]From:[/bold] {results['from']}\n"
        f"[bold]To:[/bold] {results['to']}\n"
        f"[bold]Subject:[/bold] {results['subject']}\n"
        f"[bold]Date:[/bold] {results['date']}\n"
        f"[bold]Message-ID:[/bold] {results['message_id']}",
        title="Email Headers"
    ))
    
    if results['originating_ips']:
        console.print(f"\n[bold yellow]Originating IPs:[/bold yellow] {', '.join(results['originating_ips'])}")
    
    console.print(f"\n[bold]Received Chain ({len(results['received_chain'])} hops):[/bold]")
    for hop in results['received_chain']:
        console.print(f"  {hop['hop']}. {hop['raw'][:100]}...")
    
    if case_id:
        db.add_finding(case_id, "email.headers", str(file), results, "info")
        console.print(f"\n[green]✓[/green] Added to case {case_id}")

@email_app.command("auth")
def email_auth(domain: str = typer.Argument(...), case_id: int | None = typer.Option(None, "--case-id", "-c")):
    """Check SPF, DKIM, DMARC for a domain"""
    console.print(f"[cyan]Checking email authentication for {domain}...[/cyan]")
    results = auth_checker.check_all(domain)
    
    # SPF
    spf = results['spf']
    if spf['found']:
        console.print(f"[green]✓[/green] SPF: Found ({len(spf['records'])} record(s))")
        for r in spf['records']:
            console.print(f"  {r}")
    else:
        console.print("[red]✗[/red] SPF: Not found")
    
    # DMARC
    dmarc = results['dmarc']
    if dmarc['found']:
        console.print(f"[green]✓[/green] DMARC: Found ({len(dmarc['records'])} record(s))")
        for r in dmarc['records']:
            console.print(f"  {r}")
    else:
        console.print("[red]✗[/red] DMARC: Not found")
    
    # MX
    mx = results['mx']
    if mx['found']:
        console.print(f"[green]✓[/green] MX: Found ({len(mx['records'])} record(s))")
        for r in mx['records']:
            console.print(f"  {r['priority']} {r['exchange']}")
    else:
        console.print("[red]✗[/red] MX: Not found")
    
    if case_id:
        db.add_finding(case_id, "email.auth", domain, results, "medium" if not spf['found'] or not dmarc['found'] else "low")
        console.print(f"\n[green]✓[/green] Added to case {case_id}")

# Domain commands
@domain_app.command("intel")
def domain_intel_cmd(domain: str = typer.Argument(...), case_id: int | None = typer.Option(None, "--case-id", "-c")):
    """Gather domain intelligence"""
    console.print(f"[cyan]Gathering intelligence for {domain}...[/cyan]")
    results = domain_intel.get_all_records(domain)
    
    table = Table(title=f"DNS Records for {domain}")
    table.add_column("Type", style="cyan")
    table.add_column("Records")
    
    if results['a']:
        table.add_row("A", "\n".join(results['a']))
    if results['aaaa']:
        table.add_row("AAAA", "\n".join(results['aaaa']))
    if results['ns']:
        table.add_row("NS", "\n".join(results['ns']))
    if results['mx']:
        mx_str = "\n".join([f"{r['priority']} {r['host']}" for r in results['mx']])
        table.add_row("MX", mx_str)
    if results['txt']:
        table.add_row("TXT", "\n".join(results['txt'][:5]))
    
    console.print(table)
    
    if case_id:
        db.add_finding(case_id, "domain.intel", domain, results, "info")
        console.print(f"\n[green]✓[/green] Added to case {case_id}")

# IP commands
@ip_app.command("intel")
def ip_intel_cmd(ip: str = typer.Argument(...), case_id: int | None = typer.Option(None, "--case-id", "-c")):
    """Gather IP intelligence"""
    console.print(f"[cyan]Gathering intelligence for {ip}...[/cyan]")
    results = ip_intel.get_info(ip)
    
    console.print(Panel.fit(
        f"[bold]IP:[/bold] {results['ip']}\n"
        f"[bold]Reverse DNS:[/bold] {results['reverse_dns'] or 'N/A'}",
        title="IP Intelligence"
    ))
    
    # Try ipinfo
    asn_info = ip_intel.get_asn_info(ip)
    if asn_info:
        console.print(f"\n[bold]Organization:[/bold] {asn_info.get('org', 'N/A')}")
        console.print(f"[bold]Location:[/bold] {asn_info.get('city', '')} {asn_info.get('region', '')} {asn_info.get('country', '')}")
        console.print(f"[bold]ISP:[/bold] {asn_info.get('org', 'N/A')}")
    
    if case_id:
        db.add_finding(case_id, "ip.intel", ip, {**results, **asn_info}, "info")
        console.print(f"\n[green]✓[/green] Added to case {case_id}")

# CT commands
@ct_app.command("search")
def ct_search_cmd(domain: str = typer.Argument(...), case_id: int | None = typer.Option(None, "--case-id", "-c")):
    """Search Certificate Transparency logs"""
    console.print(f"[cyan]Searching CT logs for {domain}...[/cyan]")
    results = ct_search.search(domain)
    
    if "error" in results:
        console.print(f"[red]✗[/red] {results['error']}")
        raise typer.Exit(1)
    
    console.print(f"[green]✓[/green] Found {results['certificates_found']} certificates")
    console.print(f"[green]✓[/green] Found {len(results['unique_subdomains'])} unique subdomains")
    
    if results['unique_subdomains']:
        table = Table(title="Discovered Subdomains")
        table.add_column("Subdomain")
        for sub in results['unique_subdomains'][:50]:  # Limit display
            table.add_row(sub)
        console.print(table)
        if len(results['unique_subdomains']) > 50:
            console.print(f"[yellow]... and {len(results['unique_subdomains']) - 50} more[/yellow]")
    
    if case_id:
        db.add_finding(case_id, "ct.search", domain, results, "info")
        console.print(f"\n[green]✓[/green] Added to case {case_id}")

# URL commands
@url_app.command("trace")
def url_trace_cmd(url: str = typer.Argument(...), case_id: int | None = typer.Option(None, "--case-id", "-c")):
    """Trace URL redirects"""
    console.print(f"[cyan]Tracing redirects for {url}...[/cyan]")
    results = url_tracer.trace(url)
    
    if "error" in results:
        console.print(f"[red]✗[/red] {results['error']}")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        f"[bold]Original:[/bold] {results['original_url']}\n"
        f"[bold]Final:[/bold] {results['final_url']}\n"
        f"[bold]Redirects:[/bold] {results['total_redirects']}",
        title="URL Trace"
    ))
    
    table = Table(title="Redirect Chain")
    table.add_column("Step")
    table.add_column("Status")
    table.add_column("URL")
    
    for hop in results['redirect_chain']:
        table.add_row(str(hop['step']), str(hop['status_code']), hop['url'][:80])
    
    console.print(table)
    
    if case_id:
        db.add_finding(case_id, "url.trace", url, results, "info")
        console.print(f"\n[green]✓[/green] Added to case {case_id}")

# File commands
@file_app.command("meta")
def file_meta_cmd(file: Path = typer.Argument(...), case_id: int | None = typer.Option(None, "--case-id", "-c")):
    """Extract file metadata"""
    console.print(f"[cyan]Extracting metadata from {file}...[/cyan]")
    results = file_meta.extract(file)
    
    if "error" in results:
        console.print(f"[red]✗[/red] {results['error']}")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        f"[bold]Filename:[/bold] {results['filename']}\n"
        f"[bold]Size:[/bold] {results['size_human']} ({results['size_bytes']} bytes)\n"
        f"[bold]Created:[/bold] {results['created']}\n"
        f"[bold]Modified:[/bold] {results['modified']}",
        title="File Metadata"
    ))
    
    if results.get('exif'):
        console.print(f"\n[bold]EXIF Data ({len(results['exif'])} tags):[/bold]")
        for k, v in list(results['exif'].items())[:20]:
            console.print(f"  {k}: {v[:60]}")
    
    if case_id:
        db.add_finding(case_id, "file.meta", str(file), results, "info")
        console.print(f"\n[green]✓[/green] Added to case {case_id}")

# User commands
@user_app.command("pivot")
def user_pivot_cmd(username: str = typer.Argument(...), case_id: int | None = typer.Option(None, "--case-id", "-c")):
    """Pivot on username across platforms (passive checks)"""
    console.print(f"[cyan]Pivoting on username: {username}[/cyan]")
    console.print("[yellow]Note: This performs passive checks on public endpoints[/yellow]")
    
    # Basic passive checks
    results = {
        "username": username,
        "checks": []
    }
    
    # Could add more platforms here
    platforms = ["github.com", "twitter.com", "instagram.com", "reddit.com"]
    for platform in platforms:
        results["checks"].append({
            "platform": platform,
            "url": f"https://{platform}/{username}",
            "method": "passive_url_construction"
        })
    
    console.print(f"[green]✓[/green] Generated {len(platforms)} potential profile URLs")
    for check in results["checks"]:
        console.print(f"  • {check['url']}")
    
    if case_id:
        db.add_finding(case_id, "user.pivot", username, results, "info")
        console.print(f"\n[green]✓[/green] Added to case {case_id}")

# Report commands
@report_app.command("generate")
def report_generate_cmd(
    case_id: int = typer.Option(..., "--case-id", "-c"),
    format: str = typer.Option("html", "--format", "-f", help="Report format (html, markdown, pdf, json)")
):
    """Generate investigation report"""
    try:
        console.print(f"[cyan]Generating {format} report for case {case_id}...[/cyan]")
        filepath = report_generator.generate(case_id, format)
        console.print(f"[green]✓[/green] Report saved: {filepath}")
    except Exception as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1) from e

if __name__ == "__main__":
    app()
