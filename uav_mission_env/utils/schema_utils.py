from typing import List, Dict, Any

def generate_schema_from_keys(output_keys: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a simplified JSON schema from output keys."""
    properties = {}
    required = []
    
    for item in output_keys:
        name = list(item.keys())[0]
        details = item[name]
        type_str = details.get('type', 'string')
        
        # Map simple types if needed, or pass through
        # Assuming type_str is already a valid JSON schema type (string, object, etc.)
        prop_schema = {"type": type_str}
        
        if 'description' in details:
            prop_schema['description'] = details['description']
            
        if 'max_length' in details:
            prop_schema['maxLength'] = details['max_length']
            
        properties[name] = prop_schema
        required.append(name)
    
    schema = {
        "type": "object",
        "properties": properties,
        "required": required
    }
    return schema
