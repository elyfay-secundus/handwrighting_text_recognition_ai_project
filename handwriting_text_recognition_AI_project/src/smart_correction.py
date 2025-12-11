import re

PATTERN_RM = re.compile(r'\b([A-Z])rm([a-zA-Z]+)\b')
PATTERN_RM_UPPER = re.compile(r'rm(?=[A-Z])')
PATTERN_RM_AFTER = re.compile(r'(?<=[A-Z])rm')
PATTERN_RM_STANDALONE = re.compile(r'\brm\b')
PATTERN_RN_STANDALONE = re.compile(r'\bRn\b')
PATTERN_RN_BETWEEN = re.compile(r'(?<=[A-Z])rn(?=[A-Z])')
PATTERN_RN_END = re.compile(r'(?<=[A-Z])rn\b')
PATTERN_NN_BETWEEN = re.compile(r'(?<=[A-Z])nn(?=[A-Z])')
PATTERN_NN_STANDALONE = re.compile(r'\bnn\b')
PATTERN_SHORT_WORDS = re.compile(r'\b([A-Z]{1,3})([a-z]{1,3})\b')

CHAR_REPLACEMENTS = [
    (re.compile(r'\b0(?=[A-Z])'), 'O'),
    (re.compile(r'(?<=[A-Z])0(?=[A-Z])'), 'O'),
    (re.compile(r'(?<=[A-Z])0\b'), 'O'),
    (re.compile(r'\b1(?=[A-Z])'), 'I'),
    (re.compile(r'(?<=[A-Z])1(?=[A-Z])'), 'I'),
    (re.compile(r'\b5(?=[A-Z])'), 'S'),
    (re.compile(r'(?<=[A-Z])5\b'), 'S'),
    (re.compile(r'\b8(?=[A-Z])'), 'B'),
    (re.compile(r'(?<=[A-Z])8\b'), 'B'),
    (re.compile(r'\bl(?=[A-Z])'), 'I'),
    (re.compile(r'(?<=[A-Z])l\b'), 'I'),
    (re.compile(r'\bvv'), 'W'),
    (re.compile(r'(?<=[A-Z])vv'), 'W'),
    (re.compile(r'(?<=[A-Z])v\b'), 'Y'),
]

def correct_common_mistakes(text: str) -> dict:
    original = text
    corrections = []
    corrected = text

    matches = list(PATTERN_RM.finditer(corrected))
    for match in reversed(matches):
        original_word = match.group(0)
        fixed_word = match.group(1) + 'M' + match.group(2).upper()
        corrected = corrected[:match.start()] + fixed_word + corrected[match.end():]
        corrections.append(f"'{original_word}' → '{fixed_word}'")

    corrected = PATTERN_RM_UPPER.sub('M', corrected)
    corrected = PATTERN_RM_AFTER.sub('M', corrected)
    corrected = PATTERN_RM_STANDALONE.sub('M', corrected)

    corrected = PATTERN_RN_STANDALONE.sub('M', corrected)
    corrected = PATTERN_RN_BETWEEN.sub('M', corrected)
    corrected = PATTERN_RN_END.sub('M', corrected)

    corrected = PATTERN_NN_BETWEEN.sub('M', corrected)
    corrected = PATTERN_NN_STANDALONE.sub('m', corrected)

    def uppercase_short_words(match):
        word = match.group(0)
        if 2 <= len(word) <= 5:
            return word.upper()
        return word
    before = corrected
    corrected = PATTERN_SHORT_WORDS.sub(uppercase_short_words, corrected)
    if before != corrected:
        corrections.append(f"Fixed capitalization in short words")

    for pattern, replacement in CHAR_REPLACEMENTS:
        before = corrected
        corrected = pattern.sub(replacement, corrected)
        if before != corrected:
            corrections.append(f"Fixed character confusion")

    return {
        'original': original,
        'corrected': corrected,
        'changed': original != corrected,
        'corrections': corrections
    }


def smart_correct(text: str) -> dict:
    auto_corrected = correct_common_mistakes(text)

    return {
        'original': text,
        'auto_corrected': auto_corrected['corrected'],
        'corrections_applied': auto_corrected['corrections'],
        'best_result': auto_corrected['corrected']
    }
