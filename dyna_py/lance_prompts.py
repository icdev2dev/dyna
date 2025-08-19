import lancedb
import pyarrow as pa
import pandas as pd
from lancedb.query import Query

METADATA_URI = "data/metadata"
METADATA_DB = lancedb.connect(METADATA_URI)

VECTOR_DIM = 384  # Adjust as needed

schema_registry_schema = pa.schema([
    pa.field("schema_name", pa.string(), nullable=False),
    pa.field("is_top_level", pa.bool_(), nullable=False),
    pa.field("description", pa.string()),
    pa.field("display_name", pa.string()),
    pa.field("icon", pa.string(), nullable=True),
    pa.field("vector", pa.list_(pa.float32(), VECTOR_DIM), nullable=True),
])

attribute_metadata_schema = pa.schema([
    pa.field("schema_name", pa.string(), nullable=False),
    pa.field("attribute_name", pa.string(), nullable=False),
    pa.field("data_type", pa.string(), nullable=False),
    pa.field("label", pa.string()),
    pa.field("required", pa.bool_(), nullable=False),
    pa.field("ui_control", pa.string()),
    pa.field("description", pa.string()),
    pa.field("parent_schema", pa.string()),
    pa.field("related_schema", pa.string()),
    pa.field("relation_type", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), VECTOR_DIM), nullable=True),
])

def create_metadata_schema():
    # Define the 'prompt' struct with multiple fields

    _ = METADATA_DB.create_table("schema_registry_schema", schema=schema_registry_schema)
    _ = METADATA_DB.create_table("attribute_metadata_schema", schema=attribute_metadata_schema)


def drop_metadata_registry():
    METADATA_DB.drop_all_tables()


def schema_count():
    print(METADATA_DB.open_table("schema_registry_schema").count_rows())

from metadata_registry import get_all_schema_names


def isSchemaInSchemaRegistry(data) -> bool:
    result = False
    schema_names = get_all_schema_names({"schema_registry":[data]})

    tbl = METADATA_DB.open_table("schema_registry_schema")
    
    for schema_name in schema_names:
        if len(tbl.search().where(f"schema_name =='{schema_name}'").to_list()) > 0:
            result = True
            break

    return result


def isSchemaRequestINVALID(data) -> bool:
    return  isSchemaInSchemaRegistry(data)



def insert_record_into_schema_registry(record) :

    if not isSchemaRequestINVALID(record):
        tbl = METADATA_DB.open_table("schema_registry_schema")
        tbl.add(data=[record], mode="append")
    else: 
        print("insert request is invalid")


def are_records_in_schema_registry(records): 
    result = False
    if isinstance(records, list):
        for record in records:
            if isSchemaInSchemaRegistry(data=record):
                result = True
                break

    return result

def insert_records_into_schema_registry(records) :
    if not are_records_in_schema_registry(records=records):
        for record in records: 
            insert_record_into_schema_registry(record=record)





def get_schema(): 
    prompt_type = pa.struct([
        ("id", pa.int32()),
        ("text", pa.string()),
        ("metadata", pa.struct([
            ("created_by", pa.string()),
            ("created_at", pa.timestamp('ms')),
        ]))
    ])

    # Define the 'project' struct that contains a list of prompts
    project_type = pa.struct([
        ("project_id", pa.int32()),
        ("name", pa.string()),
        ("prompts", pa.list_(prompt_type)),  # list of prompt structs
    ])

    # Create the top-level schema or use project_type as needed
    schema = pa.schema([
        ("project", project_type)
    ])

    return schema


def read_records_from_table():
    tbl = db.open_table("cool")
    print(tbl.count_rows())
    q= tbl.take_offsets([0])
    print(q.to_pandas().project.iloc[0])








def write_data_to_table():
    tbl = db.open_table("cool")
    project_array = pa.array([
        {
            "project_id": 10,
            "name": "Project A",
            "prompts": [
                {"id": 1, "text": "Prompt A1", "metadata": {"created_by": "Alice", "created_at": pd.Timestamp("2023-01-01")}},
                {"id": 2, "text": "Prompt A2", "metadata": {"created_by": "Bob", "created_at": pd.Timestamp("2023-01-02")}},
            ],
        },
        {
            "project_id": 20,
            "name": "Project B",
            "prompts": [
                {"id": 3, "text": "Prompt B1", "metadata": {"created_by": "Carlos", "created_at": pd.Timestamp("2023-02-01")}},
            ],
        }
        ]
        )
    table = pa.Table.from_arrays([project_array], schema=get_schema())
    tbl.add(data=table, mode="append")


def insert_data() :

    schema_count()
    records =    [{
      "schema_name": "Project",
      "is_top_level": True,
      "description": "Schema representing a project entity.",
      "display_name": "Project",
       "icon": None,
      "vector": [0]*384
    }]

    insert_records_into_schema_registry(records=records)

    schema_count()
    

if __name__ == "__main__":
#    create_metadata_schema()
#    drop_metadata_registry()

    insert_data()
