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
    Transforms a schema definition into a GBNF grammar string.
    Refactored to prevent infinite whitespace generation by handling spacing in structures.
    """
    grammar_lines = []

    # 1. Basic Primitives (Removed trailing 'space' from these)
    grammar_lines.append(r'space ::= [ \t\n]{0,4}}')
    grammar_lines.append(r'char ::= [^"\\\x7F\x00-\x1F] | [\\] (["\\bfnrt] | "u" [0-9a-fA-F]{4})')
    grammar_lines.append(r'string ::= "\"" char* "\""')  # Removed trailing space
    grammar_lines.append(r'boolean ::= ("true" | "false")') # Removed trailing space
    grammar_lines.append(r'null ::= "null"') # Removed trailing space
    grammar_lines.append(r'number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)?') # Removed trailing space

    # 2. Recursive JSON (Added 'space' to the structure)
    grammar_lines.append(r'gen-value ::= string | number | gen-object | gen-array | boolean | null')
    
    # Logic: "{" space ( key space ":" space value space ("," space key space ":" space value space)* )? "}"
    grammar_lines.append(r'gen-object ::= "{" space (string space ":" space gen-value space ("," space string space ":" space gen-value space)*)? "}"')
    
    # Logic: "[" space ( value space ("," space value space)* )? "]"
    grammar_lines.append(r'gen-array ::= "[" space (gen-value space ("," space gen-value space)*)? "]"')

    # 3. Thinking Rule (Unchanged)
    grammar_lines.append(r'thinking-char ::= [^<] | ( "<" [^/] )')
    grammar_lines.append(r'thinking-content ::= thinking-char {0,__THINK_LIMIT__}')
    grammar_lines.append(r'thinking ::= "<think>" thinking-content "</think>" space')

    # 4. Field Definitions
    field_kv_rules = []

    for field in output_keys:
        if len(field) == 1 and isinstance(list(field.values())[0], dict):
            f_name = list(field.keys())[0]
            f_props = list(field.values())[0]
        else:
            f_name = field.get("name")
            f_props = field

        f_type = f_props.get("type", "string")
        f_len = f_props.get("max_length", 250)

        val_rule_name = f"val-{f_name}"

        # Note: We remove 'space' from the end of all these specific value rules
        if f_type == "string":
            grammar_lines.append(f'{val_rule_name} ::= "\\"" char{{0,{f_len}}} "\\""')
        elif f_type == "object":
            if f_name == "tool_call":
                if tool_name_list:
                    tool_opts = " | ".join([f'"\\"{t}\\\""' for t in tool_name_list])
                    grammar_lines.append(f'tool-name ::= ({tool_opts})') # No trailing space
                else:
                    grammar_lines.append(f'tool-name ::= string')

                # tool_call object structure with explicit spacing
                grammar_lines.append(f'{val_rule_name} ::= "{{" space "\\"name\\"" space ":" space tool-name space "," space "\\"parameters\\"" space ":" space gen-object space "}}"')
            else:
                grammar_lines.append(f'{val_rule_name} ::= gen-object')
        else:
            grammar_lines.append(f'{val_rule_name} ::= gen-value')

        # KV Rule: "key" space ":" space value
        # We do NOT put space at the end here, we handle it in the joiner below
        kv_rule = f'"\\"{f_name}\\"" space ":" space {val_rule_name}'
        field_kv_rules.append(kv_rule)

    # 5. Root Object
    # Joiner must provide the separator: space "," space
    fields_joined = '","space'.join(field_kv_rules)
    
    # Root structure: "{" space FIELDS space "}"
    grammar_lines.append(f'json-output ::= "{{" space {fields_joined} space "}}" space')

    grammar_lines.append(r'root ::= thinking? json-output')

    return "\n".join(grammar_lines)