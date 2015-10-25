

def convert_json_key_from_unicode(item):
    if isinstance(item, unicode):
        return item.encode('utf-8')
    else:
        return item


def convert_json_dictvalue_from_unicode(item):
    if isinstance(input, dict) or isinstance(input, list):
        return convert_json_from_unicode(item)
    else:
        return item


def convert_json_from_unicode(input):
    if isinstance(input, dict):
        return {convert_json_key_from_unicode(key): convert_json_from_unicode(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert_json_from_unicode(element) for element in input]
    else:
        return input


def remove_all_non_printables(s):
    # skip it all and just return the unicode
    return s
    # out = ''
    # try:
    #     out = s.encode('ascii', 'ignore').decode('ascii')
    #     #print 'DECODING:' % out
    # except Exception as ex:
    #     #print 'EXCEPTION decoding ascii: %s' % str(ex)
    #     pass
    # #print 'DECODING: done'
    # return out