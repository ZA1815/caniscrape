import click
from rich import print

@click.group()
def cli():
    """
    A cli tool for analyzing how hard a website is to scrape.
    """
    pass

@cli.command()
@click.argument('url')
def analyze(url: str):
    """
    Analyzes a single URL for scraping difficulty.
    """
    print(f'Analyzing: [bold blue]{url}[/bold blue]...')
    print(f'Analysis complete.')

if __name__ == '__main__':
    cli()