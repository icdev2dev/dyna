
def get_all_schema_names(data):
    """
    Recursively collects all unique schema names from a given schema/attribute registry JSON.
    Returns a set of schema names.
    """
    schema_names = set()
    if isinstance(data, dict):
        # Check if this is a schema_registry or attribute_metadata part
        if "schema_registry" in data:
            for schema in data["schema_registry"]:
                schema_names.add(schema.get("schema_name"))
        if "attribute_metadata" in data:
            for attr in data["attribute_metadata"]:
                # The attribute itself belongs to a schema:
                schema_names.add(attr.get("schema_name"))
                # If the attribute references a related schema (e.g. for relations), include that:
                if attr.get("related_schema"):
                    schema_names.add(attr.get("related_schema"))
                # If parent_schema is present
                if attr.get("parent_schema"):
                    schema_names.add(attr.get("parent_schema"))
        # Recursively traverse other keys (if any, for deeper nested JSONs)
        for v in data.values():
            schema_names.update(get_all_schema_names(v))
    elif isinstance(data, list):
        for item in data:
            schema_names.update(get_all_schema_names(item))
    # Otherwise, return empty set for primitives.
    return schema_names
