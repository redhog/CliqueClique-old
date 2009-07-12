def subclass_dict(d1, d2):
    res = dict(d1)
    res.update(d2)
    return res

def bidirectional(obj1, obj2):
    yield (obj1, obj2)
    yield (obj2, obj1)
