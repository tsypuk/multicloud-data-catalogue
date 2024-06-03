import boto3
import typer
from rich.console import Console
from rich.table import Table

from multicloud_diagrams import MultiCloudDiagrams

app = typer.Typer()
dynamodb_client = boto3.client('dynamodb')
console = Console()


@app.command("get")
def table_get(table_name: str):
    print(f"Getting table: {table_name}")
    table_details = crawl_aws(table_name)

    console.rule("Generic Details")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Key", style="dim", width=25)
    table.add_column("Value")
    table.add_row('ARN', table_details['arn'])
    table.add_row('Table_Name', table_details['table_name'])
    table.add_row('TableStatus', table_details['Table']['TableStatus'])
    table.add_row('CreationDateTime', table_details['Table']['CreationDateTime'])
    table.add_row('TableSizeBytes', f"{table_details['Table']['TableSizeBytes']}")
    table.add_row('ItemCount', f"{table_details['Table']['ItemCount']}")
    table.add_row('DeletionProtectionEnabled', f"{table_details['Table']['DeletionProtectionEnabled']}")
    console.print(table)

    # Key Schema
    console.rule("Key Schema")
    item_table = Table(show_header=True, header_style="bold magenta")
    column_width = 5
    item_table.add_column("Key", style="dim", width=column_width)
    item_table.add_column("Value")
    for index, value in enumerate(table_details['Table']['KeySchema']):
        item_table.add_row(f'{index}', f'{value}')
        # if len(index) > column_width:
        #     column_width = len(index)
    console.print(item_table)

    console.rule("SSE")
    # SSE
    if 'SSEDescription' in table_details['Table']:
        item_table = Table(show_header=True, header_style="bold magenta")
        column_width = 5
        item_table.add_column("Key", style="dim", width=column_width)
        item_table.add_column("Value")
        for (key, value) in table_details['Table']['SSEDescription'].items():
            item_table.add_row(f'{key}', f'{value}')
            if len(key) > column_width:
                column_width = len(key)

        item_table.columns[0].width = column_width
        console.print(item_table)
    else:
        print('NO SSE')

    # Item:
    console.rule("Item")
    item_table = Table(show_header=True, header_style="bold magenta")
    column_width = 5
    item_table.add_column("Key", style="dim", width=column_width)
    item_table.add_column("Value")
    for (key, value) in table_details['item'].items():
        item_table.add_row(f'{key}', f'{value}')
        if len(key) > column_width:
            column_width = len(key)

    item_table.columns[0].width = column_width
    console.print(item_table)


@app.command("drawio")
def table_drawio(table_name: str):
    print(f"Drawio table: {table_name}")


@app.command("list")
def list_tables():
    print("Listing tables...")
    response = dynamodb_client.list_tables()

    table_names = response['TableNames']

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Table name")
    for index, table_name in enumerate(table_names):
        table.add_row(
            f"#{index}", table_name
        )

    console.print(table)


def render_mcd(dynamo_details: dict):
    table_name = dynamo_details['table_name']
    mcd = MultiCloudDiagrams()
    data_file = f'../output/output.{table_name}.dynamo.drawio'
    mcd.read_coords_from_file(data_file)

    mcd.export_to_file(data_file)


def crawl_aws(table_name: str) -> dict:
    table_details = dynamodb_client.describe_table(TableName=table_name)

    # Check replicas
    # if 'Replicas' in table_details['Table']:
    #     StreamSpecification
    #     ArchivalSummary
    #     LatestStreamLabel': 'string',
    # 'LatestStreamArn': 'string',
    # 'GlobalTableVersion
    # SSEDescription

    # cleanup unserialized field
    del table_details['ResponseMetadata']

    table_details['Table']['CreationDateTime'] = table_details['Table']['CreationDateTime'].strftime("%Y-%m-%d %H:%M:%S")
    if 'BillingModeSummary' in table_details['Table']:
        table_details['Table']['BillingModeSummary']['LastUpdateToPayPerRequestDateTime'] = table_details['Table']['BillingModeSummary']['LastUpdateToPayPerRequestDateTime'].strftime(
            "%Y-%m-%d %H:%M:%S")

    if 'ProvisionedThroughput' in table_details['Table']:
        if 'LastIncreaseDateTime' in table_details['Table']['ProvisionedThroughput']:
            table_details['Table']['ProvisionedThroughput']['LastIncreaseDateTime'] = table_details['Table']['ProvisionedThroughput']['LastIncreaseDateTime'].strftime("%Y-%m-%d %H:%M:%S")
        if 'LastDecreaseDateTime' in table_details['Table']['ProvisionedThroughput']:
            table_details['Table']['ProvisionedThroughput']['LastDecreaseDateTime'] = table_details['Table']['ProvisionedThroughput']['LastDecreaseDateTime'].strftime("%Y-%m-%d %H:%M:%S")

    if 'GlobalSecondaryIndexes' in table_details['Table']:
        id = 0
        for index in table_details['Table']['GlobalSecondaryIndexes']:
            if 'LastIncreaseDateTime' in index['ProvisionedThroughput']:
                table_details['Table']['GlobalSecondaryIndexes'][id]['ProvisionedThroughput'][
                    'LastIncreaseDateTime'] = table_details['Table']['GlobalSecondaryIndexes'][id]['ProvisionedThroughput'][
                    'LastIncreaseDateTime'].strftime("%Y-%m-%d %H:%M:%S")
            if 'LastDecreaseDateTime' in index['ProvisionedThroughput']:
                table_details['Table']['GlobalSecondaryIndexes'][id]['ProvisionedThroughput'][
                    'LastDecreaseDateTime'] = table_details['Table']['GlobalSecondaryIndexes'][id]['ProvisionedThroughput'][
                    'LastDecreaseDateTime'].strftime("%Y-%m-%d %H:%M:%S")
            id += 1
    table_details['arn'] = table_details['Table']['TableArn']
    table_details['table_name'] = table_name

    # Scan for 5 items, merge them into single dict to have more attributes in response
    scan_result = dynamodb_client.scan(TableName=table_name, Limit=5, Select='ALL_ATTRIBUTES')
    if 'Items' in scan_result and len(scan_result['Items']) > 0:
        result = {}
    for item in scan_result['Items']:
        result.update(item)
    table_details['item'] = result
    return table_details
