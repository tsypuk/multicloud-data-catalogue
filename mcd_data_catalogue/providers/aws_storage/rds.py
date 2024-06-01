import typer

app = typer.Typer()


@app.command("create")
def users_create(user_name: str):
    print(f"Creating user: {user_name}")


@app.command("delete")
def users_delete(user_name: str):
    print(f"Deleting user: {user_name}")
