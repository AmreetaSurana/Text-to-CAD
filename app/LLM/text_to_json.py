import json
from typing import Dict
from app.LLM.client import client

TEXT_TO_JSON_SYSTEM_PROMPT = """
You are a AutoCAD design interpreter.

Convert the user's natural language description into a single, valid JSON object
that represents a CAD construction plan to be converted into CADQuery code.

ABSOLUTE RULES (no exceptions):
1. Output ONLY a JSON object. No text before or after.
2. The output MUST start with '{' and end with '}'.
3. Do NOT include explanations, markdown, comments, or formatting.
4. Do NOT return null, empty output, or arrays.
5. Use millimeters (mm) for all dimensions.
6. If dimensions are not specified, infer reasonable defaults and include them explicitly.
7. Follow this operation order strictly:
   Sketch → Extrude → Solid Modifications.
8. Describe all cuts and holes as post-extrusion features.
9. Use simple, deterministic field names only.
10. Always include "export_format": "stl".

JSON STRUCTURE (must follow exactly):
{
  "sketch": {
    "type": "square",
    "size": number
  },
  "extrude": {
    "height": number
  },
  "features": [
    {
      "type": "cut" | "hole",
      "shape": "circle" | "semi_circle",
      "dimensions": { }
    }
  ],
  "export_format": "stl"
}

Failure to follow these rules is unacceptable.
"""


def text_to_json(description: str) -> Dict:
    response = client.chat.completions.create(
        model="ignored",
        messages=[
            {"role": "system", "content": TEXT_TO_JSON_SYSTEM_PROMPT},
            {"role": "user", "content": description}
        ],
        temperature=0.0,
        max_tokens=1000
    )

    json_text = response.choices[0].message.content.strip()
    return json.loads(json_text)

