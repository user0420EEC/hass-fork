#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автогенерация project_structure.json
------------------------------------
Скрипт проходит по всем файлам репозитория, собирает дерево конфигурации
Home Assistant / ESPHome / Zigbee2MQTT и создаёт JSON-файл для AI-контекста.
"""

import os, json, re, glob
from datetime import datetime, timezone
from pathlib import Path

# Каталоги и файлы, которые игнорируются при обходе
EXCLUDE_DIRS = {'.git', '.github', '__pycache__', 'venv', '.venv', '.idea'}
EXCLUDE_SUFFIXES = {'.pyc', '.log', '.tmp', '.bak'}

# Эвристические описания ключевых файлов
DESCR = {
    "configuration.yaml": "Главный файл конфигурации Home Assistant. Импортирует остальные YAML через !include.",
    "customize.yaml": "Кастомизация friendly_name, иконок и атрибутов.",
    "scripts.yaml": "Определение пользовательских скриптов (service calls, delay, последовательности).",
    "scenes.yaml": "Сцены (наборы состояний устройств).",
    "esphome": "Конфигурации устройств ESPHome (датчики, реле, контроллеры).",
    "zigbee2mqtt": "Настройки шлюза Zigbee2MQTT и устройств Zigbee.",
    "includes": "Подключаемые YAML-части конфигурации (sensors, switches и т.п.).",
    "blueprints": "Шаблоны автоматизаций Home Assistant."
}

INCLUDE_RE = re.compile(r'!\s*include[^\s]*\s+([^\s#]+)', re.IGNORECASE)


def is_skip_dir(d): return d in EXCLUDE_DIRS
def is_skip_file(p): return any(p.name.endswith(x) for x in EXCLUDE_SUFFIXES)


def yaml_includes(path: Path):
    if not path.suffix.lower().endswith('yaml'): return []
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
        return sorted(set(m.group(1) for m in INCLUDE_RE.finditer(text)))
    except Exception:
        return []


def describe(p: Path):
    for key, val in DESCR.items():
        if key in str(p): return val
    if p.suffix in ('.yaml', '.yml'): return 'YAML конфигурация.'
    if p.suffix == '.json': return 'JSON данные.'
    if p.suffix == '.py': return 'Python-скрипт.'
    return ''


def list_all(root='.'):
    files = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not is_skip_dir(d)]
        for f in fn:
            p = Path(dp, f)
            if is_skip_file(p): continue
            files.append(p)
    return sorted(files, key=str)


def top_level(root='.'):
    return [p for p in Path(root).iterdir() if not is_skip_dir(p.name)]


def build_root_map(entries):
    out = {}
    for e in entries:
        desc = describe(e)
        out[e.name] = {"type": "directory" if e.is_dir() else "file"}
        if desc: out[e.name]["description"] = desc
    return out


def collect_includes(files):
    incmap = {}
    for f in files:
        incs = yaml_includes(f)
        if incs: incmap[str(f)] = incs
    return incmap


def make_relations(incmap):
    return {k: sorted(set(v)) for k, v in incmap.items()}


def main():
    root = Path('.')
    files = list_all(root)
    incmap = collect_includes(files)
    data = {
        "project_name": "Home Assistant Configuration",
        "repository": "",
        "generated": datetime.now(timezone.utc).isoformat(),
        "root": build_root_map(top_level(root)),
        "files": [
            {"path": str(f), "type": "directory" if f.is_dir() else "file",
             **({"description": describe(f)} if describe(f) else {})}
            for f in files
        ],
        "yaml_includes": incmap,
        "relations": make_relations(incmap),
        "usage_rules": {
            "model_behavior": "Использовать JSON как карту структуры проекта.",
            "rules": [
                "ESPHome → /esphome/",
                "Zigbee → /zigbee2mqtt/",
                "Автоматизации → /blueprints/ или includes/automations.yaml",
                "Главные настройки → configuration.yaml",
                "Не выдумывать файлы вне структуры."
            ]
        }
    }
    Path("project_structure.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ project_structure.json обновлён")


if __name__ == "__main__":
    main()
