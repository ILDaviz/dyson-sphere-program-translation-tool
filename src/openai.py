""" 
OpenAI Integration Module 
Handles interaction with the LLM using structured output for strict type safety.
"""

import os
import json
import openai
from rich.console import Console

console = Console()

def load_glossary():
    """Load translation rules from glossary.txt if present."""
    
    glossary_path = 'glossary.txt'
    
    if os.path.exists(glossary_path):
        with open(glossary_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def translate_batch(texts_map, lang_to, model="gpt-5-nano"):
    """
    Translate a batch of texts using OpenAI Structured Outputs (Strict Mode).
    
    Args:
        texts_map: Dictionary where keys are IDs and values are dicts with "text", "context", "len".
        lang_to: Target language code.
        model: OpenAI model identifier.
        
    Returns:
        dict: Mapping of {id: translated_text_string}
    """
    if not texts_map:
        return {}

    glossary_rules = load_glossary()
    
    translation_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "translation_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "description": "The input ID."},
                                "translated_text": {"type": "string", "description": "The translated content."}
                            },
                            "required": ["id", "translated_text"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["items"],
                "additionalProperties": False
            }
        }
    }

    contents = [
        f"You are an expert English-to-{lang_to} translator for the game 'Dyson Sphere Program'.",
        "Your task is to translate the provided texts following these strict rules:",
        "",
        "1. **Translation Rules**:",
        "   - Translate the 'text' field into {lang_to}.",
        "   - Use 'context' (Chinese original) ONLY as a reference for meaning.",
        "   - If a term is a Proper Noun (e.g., 'Dyson Sphere', 'Icarus'), keep the ORIGINAL. For technical terms (e.g., 'Power', 'Iron'), TRANSLATE them into Italian using the context.",
        "   - NEVER return explanations like 'I cannot translate'.",
        "",
        "2. **Constraints**:",
        "   - STRICTLY preserve leading and trailing whitespace padding.",
        "   - **Character Budget**: Italian is longer, but for game UIs you MUST stay as close as possible to the 'len' value.",
        "   - Do NOT add spaces around variables like {0}, [1], %s.",
        "",
        "3. **Output Format**:",
        "   - You MUST return the result matching the strict JSON schema provided.",
    ]
    
    if glossary_rules:
        contents.append("\n**Glossary (Do Not Translate):**")
        contents.extend(glossary_rules)

    string_content = "\n".join(contents)
    user_content = json.dumps(texts_map, ensure_ascii=False)

    try:
        client = openai.OpenAI()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": string_content},
                {"role": "user", "content": f"Translate these items to {lang_to}: {user_content}"}
            ],
            response_format=translation_schema
        )

        response_content = completion.choices[0].message.content
        parsed_response = json.loads(response_content)
        
        result_dict = {}
        for item in parsed_response.get("items", []):
            result_dict[item["id"]] = item["translated_text"]
            
        return result_dict

    except Exception as e:
        console.print(f"[bold red]❌ Error translation batch:[/bold red] {e}")
        return {}

async def translate_batch_async(texts_map, lang_to, model="gpt-5-nano"):
    """
    Translate a batch of texts using OpenAI Structured Outputs (Strict Mode) asynchronously.
    
    Args:
        texts_map: Dictionary where keys are IDs and values are dicts with "text", "context", "len".
        lang_to: Target language code.
        model: OpenAI model identifier.
        
    Returns:
        dict: Mapping of {id: translated_text_string}
    """
    if not texts_map:
        return {}

    glossary_rules = load_glossary()
    
    translation_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "translation_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "description": "The input ID."},
                                "translated_text": {"type": "string", "description": "The translated content."}
                            },
                            "required": ["id", "translated_text"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["items"],
                "additionalProperties": False
            }
        }
    }

    contents = [
        f"You are an expert English-to-{lang_to} translator for the game 'Dyson Sphere Program'.",
        "Your task is to translate the provided texts following these strict rules:",
        "",
        "1. **Translation Rules**:",
        "   - Translate the 'text' field into {lang_to}.",
        "   - Use 'context' (Chinese original) ONLY as a reference for meaning.",
        "   - If a term is a Proper Noun (e.g., 'Dyson Sphere', 'Icarus'), keep the ORIGINAL. For technical terms (e.g., 'Power', 'Iron'), TRANSLATE them into Italian using the context.",
        "   - NEVER return explanations like 'I cannot translate'.",
        "",
        "2. **Constraints**:",
        "   - STRICTLY preserve leading and trailing whitespace padding.",
        "   - **Character Budget**: Italian is longer, but for game UIs you MUST stay as close as possible to the 'len' value.",
        "   - Do NOT add spaces around variables like {0}, [1], %s.",
        "",
        "3. **Output Format**:",
        "   - You MUST return the result matching the strict JSON schema provided.",
    ]
    
    if glossary_rules:
        contents.append("\n**Glossary (Do Not Translate):**")
        contents.extend(glossary_rules)

    string_content = "\n".join(contents)
    user_content = json.dumps(texts_map, ensure_ascii=False)

    try:
        client = openai.AsyncOpenAI()
        completion = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": string_content},
                {"role": "user", "content": f"Translate these items to {lang_to}: {user_content}"}
            ],
            response_format=translation_schema
        )

        response_content = completion.choices[0].message.content
        parsed_response = json.loads(response_content)
        
        result_dict = {}
        for item in parsed_response.get("items", []):
            result_dict[item["id"]] = item["translated_text"]
            
        return result_dict

    except Exception as e:
        console.print(f"[bold red]❌ Error translation batch:[/bold red] {e}")
        return {}