"""
Stracture-Master - CLI Module
Professional command-line interface with rich output.
"""

import sys
import os
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import Config, ExportFormat, LogLevel
from src.modules.logger import Logger
from src.modules.parser import StructureParser
from src.modules.validator import StructureValidator
from src.modules.scanner import ProjectScanner
from src.modules.content_extractor import ContentExtractor
from src.modules.builder import StructureBuilder
from src.modules.exporter import Exporter
from src.modules.profile_manager import ProfileManager
from src.modules.diff_compare import DiffCompare
from src.modules.security import SecurityManager
from src.modules.file_analyzer import FileAnalyzer

console = Console()


def setup_logging(log_level: str) -> Logger:
    """Setup logging with specified level."""
    level = LogLevel.from_string(log_level)
    logger = Logger.get_instance()
    logger.set_level(level)
    return logger


def print_banner():
    """Print application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗████████╗██████╗ ██╗   ██╗ ██████╗████████╗██╗   ██╗║
║   ██╔════╝╚══██╔══╝██╔══██╗██║   ██║██╔════╝╚══██╔══╝██║   ██║║
║   ███████╗   ██║   ██████╔╝██║   ██║██║        ██║   ██║   ██║║
║   ╚════██║   ██║   ██╔══██╗██║   ██║██║        ██║   ██║   ██║║
║   ███████║   ██║   ██║  ██║╚██████╔╝╚██████╗   ██║   ╚██████╔╝║
║   ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝   ╚═╝    ╚═════╝ ║
║                     ██████╗ ███╗   ███╗ █████╗ ███████╗████████╗
║                     ██╔══██╗████╗ ████║██╔══██╗██╔════╝╚══██╔══╝
║                     ██████╔╝██╔████╔██║███████║███████╗   ██║   
║                     ██╔══██╗██║╚██╔╝██║██╔══██║╚════██║   ██║   
║                     ██║  ██║██║ ╚═╝ ██║██║  ██║███████║   ██║   
║                     ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   
║                                               v1.0.0           ║
╚═══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold blue")


@click.group()
@click.option('--log-level', '-l', 
              type=click.Choice(['trace', 'debug', 'info', 'warn', 'error']),
              default='info', help='Logging level')
@click.pass_context
def cli(ctx, log_level):
    """Stracture-Master - Project Structure Analysis & Documentation Tool"""
    ctx.ensure_object(dict)
    ctx.obj['logger'] = setup_logging(log_level)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', 
              type=click.Choice(['json', 'txt', 'md', 'yaml', 'html']),
              default='json', help='Output format')
@click.option('--include-hidden', '-h', is_flag=True, help='Include hidden files')
@click.option('--no-recursive', is_flag=True, help='Don\'t scan recursively')
@click.pass_context
def scan(ctx, path, output, format, include_hidden, no_recursive):
    """Scan a project and extract its structure."""
    print_banner()
    console.print(f"\n[bold cyan]📂 Scanning:[/] {path}\n")
    
    scanner = ProjectScanner()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning project...", total=None)
        
        result = scanner.scan(
            Path(path),
            recursive=not no_recursive,
            include_hidden=include_hidden
        )
        
        progress.update(task, completed=100)
    
    if not result.success:
        console.print(f"[red]❌ Scan failed:[/] {', '.join(result.errors)}")
        return
    
    # Show statistics
    table = Table(title="📊 Scan Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Project Type", result.project_type.name)
    table.add_row("Total Files", str(result.stats['total_files']))
    table.add_row("Total Directories", str(result.stats['total_directories']))
    table.add_row("Total Size", f"{result.stats['total_size']:,} bytes")
    table.add_row("Binary Files", str(result.stats['binary_files']))
    table.add_row("Scan Time", f"{result.stats['scan_time_ms']} ms")
    
    console.print(table)
    
    # Export if output specified
    if output:
        format_map = {
            'json': ExportFormat.JSON,
            'txt': ExportFormat.TXT,
            'md': ExportFormat.MARKDOWN,
            'yaml': ExportFormat.YAML,
            'html': ExportFormat.HTML,
        }
        
        exporter = Exporter()
        export_result = exporter.export_structure(
            result.structure,
            Path(output),
            format_map[format]
        )
        
        if export_result.success:
            console.print(f"\n[green]✅ Structure saved to:[/] {output}")
        else:
            console.print(f"\n[red]❌ Export failed:[/] {', '.join(export_result.errors)}")
    else:
        # Display tree
        console.print("\n[bold]📁 Project Structure:[/]\n")
        tree = build_rich_tree(result.structure, Path(path).name)
        console.print(tree)


@cli.command()
@click.argument('structure_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), default='./output',
              help='Output directory')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing files')
@click.option('--dry-run', '-d', is_flag=True, help='Preview without creating')
@click.pass_context
def build(ctx, structure_file, output, force, dry_run):
    """Build project structure from a structure file."""
    print_banner()
    console.print(f"\n[bold cyan]🔨 Building from:[/] {structure_file}")
    console.print(f"[bold cyan]📁 Output:[/] {output}\n")
    
    if dry_run:
        console.print("[yellow]⚠️  DRY RUN MODE - No changes will be made[/]\n")
    
    # Parse structure file
    parser = StructureParser()
    parse_result = parser.parse_file(Path(structure_file))
    
    if not parse_result.success:
        console.print(f"[red]❌ Parse error:[/] {', '.join(parse_result.errors)}")
        return
    
    # Validate
    validator = StructureValidator()
    val_result = validator.validate(parse_result.structure, Path(output))
    
    if not val_result.is_valid:
        console.print("[red]❌ Validation errors:[/]")
        for issue in val_result.errors:
            console.print(f"  • {issue.message} ({issue.path})")
        if not force:
            return
    
    # Build
    builder = StructureBuilder()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building structure...", total=None)
        
        result = builder.build(
            parse_result.structure,
            Path(output),
            force=force,
            dry_run=dry_run
        )
        
        progress.update(task, completed=100)
    
    # Show results
    table = Table(title="📊 Build Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Directories Created", str(result.stats['directories_created']))
    table.add_row("Files Created", str(result.stats['files_created']))
    table.add_row("Items Skipped", str(result.stats['items_skipped']))
    table.add_row("Errors", str(result.stats['errors']))
    table.add_row("Build Time", f"{result.stats['build_time_ms']} ms")
    
    console.print(table)
    
    if result.success:
        console.print(f"\n[green]✅ Structure built successfully at:[/] {output}")
    else:
        console.print(f"\n[red]❌ Build failed with errors[/]")
        for error in result.errors:
            console.print(f"  • {error}")


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), required=True,
              help='Output file path')
@click.option('--content', '-c', is_flag=True, help='Extract file contents')
@click.option('--format', '-f',
              type=click.Choice(['json', 'txt', 'md', 'html', 'zip']),
              default='txt', help='Output format')
@click.option('--encrypt', '-e', is_flag=True, help='Encrypt output')
@click.option('--password', '-p', type=str, help='Encryption password')
@click.option('--profile', type=str, help='Use a profile')
@click.pass_context
def extract(ctx, path, output, content, format, encrypt, password, profile):
    """Extract project structure and content."""
    print_banner()
    console.print(f"\n[bold cyan]📦 Extracting:[/] {path}")
    console.print(f"[bold cyan]📁 Output:[/] {output}\n")
    
    # Load profile if specified
    if profile:
        pm = ProfileManager()
        profile_data = pm.get(profile)
        if profile_data:
            console.print(f"[cyan]📋 Using profile:[/] {profile}")
            content = profile_data.extract_content
            encrypt = profile_data.encrypt_output
    
    # Scan project
    scanner = ProjectScanner()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning project...", total=None)
        scan_result = scanner.scan(Path(path))
        progress.update(task, completed=100)
    
    if not scan_result.success:
        console.print(f"[red]❌ Scan failed:[/] {', '.join(scan_result.errors)}")
        return
    
    # Extract content if requested
    files = []
    if content:
        extractor = ContentExtractor()
        
        # Ask user confirmation
        console.print(f"\n[yellow]📄 Found {len(scan_result.files)} files[/]")
        if not click.confirm("Extract file contents?", default=True):
            content = False
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Extracting content...", total=None)
                extract_result = extractor.extract(scan_result.files)
                files = extract_result.files
                progress.update(task, completed=100)
    
    # Check encryption
    if encrypt and not password:
        password = click.prompt("Enter encryption password", hide_input=True)
    
    # Export
    format_map = {
        'json': ExportFormat.JSON,
        'txt': ExportFormat.TXT,
        'md': ExportFormat.MARKDOWN,
        'html': ExportFormat.HTML,
        'zip': ExportFormat.ZIP,
    }
    
    exporter = Exporter()
    
    if content and files:
        export_result = exporter.export_content(
            files,
            Path(output),
            format=format_map[format],
            encrypt=encrypt,
            password=password
        )
    else:
        export_result = exporter.export_structure(
            scan_result.structure,
            Path(output),
            format_map[format]
        )
    
    if export_result.success:
        console.print(f"\n[green]✅ Export complete:[/] {output}")
        if encrypt:
            console.print("[yellow]🔐 Output is encrypted[/]")
    else:
        console.print(f"\n[red]❌ Export failed:[/] {', '.join(export_result.errors)}")


@cli.command()
@click.argument('old_path', type=click.Path(exists=True))
@click.argument('new_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file')
@click.option('--format', '-f',
              type=click.Choice(['md', 'json', 'html']),
              default='md', help='Output format')
@click.pass_context
def compare(ctx, old_path, new_path, output, format):
    """Compare two project structures."""
    print_banner()
    console.print(f"\n[bold cyan]🔄 Comparing:[/]")
    console.print(f"  Old: {old_path}")
    console.print(f"  New: {new_path}\n")
    
    diff = DiffCompare()
    result = diff.compare_directories(Path(old_path), Path(new_path))
    
    # Show summary
    table = Table(title="📊 Comparison Results", show_header=True)
    table.add_column("Change Type", style="cyan")
    table.add_column("Count", style="green")
    
    table.add_row("[green]Added[/]", str(result.stats['added']))
    table.add_row("[red]Removed[/]", str(result.stats['removed']))
    table.add_row("[yellow]Modified[/]", str(result.stats['modified']))
    table.add_row("Unchanged", str(result.stats['unchanged']))
    
    console.print(table)
    
    # Export if output specified
    if output:
        if format == 'md':
            content = diff.to_markdown(result)
        elif format == 'json':
            content = diff.to_json(result)
        else:
            content = diff.to_html(result)
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"\n[green]✅ Report saved to:[/] {output}")
    else:
        # Show changes
        if result.added_items:
            console.print("\n[bold green]➕ Added:[/]")
            for item in result.added_items[:10]:
                console.print(f"  • {item.path}")
            if len(result.added_items) > 10:
                console.print(f"  ... and {len(result.added_items) - 10} more")
        
        if result.removed_items:
            console.print("\n[bold red]➖ Removed:[/]")
            for item in result.removed_items[:10]:
                console.print(f"  • {item.path}")
            if len(result.removed_items) > 10:
                console.print(f"  ... and {len(result.removed_items) - 10} more")


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file')
@click.pass_context
def analyze(ctx, path, output):
    """Analyze code quality and metrics."""
    print_banner()
    console.print(f"\n[bold cyan]📊 Analyzing:[/] {path}\n")
    
    analyzer = FileAnalyzer()
    results = analyzer.analyze_directory(Path(path))
    
    # Show summary
    table = Table(title="📊 Code Analysis Results", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Files Analyzed", str(results['totals']['files']))
    table.add_row("Lines of Code", f"{results['totals']['lines_of_code']:,}")
    table.add_row("Blank Lines", f"{results['totals']['blank_lines']:,}")
    table.add_row("Comment Lines", f"{results['totals']['comment_lines']:,}")
    table.add_row("Total Lines", f"{results['totals']['total_lines']:,}")
    table.add_row("Functions", str(results['totals']['functions']))
    table.add_row("Classes", str(results['totals']['classes']))
    table.add_row("TODOs", str(results['totals']['todos']))
    table.add_row("FIXMEs", str(results['totals']['fixmes']))
    
    console.print(table)
    
    # Languages breakdown
    if results['by_language']:
        lang_table = Table(title="📝 By Language", show_header=True)
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Files", style="green")
        lang_table.add_column("Lines of Code", style="green")
        
        for lang, stats in sorted(results['by_language'].items(),
                                  key=lambda x: x[1]['lines_of_code'],
                                  reverse=True):
            lang_table.add_row(lang, str(stats['files']), f"{stats['lines_of_code']:,}")
        
        console.print("\n")
        console.print(lang_table)
    
    if output:
        import json
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]✅ Analysis saved to:[/] {output}")


@cli.command()
@click.option('--clipboard', '-c', is_flag=True, help='Preview from clipboard')
@click.argument('file', type=click.Path(), required=False)
@click.pass_context
def preview(ctx, clipboard, file):
    """Preview structure from file or clipboard."""
    print_banner()
    
    parser = StructureParser()
    
    if clipboard:
        console.print("\n[bold cyan]📋 Reading from clipboard...[/]\n")
        result = parser.parse_clipboard()
    elif file:
        console.print(f"\n[bold cyan]📄 Reading from file:[/] {file}\n")
        result = parser.parse_file(Path(file))
    else:
        console.print("[red]Please specify --clipboard or provide a file[/]")
        return
    
    if not result.success:
        console.print(f"[red]❌ Parse error:[/] {', '.join(result.errors)}")
        return
    
    # Show stats
    console.print(f"[cyan]Format detected:[/] {result.format_detected.name}")
    console.print(f"[cyan]Files:[/] {result.stats.get('files', 0)}")
    console.print(f"[cyan]Directories:[/] {result.stats.get('directories', 0)}")
    
    # Show tree
    console.print("\n[bold]📁 Structure Preview:[/]\n")
    tree = build_rich_tree(result.structure, "root")
    console.print(tree)
    
    # Confirm
    if click.confirm("\nDo you want to use this structure?", default=True):
        console.print("[green]✅ Structure confirmed[/]")
    else:
        console.print("[yellow]❌ Structure rejected[/]")


@cli.command()
@click.pass_context
def profiles(ctx):
    """List and manage profiles."""
    print_banner()
    
    pm = ProfileManager()
    profile_list = pm.list_profiles()
    
    table = Table(title="📋 Available Profiles", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    
    for name in profile_list:
        info = pm.get_profile_info(name)
        if info:
            table.add_row(name, info.get('description', ''))
    
    console.print(table)


@cli.command()
@click.option('--export', '-e', type=click.Path(), help='Export logs to file')
@click.option('--format', '-f',
              type=click.Choice(['txt', 'json', 'html']),
              default='txt', help='Export format')
@click.option('--clear', is_flag=True, help='Clear logs')
@click.pass_context  
def log(ctx, export, format, clear):
    """View and export logs."""
    logger = ctx.obj['logger']
    
    if clear:
        logger.clear()
        console.print("[green]✅ Logs cleared[/]")
        return
    
    if export:
        if format == 'txt':
            success = logger.export_txt(Path(export))
        elif format == 'json':
            success = logger.export_json(Path(export))
        else:
            success = logger.export_html(Path(export))
        
        if success:
            console.print(f"[green]✅ Logs exported to:[/] {export}")
        else:
            console.print("[red]❌ Export failed[/]")
        return
    
    # Show recent logs
    entries = logger.get_entries(limit=50)
    
    if not entries:
        console.print("[yellow]No log entries[/]")
        return
    
    for entry in entries:
        level_colors = {
            'TRACE': 'dim',
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARN': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold red',
        }
        color = level_colors.get(entry.level.name, 'white')
        ts = entry.timestamp.strftime('%H:%M:%S')
        console.print(f"[dim]{ts}[/] [{color}]{entry.level.name:8}[/] {entry.message}")


def build_rich_tree(structure: dict, name: str = "root") -> Tree:
    """Build a Rich tree from structure dict."""
    tree = Tree(f"📁 [bold]{name}[/]")
    
    def add_items(parent: Tree, struct: dict):
        items = sorted(struct.items(), key=lambda x: (not isinstance(x[1], dict), x[0].lower()))
        for item_name, content in items:
            if isinstance(content, dict):
                branch = parent.add(f"📁 [cyan]{item_name}[/]")
                if content:
                    add_items(branch, content)
            else:
                ext = Path(item_name).suffix.lower()
                icon = get_file_icon(ext)
                parent.add(f"{icon} {item_name}")
    
    add_items(tree, structure)
    return tree


def get_file_icon(ext: str) -> str:
    """Get file icon based on extension."""
    icons = {
        '.py': '🐍',
        '.js': '📜',
        '.ts': '📘',
        '.jsx': '⚛️',
        '.tsx': '⚛️',
        '.html': '🌐',
        '.css': '🎨',
        '.scss': '🎨',
        '.json': '📋',
        '.md': '📝',
        '.txt': '📄',
        '.yaml': '⚙️',
        '.yml': '⚙️',
        '.xml': '📰',
        '.sql': '🗄️',
        '.sh': '🖥️',
        '.bat': '🖥️',
        '.ps1': '🖥️',
        '.go': '🔵',
        '.rs': '🦀',
        '.java': '☕',
        '.php': '🐘',
        '.rb': '💎',
        '.c': '⚙️',
        '.cpp': '⚙️',
        '.h': '⚙️',
        '.cs': '💜',
        '.swift': '🍎',
        '.kt': '🎯',
        '.vue': '💚',
        '.svelte': '🔥',
    }
    return icons.get(ext, '📄')


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()
