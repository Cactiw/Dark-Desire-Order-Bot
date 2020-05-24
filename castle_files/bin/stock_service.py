from castle_files.work_materials.equipment_constants import equipment_names, get_equipment_by_name, \
    get_equipment_by_code

from castle_files.work_materials.item_consts import items
from castle_files.work_materials.resource_constants import resources, resources_reverted, get_resource_code_by_name
from castle_files.work_materials.alch_constants import alch_recipes

import logging
import traceback


def get_item_code_by_name(name):
    name = name.lower()
    for num, elem in list(items.items()):
        if name == elem[1].lower():
            code = "k" + num
            return code
        elif elem[0].lower() in name and "recipe" in name:
            code = "r" + num
            return code
        else:
            continue
    item = get_equipment_by_name(name)
    if item is not None:
        return item.type + item.code
    item = alch_recipes.get(name.lower())
    if item is not None:
        return item.get("code")
    item = get_resource_code_by_name(name)
    # print(name, item)
    return item


def get_item_name_by_code(code):
    try:
        item = get_equipment_by_code(code)
        if item is not None:
            return item.name
        item = resources_reverted.get(code)
        if item is not None:
            return item
        if code[0] in ["k", "r"]:
            item = items.get(code[1:])
            if code[0] == 'k':
                return item[1]
            if code[0] == 'r':
                return item[0] + " recipe"
        if code[0] == "p":
            for name, potion in list(alch_recipes.items()):
                if potion.get("code") == code:
                    return name
        return code
    except Exception:
        logging.error(traceback.format_exc())
        return code
