"""
StructureMaster - Main Entry Point
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main entry point - launches CLI or GUI based on arguments."""
    if len(sys.argv) > 1 and sys.argv[1] != '--gui':
        # CLI mode
        from cli.cli import main as cli_main
        cli_main()
    else:
        # GUI mode
        try:
            from gui.main_window import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"GUI not available: {e}")
            print("Install PyQt6: pip install PyQt6")
            print("\nRunning CLI instead...")
            from cli.cli import main as cli_main
            cli_main()


if __name__ == '__main__':
    main()
