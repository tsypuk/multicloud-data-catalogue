import boto3
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from multicloud_diagrams import MultiCloudDiagrams

app = typer.Typer()
dynamodb_client = boto3.client('dynamodb')
console = Console()


@app.command("get")
def table_get(table_name: str):
    print(f"Getting table: {table_name}")
    table_details = crawl_aws(table_name)

    console.rule("SSE")
    # SSE
    if 'SSEDescription' in table_details['Table']:
        sse_table = Table(show_header=True, header_style="bold magenta")
        column_width = 5
        sse_table.add_column("Key", style="dim", width=column_width)
        sse_table.add_column("Value")
        for (key, value) in table_details['Table']['SSEDescription'].items():
            sse_table.add_row(f'{key}', f'{value}')
            if len(key) > column_width:
                column_width = len(key)

        sse_table.columns[0].width = column_width
        console.print(sse_table)
    else:
        print('NO SSE')


@app.command("drawio")
def table_drawio(table_name: str):
    print(f"Drawio table: {table_name}")
    render_mcd(crawl_aws(table_name))


def print_table_info(table_details):
    console.rule("Generic Details")

    # Table Data
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


def print_table_schema(table_details):
    # Key Schema
    console.rule("Key Schema")
    schema_table = Table(show_header=True, header_style="bold magenta")
    column_width = 5
    schema_table.add_column("Key", style="dim", width=column_width)
    schema_table.add_column("Value")
    for index, value in enumerate(table_details['Table']['KeySchema']):
        schema_table.add_row(f'{index}', f'{value}')
        # if len(index) > column_width:
        #     column_width = len(index)
    console.print(schema_table)


def print_lsi(table_details):
    if 'LocalSecondaryIndexes' in table_details['Table']:
        lsis_table = Table(show_header=True, header_style="bold magenta")
        column_width = 5
        lsis_table.add_column("LSI Name", style="dim", width=column_width)
        for attribute in table_details['Table']['LocalSecondaryIndexes']:
            lsis_table.add_row(f"IndexName: {attribute['IndexName']}")
        console.print(lsis_table)

        for attribute in table_details['Table']['LocalSecondaryIndexes']:
            attributes = []
            index_name = attribute['IndexName']
            attributes.append('IndexName: ' + index_name)
            attributes.append('IndexSizeBytes: ' + str(attribute['IndexSizeBytes']))
            attributes.append('ItemCount: ' + str(attribute['ItemCount']))
            attributes.append('ProjectionType: ' + attribute['Projection']['ProjectionType'])

            rows_schema = '{ '
            for schema_attribute in attribute['KeySchema']:
                rows_schema += (schema_attribute['AttributeName'] + ': ' + schema_attribute['KeyType'] + ',')
            rows_schema = rows_schema.rstrip(rows_schema[-1]) + '}'
            attributes.append('Schema: ' + rows_schema)

            lsi_table = Table(show_header=True, header_style="bold magenta")
            column_width = 5
            lsi_table.add_column("Key", style="dim", width=column_width)
            lsi_table.add_column("Value")

            console.rule(f"LSI:{index_name}")

            for idx in attributes:
                lsi_table.add_row(idx)
            if len(idx) > column_width:
                column_width = len(idx)

            lsi_table.columns[0].width = column_width
            console.print(lsi_table)


