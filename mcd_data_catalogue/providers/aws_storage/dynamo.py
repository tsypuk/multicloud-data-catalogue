import boto3
import typer
from multicloud_diagrams import MultiCloudDiagrams

app = typer.Typer()
dynamodb_client = boto3.client('dynamodb')


@app.command("get")
def table_get(table_name: str):
    print(f"Getting table: {table_name}")
    render_mcd({})


@app.command("list")
def list_tables(item: str):
    print(f"Listing tables: {item}")
    response = dynamodb_client.list_tables()


@app.command("sell")
def items_sell(item: str):
    print(f"Selling item: {item}")


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
    del table_details['Table']['CreationDateTime']
    del table_details['ResponseMetadata']
    if 'BillingModeSummary' in table_details['Table']:
        del table_details['Table']['BillingModeSummary']['LastUpdateToPayPerRequestDateTime']

    if 'ProvisionedThroughput' in table_details['Table']:
        if 'LastIncreaseDateTime' in table_details['Table']['ProvisionedThroughput']:
            del table_details['Table']['ProvisionedThroughput']['LastIncreaseDateTime']
        if 'LastDecreaseDateTime' in table_details['Table']['ProvisionedThroughput']:
            del table_details['Table']['ProvisionedThroughput']['LastDecreaseDateTime']

    if 'GlobalSecondaryIndexes' in table_details['Table']:
        id = 0
        for index in table_details['Table']['GlobalSecondaryIndexes']:
            if 'LastIncreaseDateTime' in index['ProvisionedThroughput']:
                del table_details['Table']['GlobalSecondaryIndexes'][id]['ProvisionedThroughput'][
                    'LastIncreaseDateTime']
            if 'LastDecreaseDateTime' in index['ProvisionedThroughput']:
                del table_details['Table']['GlobalSecondaryIndexes'][id]['ProvisionedThroughput'][
                    'LastDecreaseDateTime']
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
