#!/usr/bin/env python3
"""Merge Fatawa Razviya Jild 2 easy-Urdu tashreeh v4 chunks into jild-02.json.

Reads the 14 chunk files listed in chunks-manifest-v4-jild02.json,
concatenates them in order 01 -> 14, derives start_page = min(pages)
where the field is absent, normalises page markers, validates, and
writes {"masail": [...]} to jild-02.json.

ORDER -- chunk order is the order (no quirk, unlike Jild 1 Part 2):
  The v3 merged file ~/workspace/fatawa-app/content/tashreeh/jild-02.json
  has ID order == concatenation order of the v4 chunks 01..14 (verified
  locally by the merge agent: all 187 ids match the v3 sequence exactly).
  Do NOT sort or reorder. Within each chunk, items keep file order.

START_PAGE (rule 2): chunks 06 and 12 have NO start_page field in v3 or
  v4 (preserved faithfully by the workers). The merged v3 file has
  start_page == min(pages) for all 187 items, so deriving
  start_page = min(pages) when the field is absent reproduces v3
  exactly. Items that already carry start_page keep their value (it
  already equals min(pages) for every one of them -- asserted below).

MARKER NORMALISATION (the only text transformation): page markers, if
  present, are normalised to the single form [safha N] written with the
  Urdu word for page:
  - lenticular-bracket form (U+3010/U+3011 around the Urdu word for
    page + number) -> [safha N]
  - [short form] -> [safha N]
  - [safha N] stays as-is
  Applied to every string field of every item (jawab, sawal, title,
  notes). The 14 v4 chunks contain ZERO markers of any form (verified
  locally), so normalisation is expected to be a no-op here; the code
  stays so the merge is robust and the "none remain" assertions still
  run. No other text is touched and no markers are invented.
  NOTE: the literal lenticular-bracket characters are written here only
  as U+3010/U+3011 escapes, never as literal characters in this file.

VALIDATION (fails loudly on any violation):
  187 items; ID sequence EXACTLY == the v3 merged file's ID sequence
  (embedded below as V3_IDS, copied verbatim from
  ~/workspace/fatawa-app/content/tashreeh/jild-02.json); pages per item
  identical to v3 (embedded as V3_PAGES, same source, verified against
  the v3 file before pushing); 674 unique pages (min 5, max 711);
  volume_ids == {58}; start_page == min(pages) for every item (after
  derivation); zero empty tashreeh_jawab; no lenticular / short markers
  remain; first id jild2-p5, last id jild2-p698.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = "chunks-manifest-v4-jild02.json"

# Concatenation order: chunk files 01 -> 14, in order.
CHUNK_ORDER = [f"jild-02-chunk-{n:02d}.json" for n in range(1, 15)]

EXPECTED_ITEMS = 187
EXPECTED_PAGES = 674
EXPECTED_MIN_PAGE = 5
EXPECTED_MAX_PAGE = 711
EXPECTED_VOLUME_IDS = {58}
EXPECTED_FIRST_ID = "jild2-p5"
EXPECTED_LAST_ID = "jild2-p698"

# v3 ID sequence, verbatim from content/tashreeh/jild-02.json.
V3_IDS = ["jild2-p5", "jild2-masala-23-p37", "jild2-masala-24-p38", "jild2-masala-25-p38", "jild2-masala-26-p39", "jild2-masala-27-p39", "jild2-masala-28-p43", "jild2-p47", "jild2-p52", "jild2-p56", "jild2-p61", "jild2-p67", "jild2-p71", "jild2-p75", "jild2-p83", "jild2-p85", "jild2-p89", "jild2-p92", "jild2-p101", "jild2-p105", "jild2-masala-29-p113", "jild2-p114-faida-1", "jild2-p114-faida-2", "jild2-p117", "jild2-p119", "jild2-p120", "jild2-p122", "jild2-p133", "jild2-p135", "jild2-p141", "jild2-p143", "jild2-p146", "jild2-p152", "jild2-p159", "jild2-p165", "jild2-p167", "jild2-p174", "jild2-p177", "jild2-p183", "jild2-p185", "jild2-p188", "jild2-p191", "jild2-p194", "jild2-p197", "jild2-p199", "jild2-p201", "jild2-p204", "jild2-p206", "jild2-p209", "jild2-p212", "jild2-p214", "jild2-p217", "jild2-p220", "jild2-p223", "jild2-p226", "jild2-p228", "jild2-p230", "jild2-p233", "jild2-masala-30-p250", "jild2-masala-31-p260", "jild2-masala-32-p261", "jild2-masala-33-p272", "jild2-masala-34-p273", "jild2-masala-35-p273", "jild2-masala-36-p274", "jild2-masala-37-p274", "jild2-masala-38-p275", "jild2-masala-39-p278", "jild2-masala-40-p278", "jild2-masala-41-p281", "jild2-masala-42-p282", "jild2-masala-43-p283", "jild2-masala-44-p286", "jild2-masala-45-p309", "jild2-masala-46-p314", "jild2-masala-47-p315", "jild2-masala-48-p321", "jild2-masala-49-p322", "jild2-p332", "jild2-p333", "jild2-p336", "jild2-masala-52-p338", "jild2-masala-53-p352", "jild2-p353-asl-1", "jild2-p353-asl-2", "jild2-p354-asl-3", "jild2-p357-asl-4", "jild2-p365-asl-5", "jild2-p365-asl-6", "jild2-p370-asl-7", "jild2-p371-asl-8", "jild2-p373-asl-9", "jild2-p377-asl-10", "jild2-p383", "jild2-p386", "jild2-p389", "jild2-p392", "jild2-p396", "jild2-p400", "jild2-p403", "jild2-p406", "jild2-p408", "jild2-p411", "jild2-p414", "jild2-p418", "jild2-p423", "jild2-masala-54-p426", "jild2-masala-55-p452", "jild2-p476", "jild2-p477", "jild2-p478", "jild2-p479", "jild2-p484", "jild2-p490", "jild2-p491", "jild2-p495", "jild2-p501", "jild2-p509", "jild2-p511", "jild2-p515", "jild2-p520", "jild2-masala-3-p526", "jild2-masala-3-p528", "jild2-masala-3-p530", "jild2-masala-3-p532", "jild2-masala-3-p534", "jild2-masala-3-p536", "jild2-masala-3-p538", "jild2-masala-3-p540", "jild2-masala-3-p542", "jild2-masala-3-p544", "jild2-masala-3-p546", "jild2-masala-3-p548", "jild2-masala-3-p550", "jild2-masala-3-p553", "jild2-masala-3-p558", "jild2-masala-3-p562", "jild2-masala-3-p564", "jild2-masala-3-p566", "jild2-masala-3-p568", "jild2-masala-3-p572", "jild2-masala-3-p574", "jild2-p576", "jild2-p577", "jild2-p578", "jild2-p581", "jild2-p582", "jild2-p584", "jild2-p586", "jild2-p587", "jild2-p590", "jild2-p594", "jild2-p595", "jild2-p596", "jild2-p597", "jild2-p599", "jild2-p601", "jild2-p602", "jild2-p607", "jild2-p607b", "jild2-p611", "jild2-p613", "jild2-p622", "jild2-p623", "jild2-p625", "jild2-p626", "jild2-p627", "jild2-p628", "jild2-p630", "jild2-p634", "jild2-p640", "jild2-p643", "jild2-p648", "jild2-p649", "jild2-p651", "jild2-p653", "jild2-p655", "jild2-p657", "jild2-p664", "jild2-p667", "jild2-p673", "jild2-p678", "jild2-p681", "jild2-p685", "jild2-p688", "jild2-p694", "jild2-p698"]

# v3 pages per item id, verbatim from content/tashreeh/jild-02.json.
V3_PAGES = {
"jild2-p5": [5, 6, 7],
"jild2-masala-23-p37": [37],
"jild2-masala-24-p38": [38],
"jild2-masala-25-p38": [38, 39],
"jild2-masala-26-p39": [39],
"jild2-masala-27-p39": [39, 40, 41],
"jild2-masala-28-p43": [43, 44, 45, 46, 47],
"jild2-p47": [47, 48, 49, 50, 51],
"jild2-p52": [52, 53, 54, 55, 56],
"jild2-p56": [56, 57, 58, 59, 60, 61],
"jild2-p61": [61, 62, 63, 64, 65, 66, 67],
"jild2-p67": [67, 68, 69, 70, 71],
"jild2-p71": [71, 72, 73, 74, 75],
"jild2-p75": [75, 76, 77, 78, 79, 80, 81, 82],
"jild2-p83": [83, 84, 85],
"jild2-p85": [85, 86, 87, 88, 89],
"jild2-p89": [89, 90, 91, 92],
"jild2-p92": [92, 93, 94, 95, 96, 97, 98, 99, 100, 101],
"jild2-p101": [101, 102, 103, 104, 105],
"jild2-p105": [105, 106, 107, 108, 109, 110, 111, 112],
"jild2-masala-29-p113": [113, 114],
"jild2-p114-faida-1": [114],
"jild2-p114-faida-2": [114, 115, 116, 117],
"jild2-p117": [117, 118, 119],
"jild2-p119": [119, 120],
"jild2-p120": [120, 121],
"jild2-p122": [122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132],
"jild2-p133": [133, 134],
"jild2-p135": [135, 136, 137, 138, 139, 140, 141],
"jild2-p141": [141, 142, 143],
"jild2-p143": [143, 144, 145],
"jild2-p146": [146, 147, 148, 149, 150, 151],
"jild2-p152": [152, 153, 154, 155, 156, 157, 158, 159],
"jild2-p159": [159, 160, 161, 162, 163, 165],
"jild2-p165": [165, 166, 167],
"jild2-p167": [167, 168, 169, 170, 171, 172, 173],
"jild2-p174": [174, 175, 176],
"jild2-p177": [177, 178, 179, 180, 181, 182],
"jild2-p183": [183, 184],
"jild2-p185": [185, 186, 187],
"jild2-p188": [188, 189, 190],
"jild2-p191": [191, 192, 193],
"jild2-p194": [194, 195, 196],
"jild2-p197": [197, 198],
"jild2-p199": [199, 200],
"jild2-p201": [201, 202, 203],
"jild2-p204": [204, 205],
"jild2-p206": [206, 207, 208],
"jild2-p209": [209, 210, 211],
"jild2-p212": [212, 213],
"jild2-p214": [214, 215, 216],
"jild2-p217": [217, 218, 219],
"jild2-p220": [220, 221, 222],
"jild2-p223": [223, 224, 225],
"jild2-p226": [226, 227],
"jild2-p228": [228, 229],
"jild2-p230": [230, 231, 232],
"jild2-p233": [233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249],
"jild2-masala-30-p250": [250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260],
"jild2-masala-31-p260": [260, 261],
"jild2-masala-32-p261": [261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272],
"jild2-masala-33-p272": [272, 273],
"jild2-masala-34-p273": [273],
"jild2-masala-35-p273": [273, 274],
"jild2-masala-36-p274": [274],
"jild2-masala-37-p274": [274, 275],
"jild2-masala-38-p275": [275, 276, 277, 278],
"jild2-masala-39-p278": [278],
"jild2-masala-40-p278": [278, 279, 280, 281],
"jild2-masala-41-p281": [281, 282],
"jild2-masala-42-p282": [282, 283],
"jild2-masala-43-p283": [283, 284, 285],
"jild2-masala-44-p286": [286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309],
"jild2-masala-45-p309": [309, 310, 311, 312, 313],
"jild2-masala-46-p314": [314, 315],
"jild2-masala-47-p315": [315, 316, 317, 318, 319, 320, 321],
"jild2-masala-48-p321": [321],
"jild2-masala-49-p322": [322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332],
"jild2-p332": [332, 333],
"jild2-p333": [333, 334, 335],
"jild2-p336": [336, 337, 338],
"jild2-masala-52-p338": [338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352],
"jild2-masala-53-p352": [352, 353],
"jild2-p353-asl-1": [353],
"jild2-p353-asl-2": [353, 354],
"jild2-p354-asl-3": [354, 355, 356, 357],
"jild2-p357-asl-4": [357, 358, 359, 360, 361, 362, 363, 364],
"jild2-p365-asl-5": [365],
"jild2-p365-asl-6": [365, 366, 367, 368, 369, 370],
"jild2-p370-asl-7": [370, 371],
"jild2-p371-asl-8": [371, 372, 373],
"jild2-p373-asl-9": [373, 374, 375, 376, 377],
"jild2-p377-asl-10": [377, 378, 379, 380, 381, 382, 383],
"jild2-p383": [383, 384, 385],
"jild2-p386": [386, 387, 388, 389],
"jild2-p389": [389, 390, 391],
"jild2-p392": [392, 393, 394, 395],
"jild2-p396": [396, 397, 398, 399],
"jild2-p400": [400, 401, 402],
"jild2-p403": [403, 404, 405],
"jild2-p406": [406, 407, 408],
"jild2-p408": [408, 409, 410, 411],
"jild2-p411": [411, 412, 413],
"jild2-p414": [414, 415, 416, 417],
"jild2-p418": [418, 419, 420, 421, 422],
"jild2-p423": [423, 424],
"jild2-masala-54-p426": [426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451],
"jild2-masala-55-p452": [452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475],
"jild2-p476": [476, 477],
"jild2-p477": [477, 478],
"jild2-p478": [478, 479],
"jild2-p479": [479, 480, 481, 482, 483, 484],
"jild2-p484": [484, 485, 486, 487, 488, 489],
"jild2-p490": [490, 491],
"jild2-p491": [491, 492, 493, 494, 495],
"jild2-p495": [495, 496, 497, 498, 499, 500],
"jild2-p501": [501, 502, 503, 504, 505, 506, 507, 508, 509],
"jild2-p509": [509, 510, 511],
"jild2-p511": [511, 512, 513, 514, 515],
"jild2-p515": [515, 516, 517, 518, 519, 520],
"jild2-p520": [520, 521, 522, 523, 524, 525],
"jild2-masala-3-p526": [526, 527],
"jild2-masala-3-p528": [528, 529],
"jild2-masala-3-p530": [530, 531],
"jild2-masala-3-p532": [532, 533],
"jild2-masala-3-p534": [534, 535],
"jild2-masala-3-p536": [536, 537],
"jild2-masala-3-p538": [538, 539],
"jild2-masala-3-p540": [540, 541],
"jild2-masala-3-p542": [542, 543],
"jild2-masala-3-p544": [544, 545],
"jild2-masala-3-p546": [546, 547],
"jild2-masala-3-p548": [548, 549],
"jild2-masala-3-p550": [550, 551, 552],
"jild2-masala-3-p553": [553, 554, 555, 556, 557],
"jild2-masala-3-p558": [558, 559, 560, 561],
"jild2-masala-3-p562": [562, 563],
"jild2-masala-3-p564": [564, 565],
"jild2-masala-3-p566": [566, 567],
"jild2-masala-3-p568": [568, 569, 570, 571],
"jild2-masala-3-p572": [572, 573],
"jild2-masala-3-p574": [574, 575],
"jild2-p576": [576, 577],
"jild2-p577": [577, 578],
"jild2-p578": [578, 579, 580, 581],
"jild2-p581": [581, 582],
"jild2-p582": [582, 583, 584],
"jild2-p584": [584, 585, 586],
"jild2-p586": [586, 587],
"jild2-p587": [587, 588, 589, 590],
"jild2-p590": [590, 591, 592, 593, 594],
"jild2-p594": [594, 595],
"jild2-p595": [595, 596],
"jild2-p596": [596, 597],
"jild2-p597": [597, 598, 599],
"jild2-p599": [599, 600, 601],
"jild2-p601": [601, 602],
"jild2-p602": [602, 603, 604, 605, 606, 607],
"jild2-p607": [607],
"jild2-p607b": [607, 608, 609, 610, 611],
"jild2-p611": [611, 612, 613],
"jild2-p613": [613, 614, 615, 616, 617, 618, 619, 620, 621, 622],
"jild2-p622": [622, 623],
"jild2-p623": [623, 624, 625],
"jild2-p625": [625, 626, 627],
"jild2-p626": [626, 627],
"jild2-p627": [627],
"jild2-p628": [628, 629, 630],
"jild2-p630": [630, 631, 632, 633, 634],
"jild2-p634": [634, 635, 636, 637, 638, 639],
"jild2-p640": [640, 641, 642, 643],
"jild2-p643": [643, 644, 645, 646, 647],
"jild2-p648": [648, 649],
"jild2-p649": [649, 650, 651],
"jild2-p651": [651, 652],
"jild2-p653": [653, 654, 655],
"jild2-p655": [655, 656, 657],
"jild2-p657": [657, 658, 659, 660, 661, 662, 663],
"jild2-p664": [664, 665, 666, 667],
"jild2-p667": [667, 668, 669, 670, 671, 672, 673],
"jild2-p673": [673, 674, 675, 676, 677],
"jild2-p678": [678, 679, 680],
"jild2-p681": [681, 682, 683, 684],
"jild2-p685": [685, 686, 687, 688],
"jild2-p688": [688, 689, 690, 691, 692, 693, 694],
"jild2-p694": [694, 696, 697],
"jild2-p698": [698, 699, 700, 701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711],
}

# The Urdu word for "page" is safha; the canonical marker is [safha N].
# Lenticular brackets are U+3010 (open) and U+3011 (close); the short
# form is "[safha-initial N]" with the single-letter abbreviation.
# All three patterns are built from escapes so this file never contains
# a literal lenticular-bracket pair.
SAFHA = "\u0635\u0641\u062d\u06c1"  # the Urdu word for page
RE_LENTICULAR = re.compile("\u3010" + SAFHA + " (\\d+)\u3011")
RE_SHORT = re.compile("\\[\u0635 (\\d+)\\]")
RE_FULL = re.compile("\\[" + SAFHA + " \\d+\\]")
LENTICULAR_PREFIX = "\u3010" + SAFHA  # for the "none remain" check
SHORT_PREFIX_RE = re.compile("\\[\u0635 \\d+\\]")

# Canonical output key order for every item (the JSON contract).
ITEM_KEYS = ["id", "title", "volume_id", "pages", "start_page",
             "tashreeh_sawal", "tashreeh_jawab", "notes"]


def normalise_markers(text):
    """Normalise page markers in one string. Returns (new_text, counts)."""
    counts = {"lenticular": 0, "short": 0, "full_before": 0}
    counts["full_before"] = len(RE_FULL.findall(text))
    text, n1 = RE_LENTICULAR.subn("[" + SAFHA + " \\1]", text)
    counts["lenticular"] = n1
    text, n2 = RE_SHORT.subn("[" + SAFHA + " \\1]", text)
    counts["short"] = n2
    return text, counts


def normalise_item(item):
    """Normalise markers in every string field of one item (recursively
    through lists/dicts). Returns per-form counts for this item."""
    totals = {"lenticular": 0, "short": 0, "full_before": 0}

    def walk(value):
        if isinstance(value, str):
            new, c = normalise_markers(value)
            for k in totals:
                totals[k] += c[k]
            return new
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value

    for key in list(item.keys()):
        item[key] = walk(item[key])
    return totals


def main():
    assert len(V3_IDS) == EXPECTED_ITEMS, "embedded V3_IDS length mismatch"
    assert set(V3_PAGES) == set(V3_IDS), "embedded V3_PAGES keys != V3_IDS"
    assert sum(len(v) for v in V3_PAGES.values()) >= EXPECTED_PAGES

    manifest = json.load(open(os.path.join(BASE, MANIFEST), encoding="utf-8"))
    entries = manifest["chunks"]
    assert len(entries) == 14, f"expected 14 manifest entries, got {len(entries)}"
    assert all(e.get("status") == "done" for e in entries), "not all chunks done"
    by_file = {e["file"]: e for e in entries}
    assert set(by_file) == set(CHUNK_ORDER), (
        f"manifest files != CHUNK_ORDER: "
        f"missing={set(CHUNK_ORDER) - set(by_file)} "
        f"extra={set(by_file) - set(CHUNK_ORDER)}"
    )

    all_items = []
    derived = []
    for fname in CHUNK_ORDER:
        path = os.path.join(BASE, fname)
        d = json.load(open(path, encoding="utf-8"))
        items = d["masail"]
        entry = by_file[fname]
        assert len(items) == entry["items"], (
            f"{fname}: {len(items)} items, manifest says {entry['items']}"
        )
        # Marker normalisation, with before/after counts per chunk.
        before = {"lenticular": 0, "short": 0, "full_before": 0}
        for it in items:
            c = normalise_item(it)
            for k in before:
                before[k] += c[k]
        after_full = sum(
            len(RE_FULL.findall(json.dumps(it, ensure_ascii=False)))
            for it in items
        )
        print(
            f"{fname}: {len(items)} items | markers before: "
            f"lenticular={before['lenticular']} short={before['short']} "
            f"full={before['full_before']} | after: full={after_full}"
        )
        assert after_full == (
            before["lenticular"] + before["short"] + before["full_before"]
        ), f"{fname}: marker count changed by normalisation!"
        # Derive start_page = min(pages) where absent (chunks 06, 12).
        for it in items:
            if "start_page" not in it:
                it["start_page"] = min(it["pages"])
                derived.append(it["id"])
        all_items.extend(items)

    print(f"concatenated: {len(all_items)} items")
    print(f"start_page derived for {len(derived)} items (chunks 06 + 12)")
    assert len(all_items) == EXPECTED_ITEMS, (
        f"expected {EXPECTED_ITEMS} items, got {len(all_items)}"
    )

    # Rebuild each item in the canonical key order (the JSON contract).
    canonical = []
    for it in all_items:
        assert set(it.keys()) == set(ITEM_KEYS), (
            f"{it.get('id')}: keys {sorted(it.keys())} != {sorted(ITEM_KEYS)}"
        )
        canonical.append({k: it[k] for k in ITEM_KEYS})
    all_items = canonical

    # Validation.
    ids = [it["id"] for it in all_items]
    assert ids == V3_IDS, (
        f"ID sequence != v3: first diff at "
        f"{next((i for i, (a, b) in enumerate(zip(ids, V3_IDS)) if a != b), min(len(ids), len(V3_IDS)))}"
    )
    assert len(ids) == len(set(ids)), (
        f"DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}"
    )
    empty = [it["id"] for it in all_items if not it.get("tashreeh_jawab")]
    assert not empty, f"EMPTY JAWAB: {empty}"
    vols = set(it.get("volume_id") for it in all_items)
    assert vols == EXPECTED_VOLUME_IDS, f"volume_ids {vols} != {EXPECTED_VOLUME_IDS}"
    pages = set()
    for it in all_items:
        assert it["pages"] == V3_PAGES[it["id"]], (
            f"{it['id']}: pages {it['pages']} != v3 {V3_PAGES[it['id']]}"
        )
        pages.update(it["pages"])
    assert len(pages) == EXPECTED_PAGES, (
        f"expected {EXPECTED_PAGES} unique pages, got {len(pages)}"
    )
    assert min(pages) == EXPECTED_MIN_PAGE, f"min page {min(pages)}"
    assert max(pages) == EXPECTED_MAX_PAGE, f"max page {max(pages)}"
    exceptions = {
        it["id"] for it in all_items if it["start_page"] != min(it["pages"])
    }
    assert not exceptions, f"start_page != min(pages): {sorted(exceptions)}"
    assert ids[0] == EXPECTED_FIRST_ID, f"first id {ids[0]}"
    assert ids[-1] == EXPECTED_LAST_ID, f"last id {ids[-1]}"

    out = {"masail": all_items}
    out_text = json.dumps(out, ensure_ascii=False, indent=1)
    assert LENTICULAR_PREFIX not in out_text, "lenticular markers remain in output!"
    assert not SHORT_PREFIX_RE.search(out_text), "short markers remain in output!"
    total_markers = len(RE_FULL.findall(out_text))
    print(
        f"VALIDATION PASSED: {len(all_items)} items, {len(pages)} unique pages "
        f"(min {min(pages)}, max {max(pages)}), volume_ids {sorted(vols)}, "
        f"first {ids[0]}, last {ids[-1]}, start_page == min(pages) for all, "
        f"derived start_page for {len(derived)} items, markers {total_markers}"
    )

    with open(os.path.join(BASE, "jild-02.json"), "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"WROTE jild-02.json: {len(out_text.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