def print_gsi(table_details):
    # GSI
    if 'GlobalSecondaryIndexes' in table_details['Table']:
        console.rule("GSIs:")
        gsis_table = Table(show_header=True, header_style="bold magenta")
        column_width = 15
        gsis_table.add_column("GSI Name", style="dim", width=column_width)

        for attribute in table_details['Table']['GlobalSecondaryIndexes']:
            gsis_table.add_row(f"IndexName: {attribute['IndexName']}")
            if len(f"IndexName: {attribute['IndexName']}") > column_width:
                column_width = len(f"IndexName: {attribute['IndexName']}")
        console.print(gsis_table)

        for attribute in table_details['Table']['GlobalSecondaryIndexes']:
            rows = []
            index_name = attribute['IndexName']
            rows.append('IndexName: ' + index_name)
            rows.append('IndexSizeBytes: ' + str(attribute['IndexSizeBytes']))
            rows.append('IndexStatus: ' + attribute['IndexStatus'])
            rows.append('ItemCount: ' + str(attribute['ItemCount']))
            rows.append('RCU: ' + str(attribute['ProvisionedThroughput']['ReadCapacityUnits']))
            rows.append('WCU: ' + str(attribute['ProvisionedThroughput']['WriteCapacityUnits']))
            rows.append('ProjectionType: ' + attribute['Projection']['ProjectionType'])

            rows_schema = '{ '
            for schema_attribute in attribute['KeySchema']:
                rows_schema += (schema_attribute['AttributeName'] + ': ' + schema_attribute['KeyType'] + ',')
            rows_schema = rows_schema.rstrip(rows_schema[-1]) + '}'
            rows.append('Schema: ' + rows_schema)

            gsi_table = Table(show_header=True, header_style="bold magenta")
            column_width = 10
            gsi_table.add_column("Key", style="dim", width=column_width)

            console.rule(f"GSI:-{index_name}")

            for idx_name in rows:
                gsi_table.add_row(f'{idx_name}')
                if len(idx_name) > column_width:
                    column_width = len(idx_name)

            gsi_table.columns[0].width = column_width
            console.print(gsi_table)


def print_item(table_details):
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


@app.command("list")
def list_tables():
    print("Listing tables...")
    table_names = dynamodb_client.list_tables()['TableNames']

    table_select = True
    while table_select:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("Table name")
        for index, table_name in enumerate(table_names):
            table.add_row(
                f"{index}", table_name
            )

        # tables = list(table_names.values())

        console.print(table)
        table_id = Prompt.ask("Enter Table ID", default=0)
        print(table_id)
        table_name = table_names[int(table_id)]
        print(table_name)

        # crawl Table
        print(f'Crawling: {table_name}')
        table_details = crawl_aws(table_name)

        print_table_info(table_details)

        table_operations = True
        while table_operations:
            choices = ['schema', 'item', 'drawio', 'back2list']

            if 'LocalSecondaryIndexes' in table_details['Table']:
                choices.append('lsi')
            if 'GlobalSecondaryIndexes' in table_details['Table']:
                choices.append('gsi')

            action = Prompt.ask(f"Choose operation for table: {table_name}",
                                choices=choices,
                                default='schema')
            match action:
                case 'schema':
                    print_table_schema(table_details)
                case 'lsi':
                    print_lsi(table_details)
                case 'gsi':
                    print_gsi(table_details)
                case 'item':
                    print_item(table_details)
                case 'drawio':
                    render_mcd(table_details=table_details)
                case 'back2list':
                    table_operations = False


