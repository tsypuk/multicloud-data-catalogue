import typer

from mcd_data_catalogue.providers.aws_storage import dynamo, rds

aws_app = typer.Typer()
aws_app.add_typer(dynamo.app, name="dynamodb")
aws_app.add_typer(rds.app, name="rds")
