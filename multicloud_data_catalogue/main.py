import typer

from multicloud_data_catalogue.providers.aws import aws_app

app = typer.Typer()
app.add_typer(aws_app, name="aws")

if __name__ == "__main__":
    app()