def render_mcd(table_details: dict):
    table_name = table_details['table_name']
    mcd = MultiCloudDiagrams()
    data_file = f'output.{table_name}.dynamo.drawio'
    mcd.read_coords_from_file(data_file)

    dynamo_table = table_details['Table']
    table_arn = dynamo_table['TableArn']
    table_name = dynamo_table['TableName']
    metadata = {
        'DeletionProtectionEnabled': dynamo_table['DeletionProtectionEnabled'],
        'ItemCount': dynamo_table['ItemCount'],
        'TableSizeBytes': dynamo_table['TableSizeBytes'],
        'TableStatus': dynamo_table['TableStatus'],
        'CreationDateTime': dynamo_table['CreationDateTime']
    }

    mcd.add_vertex(node_id=table_arn, node_name=table_name, node_type='dynamo', metadata=metadata)

    # DynamoDB Stream
    if 'LatestStreamArn' in dynamo_table:
        stream_arn = dynamo_table['LatestStreamArn']
        stream_metadata = {
            "LatestStreamLabel": dynamo_table['LatestStreamLabel'],
            "StreamViewType": dynamo_table['StreamSpecification']['StreamViewType']
        }
        mcd.add_vertex(node_id=stream_arn, node_name=dynamo_table['LatestStreamLabel'], node_type='dynamo_stream', metadata=stream_metadata)
        mcd.add_link(f'dynamo:{table_arn}', f'dynamo_stream:{stream_arn}', action=['DynamoDBStream'])

    # KeySchema
    rows_keys = []
    for attribute in dynamo_table['KeySchema']:
        rows_keys.append(attribute['AttributeName'] + ' : ' + attribute['KeyType'])
    mcd.add_list(table_name=f'Schema:{table_name}', rows=rows_keys)
    mcd.add_link(f'dynamo:{table_arn}', f'Schema:{table_name}:list', action=['Key Schema'])

    # Attributes
    rows = []
    for attribute in dynamo_table['AttributeDefinitions']:
        rows.append(attribute['AttributeName'] + ' : ' + attribute['AttributeType'])
    mcd.add_list(table_name=f'Attributes:{table_name}', rows=rows)
    mcd.add_link(src_node_id=f'dynamo:{table_arn}', dst_node_id=f'Attributes:{table_name}:list', action=['AttributeDefinitions'])

    # Local Secondary Indexes
    if 'LocalSecondaryIndexes' in dynamo_table:
        attributes = []
        for attribute in dynamo_table['LocalSecondaryIndexes']:
            attributes.append('IndexName: ' + attribute['IndexName'])
        mcd.add_list(table_name=f'LSIs:{table_name}', rows=attributes)
        mcd.add_link(f'dynamo:{table_arn}', f'LSIs:{table_name}:list', action=['index: LSI'])

        for attribute in dynamo_table['LocalSecondaryIndexes']:
            attributes = {}
            index_name = attribute['IndexName']
            attributes['IndexName'] = index_name
            attributes['IndexSizeBytes'] = str(attribute['IndexSizeBytes'])
            attributes['ItemCount'] = str(attribute['ItemCount'])
            attributes['ProjectionType'] = attribute['Projection']['ProjectionType']

            rows_schema = '{ '
            for schema_attribute in attribute['KeySchema']:
                rows_schema += (schema_attribute['AttributeName'] + ': ' + schema_attribute['KeyType'] + ',')
            rows_schema = rows_schema.rstrip(rows_schema[-1]) + '}'
            attributes['Schema'] = rows_schema

            mcd.add_map(table_name=f'LSI:{table_name}-{index_name}', key_value_pairs=attributes)
            mcd.add_link(f'LSIs:{table_name}:list', f'LSI:{table_name}-{index_name}:list', action=[f'LSI : {index_name}'])

    # Global Secondary Indexes
    if 'GlobalSecondaryIndexes' in dynamo_table:
        rows = []
        for attribute in dynamo_table['GlobalSecondaryIndexes']:
            rows.append('IndexName: ' + attribute['IndexName'])
        mcd.add_list(table_name=f'GSIs:{table_name}', rows=rows)
        mcd.add_link(f'dynamo:{table_arn}', f'GSIs:{table_name}:list', action=['index: GSI'])

        for attribute in dynamo_table['GlobalSecondaryIndexes']:
            index_details = {}
            index_name = attribute['IndexName']
            index_details['IndexName'] = index_name
            index_details['IndexSizeBytes'] = str(attribute['IndexSizeBytes'])
            index_details['IndexStatus'] = attribute['IndexStatus']
            index_details['ItemCount'] = str(attribute['ItemCount'])
            index_details['RCU'] = str(attribute['ProvisionedThroughput']['ReadCapacityUnits'])
            index_details['WCU'] = str(attribute['ProvisionedThroughput']['WriteCapacityUnits'])
            index_details['ProjectionType'] = attribute['Projection']['ProjectionType']

            rows_schema = '{ '
            for schema_attribute in attribute['KeySchema']:
                rows_schema += (schema_attribute['AttributeName'] + ': ' + schema_attribute['KeyType'] + ',')
            rows_schema = rows_schema.rstrip(rows_schema[-1]) + '}'
            index_details['Schema'] = rows_schema

            mcd.add_map(table_name=f'GSI:{table_name}-{index_name}', key_value_pairs=index_details)
            mcd.add_link(f'GSIs:{table_name}:list', f'GSI:{table_name}-{index_name}:list', action=[f'GSI : {index_name}'])

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
