import unittest
from metadata_registry import get_all_schema_names

json_rep = {
  "schema_registry": [
    {
      "schema_name": "Project",
      "is_top_level": True,
      "description": "Schema representing a project entity.",
      "display_name": "Project",
      "icon": "project_icon.png",
      "vector": None
    },
    {
      "schema_name": "Prompt",
      "is_top_level": False,
      "description": "Prompt details used within a project.",
      "display_name": "Prompt",
      "icon": "prompt_icon.png",
      "vector": None
    }
  ],
  "attribute_metadata": [
    {
      "schema_name": "Project",
      "attribute_name": "project_id",
      "data_type": "GUID",
      "label": "Project Id",
      "required": True,
      "ui_control": "text",
      "description": "Unique identifier for the project.",
      "parent_schema": None,
      "related_schema": None,
      "relation_type": None,
      "vector": None
    },
    {
      "schema_name": "Project",
      "attribute_name": "project_name",
      "data_type": "string",
      "label": "Project Name",
      "required": True,
      "ui_control": "text",
      "description": "Name of the project.",
      "parent_schema": None,
      "related_schema": None,
      "relation_type": None,
      "vector": None
    },
    {
      "schema_name": "Project",
      "attribute_name": "prompts",
      "data_type": "relation",
      "label": "Prompts",
      "required": False,
      "ui_control": "table",
      "description": "List of prompts associated with the project.",
      "parent_schema": None,
      "related_schema": "Prompt",
      "relation_type": "one_to_many",
      "vector": None
    },
    {
      "schema_name": "Prompt",
      "attribute_name": "name",
      "data_type": "string",
      "label": "Prompt Name",
      "required": True,
      "ui_control": "text",
      "description": "The name of the prompt.",
      "parent_schema": "Project",
      "related_schema": None,
      "relation_type": None,
      "vector": None
    },
    {
      "schema_name": "Prompt",
      "attribute_name": "description",
      "data_type": "string",
      "label": "Prompt Description",
      "required": False,
      "ui_control": "textarea",
      "description": "Details about what the prompt is for.",
      "parent_schema": "Project",
      "related_schema": None,
      "relation_type": None,
      "vector": None
    }
  ]
}


class MetadataTestCases(unittest.TestCase) :
    def test_schema_names(self): 
        schema_names =  get_all_schema_names(json_rep)
        print(schema_names)
       
unittest.main()
