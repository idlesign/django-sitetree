import re


RE_TAG_VALUES = re.compile('>([^<]+)<')


def strip_tags(src):

    result = []
    for match in RE_TAG_VALUES.findall(src):
        match = match.strip()
        if match:
            result.append(match)

    return '|'.join(result)
