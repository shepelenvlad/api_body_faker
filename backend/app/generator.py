"""
Генерация JSON-тела на основе JSON Schema.

Приоритет значений для поля:
1. const               -> берём как есть
2. enum                -> случайный выбор из списка
3. example / default   -> берём как есть (автор схемы явно задал значение)
4. иначе               -> генерируем через Faker (по format, затем по имени поля,
                           затем по типу как fallback)

Ограничение v1: $ref / $defs не резолвятся. Если понадобится — легко добавить
resolve_ref() и прокидывать корневую схему вглубь рекурсии.
"""

import random
import re
from typing import Any

from faker import Faker

fake = Faker()

# Эвристики по ИМЕНИ поля — работают, если явный "format" в схеме не задан.
# Порядок важен: более специфичные паттерны должны идти раньше общих.
_FIELD_NAME_GENERATORS: list[tuple[re.Pattern, Any]] = [
    (re.compile(r"e[-_]?mail", re.I), lambda: fake.email()),
    (re.compile(r"first[-_]?name", re.I), lambda: fake.first_name()),
    (re.compile(r"last[-_]?name", re.I), lambda: fake.last_name()),
    (re.compile(r"full[-_]?name|^name$", re.I), lambda: fake.name()),
    (re.compile(r"phone", re.I), lambda: fake.phone_number()),
    (re.compile(r"address", re.I), lambda: fake.address().replace("\n", ", ")),
    (re.compile(r"city", re.I), lambda: fake.city()),
    (re.compile(r"country", re.I), lambda: fake.country()),
    (re.compile(r"company", re.I), lambda: fake.company()),
    (re.compile(r"^id$|_id$", re.I), lambda: str(fake.uuid4())),
    (re.compile(r"url|link", re.I), lambda: fake.url()),
    (re.compile(r"username|login", re.I), lambda: fake.user_name()),
    (re.compile(r"password", re.I), lambda: fake.password()),
    (re.compile(r"zip|postal", re.I), lambda: fake.postcode()),
    (re.compile(r"description|comment|note", re.I), lambda: fake.sentence()),
    (re.compile(r"title", re.I), lambda: fake.sentence(nb_words=4).rstrip(".")),
    (re.compile(r"price|amount|cost", re.I), lambda: round(random.uniform(1, 1000), 2)),
]

_FORMAT_GENERATORS = {
    "email": lambda: fake.email(),
    "date": lambda: fake.date(),
    "date-time": lambda: fake.iso8601(),
    "uuid": lambda: str(fake.uuid4()),
    "uri": lambda: fake.url(),
    "url": lambda: fake.url(),
    "hostname": lambda: fake.hostname(),
    "ipv4": lambda: fake.ipv4(),
    "ipv6": lambda: fake.ipv6(),
    "phone": lambda: fake.phone_number(),
}


def generate_from_schema(schema: dict, field_name: str = "") -> Any:
    if not isinstance(schema, dict):
        return None

    if "const" in schema:
        return schema["const"]
    if schema.get("enum"):
        return random.choice(schema["enum"])
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]

    schema_type = schema.get("type", "object")

    if schema_type == "object":
        properties = schema.get("properties", {})
        return {
            name: generate_from_schema(sub_schema, field_name=name)
            for name, sub_schema in properties.items()
        }

    if schema_type == "array":
        item_schema = schema.get("items", {})
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", max(min_items, 3))
        count = random.randint(min_items, max_items)
        return [generate_from_schema(item_schema, field_name=field_name) for _ in range(count)]

    if schema_type == "string":
        fmt = schema.get("format")
        if fmt in _FORMAT_GENERATORS:
            return _FORMAT_GENERATORS[fmt]()
        for pattern, generator in _FIELD_NAME_GENERATORS:
            if pattern.search(field_name):
                return generator()
        min_len = schema.get("minLength", 5)
        max_len = schema.get("maxLength", max(min_len, 10))
        return fake.text(max_nb_chars=max_len)[:max_len]

    if schema_type == "integer":
        return random.randint(schema.get("minimum", 0), schema.get("maximum", 1000))

    if schema_type == "number":
        return round(random.uniform(schema.get("minimum", 0), schema.get("maximum", 1000)), 2)

    if schema_type == "boolean":
        return random.choice([True, False])

    if schema_type == "null":
        return None

    return None
