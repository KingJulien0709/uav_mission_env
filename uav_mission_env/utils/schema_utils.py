from typing import List, Dict, Any
import numpy as np

def create_json_schema_from_keys(output_keys: List[Dict[str, Any]]) -> Dict[str, Any]:
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


def create_gbnf_grammar(output_keys: List[Dict[str, Any]], tool_name_list: List[str]) -> str:
    """
    Transforms a schema definition into a strict vLLM/Lark grammar string.
    """
    
    # 1. Base Parts of the Grammar
    # ?start: Optional thinking -> strict JSON object
    # thinking: <think> ... </think> (Max 8192 chars, lazy match)
    grammar_parts = [
        r'root: thinking? json_output',
        r'thinking: "<think>" /[\s\S]{0,__THINK_LIMIT__}?/ "</think>" "\n"?',
    ]

    # 2. Build the JSON Object Sequence
    # We need to construct the line: json_output: "{" rule_1 "," rule_2 "," rule_3 "}"
    field_rule_names = []
    field_definitions = []
    primitive_definitions = set()  # To avoid duplicate rules for same max_length

    for field in output_keys:
        # Normalize input (handle cases where key might be the dict key or 'name' field)
        # Assuming input format: {'justification': {'type': 'string', ...}} or {'name': 'justification', ...}
        if len(field) == 1 and isinstance(list(field.values())[0], dict):
            f_name = list(field.keys())[0]
            f_props = list(field.values())[0]
        else:
            f_name = field.get("name")
            f_props = field
            
        f_type = f_props.get("type", "string")
        f_len = f_props.get("max_length", 250) # Default length if missing

        rule_name = f"field_{f_name}"
        field_rule_names.append(rule_name)

        # --- CASE A: STRING FIELDS (Strict Limits, No Newlines) ---
        if f_type == "string":
            # Rule: "key_name": primitive_rule
            field_definitions.append(f'{rule_name}: "\\" {f_name} \\":" string_{f_len}')
            
            # Primitive: string_300: "\"" /[^"\n]{0,300}/ "\""
            primitive_code = f'string_{f_len}: "\\"" /[^"\\n]{{0,{f_len}}}/ "\\""'
            primitive_definitions.add(primitive_code)

        # --- CASE B: OBJECT FIELDS (Tool Call) ---
        elif f_type == "object":
            # For 'tool_call', we usually want a specific nested structure
            if f_name == "tool_call":
                # Hardcoded structure for tool_call as discussed previously
                field_definitions.append(f'{rule_name}: "\\" {f_name} \\":" tool_obj')
                
                if tool_name_list:
                    # Create a rule that matches only the allowed tool names
                    # e.g. tool_name: "\"tool_a\"" | "\"tool_b\""
                    quoted_tools = [f'"\\"{t}\\""' for t in tool_name_list]
                    tool_name_rule = " | ".join(quoted_tools)
                    primitive_definitions.add(f'tool_name: {tool_name_rule}')
                    primitive_definitions.add(r'tool_obj: "{" "\"name\":" tool_name "," "\"parameters\":" param_obj "}"')
                else:
                    # Fallback to any string if no list provided
                    primitive_definitions.add(r'tool_obj: "{" "\"name\":" string_any "," "\"parameters\":" param_obj "}"')
                    primitive_definitions.add(r'string_any: "\"" /[^"]*/ "\""')

                primitive_definitions.add(r'param_obj: "{" /[\s\S]*?/ "}"') # Lazy match for params
            else:
                # Generic fallback for other objects (just allow {} with anything inside)
                field_definitions.append(f'{rule_name}: "\\" {f_name} \\": generic_obj')
                primitive_definitions.add(r'generic_obj: "{" /[\s\S]*?/ "}"')

    # 3. Assemble the JSON Structure Rule
    # Joins fields with a comma "," but NO whitespace to prevent gaps
    json_structure = 'json_output: "{" ' + ' "," '.join(field_rule_names) + ' "}"'
    grammar_parts.append(json_structure)

    # 4. Add Definitions
    grammar_parts.extend(field_definitions)
    grammar_parts.extend(sorted(list(primitive_definitions)))

    # 5. Return the formatted string
    return "\n".join(grammar_parts)
