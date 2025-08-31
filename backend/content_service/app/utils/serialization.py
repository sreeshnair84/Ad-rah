"""
Utility functions for data serialization, particularly for MongoDB ObjectId handling
"""
from typing import Any, Dict, List, Union

def convert_objectid_to_str(data: Any) -> Any:
    """
    Recursively convert ObjectId instances to strings in a data structure
    
    This function handles:
    - Single ObjectId instances
    - Lists containing ObjectIds
    - Dictionaries with ObjectId values
    - Nested structures
    - MongoDB documents with _id fields
    
    Args:
        data: The data structure to process
        
    Returns:
        The same data structure with ObjectIds converted to strings
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Special handling for _id fields
            if key == "_id" and value is not None:
                try:
                    from bson import ObjectId
                    if isinstance(value, ObjectId):
                        # Convert _id to both id and _id for compatibility
                        result["id"] = str(value)
                        result["_id"] = str(value)
                    else:
                        result[key] = convert_objectid_to_str(value)
                except ImportError:
                    result[key] = convert_objectid_to_str(value)
            else:
                result[key] = convert_objectid_to_str(value)
        return result
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    else:
        # Handle individual ObjectId instances
        try:
            from bson import ObjectId
            if isinstance(data, ObjectId):
                return str(data)
        except ImportError:
            pass
        return data

def ensure_string_id(data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """
    Ensure that documents have string IDs for API responses
    
    Args:
        data: Single document or list of documents
        
    Returns:
        Documents with string IDs
    """
    if isinstance(data, list):
        return [ensure_string_id(item) for item in data]
    elif isinstance(data, dict):
        # Convert _id to id if present
        if "_id" in data and "id" not in data:
            data["id"] = str(data["_id"])
        elif "_id" in data:
            data["id"] = str(data["_id"])
            
        return convert_objectid_to_str(data)
    else:
        return data

def safe_json_response(data: Any) -> Any:
    """
    Prepare data for safe JSON serialization by handling ObjectIds and other non-serializable objects
    
    Args:
        data: The data to serialize
        
    Returns:
        JSON-serializable data
    """
    return convert_objectid_to_str(data)