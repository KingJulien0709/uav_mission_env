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
    """
    grammar_lines = []

    # 1. Basic Primitives
    grammar_lines.append(r'space ::= | " " | "\n" [ \t]{0,5}')
    grammar_lines.append(r'char ::= [^"\\\x7F\x00-\x1F] | [\\] (["\\bfnrt] | "u" [0-9a-fA-F]{4})')
    grammar_lines.append(r'string ::= "\"" char* "\"" space')
    grammar_lines.append(r'boolean ::= ("true" | "false") space')
    grammar_lines.append(r'null ::= "null" space')
    grammar_lines.append(r'number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? space')

    # 2. Recursive JSON (simplified)
    grammar_lines.append(r'gen-value ::= string | number | gen-object | gen-array | boolean | null')
    grammar_lines.append(r'gen-object ::= "{" space (string ":" space gen-value ("," space string ":" space gen-value)*)? "}" space')
    grammar_lines.append(r'gen-array ::= "[" space (gen-value ("," space gen-value)*)? "]" space')

    # 3. Thinking Rule
    # Matches content until "</" appears
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

        if f_type == "string":
            # Specific length string
            grammar_lines.append(f'{val_rule_name} ::= "\\"" char{{0,{f_len}}} "\\"" space')
        elif f_type == "object":
            if f_name == "tool_call":
                if tool_name_list:
                    tool_opts = " | ".join([f'"\\"{t}\\\""' for t in tool_name_list])
                    grammar_lines.append(f'tool-name ::= ({tool_opts}) space')
                else:
                    grammar_lines.append(f'tool-name ::= string')

                # tool_call object structure
                grammar_lines.append(f'{val_rule_name} ::= "{{" space "\\"name\\"" space ":" space tool-name "," space "\\"parameters\\"" space ":" space gen-object "}}" space')
            else:
                grammar_lines.append(f'{val_rule_name} ::= gen-object')
        else:
            # Fallback
            grammar_lines.append(f'{val_rule_name} ::= gen-value')

        # KV Rule
        kv_rule = f'"\\"{f_name}\\"" space ":" space {val_rule_name}'
        field_kv_rules.append(kv_rule)

    # 5. Root Object
    fields_joined = ' "," space '.join(field_kv_rules)
    grammar_lines.append(f'json-output ::= "{{" space {fields_joined} "}}" space')

    grammar_lines.append(r'root ::= thinking? json-output')

    return "\n".join(grammar_lines)
