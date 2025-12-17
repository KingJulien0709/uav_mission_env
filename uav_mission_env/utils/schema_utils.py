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

    # 1. Spacing Primitives (The "Tuning" Part)
    # 'ws': Structural whitespace (newlines, tabs, spaces). Used between fields.
    grammar_lines.append(r'ws ::= [ \t\n]*')
    # 'sp': Inline space (strictly space/tab). Used for "key": value alignment.
    grammar_lines.append(r'sp ::= [ \t]*') 

    # 2. Basic Types
    grammar_lines.append(r'char ::= [^"\\\x7F\x00-\x1F] | [\\] (["\\bfnrt] | "u" [0-9a-fA-F]{4})')
    grammar_lines.append(r'string ::= "\"" char* "\""')
    grammar_lines.append(r'boolean ::= ("true" | "false")')
    grammar_lines.append(r'null ::= "null"')
    grammar_lines.append(r'number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)?')

    # 3. Recursive Structure (Using 'ws' for structure, 'sp' for inline)
    grammar_lines.append(r'gen-value ::= string | number | gen-object | gen-array | boolean | null')
    
    # Logic: { ws "key" sp : sp value ( , ws "key" sp : sp value )* ws }
    grammar_lines.append(r'gen-object ::= "{" ws (string sp ":" sp gen-value ("," ws string sp ":" sp gen-value)*)? ws "}"')
    
    # Logic: [ ws value ( , ws value )* ws ]
    grammar_lines.append(r'gen-array ::= "[" ws (gen-value ("," ws gen-value)*)? ws "]"')

    # 4. Thinking Rule (Unchanged)
    grammar_lines.append(r'thinking-char ::= [^<] | ( "<" [^/] )')
    grammar_lines.append(r'thinking-content ::= thinking-char {0,__THINK_LIMIT__}')
    grammar_lines.append(r'thinking ::= "<think>" thinking-content "</think>" "\n"')

    # 5. Field Definitions
    field_kv_rules = []

    for field in output_keys:
        # (Same field parsing logic as before)
        if len(field) == 1 and isinstance(list(field.values())[0], dict):
            f_name = list(field.keys())[0]
            f_props = list(field.values())[0]
        else:
            f_name = field.get("name")
            f_props = field

        f_type = f_props.get("type", "string")
        f_len = f_props.get("max_length", 250)
        
        val_rule_name = f"val-{f_name}"

        # Define specific rules per type
        if f_type == "string":
            grammar_lines.append(f'{val_rule_name} ::= "\\"" char{{0,{f_len}}} "\\""')
        elif f_type == "boolean":
            grammar_lines.append(f'{val_rule_name} ::= boolean')
        elif f_type in ["number", "integer"]:
            grammar_lines.append(f'{val_rule_name} ::= number')
        elif f_type == "object":
            if f_name == "tool_call" and tool_name_list:
                tool_opts = " | ".join([f'"\\"{t}\\\""' for t in tool_name_list])
                grammar_lines.append(f'tool-name ::= ({tool_opts})')
                # Strict spacing for tool calls: { ws "name" sp : sp ... }
                grammar_lines.append(f'{val_rule_name} ::= "{{" ws "\\"name\\"" sp ":" sp tool-name "," ws "\\"parameters\\"" sp ":" sp gen-object ws "}}"')
            else:
                grammar_lines.append(f'{val_rule_name} ::= gen-object')
        else:
            grammar_lines.append(f'{val_rule_name} ::= gen-value')

        # Key-Value separator rule: "key" sp : sp value
        kv_rule = f'"\\"{f_name}\\"" sp ":" sp {val_rule_name}'
        field_kv_rules.append(kv_rule)

    # 6. Root Object Construction
    # Separator: Comma + Structural Whitespace (allows newlines between fields)
    fields_joined = ' "," ws '.join(field_kv_rules)
    
    # Root: thinking? ws { ws fields ws } ws
    grammar_lines.append(f'json-output ::= "{{" ws {fields_joined} ws "}}" ws')
    grammar_lines.append(r'root ::= thinking? ws json-output')

    return "\n".join(grammar_lines)