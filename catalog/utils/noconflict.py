# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# SOLVING THE METACLASS CONFLICT (Python recipe)
# http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/

import inspect
import types


def skip_redundant(iterable, skipset=None):
    # Redundant items are repeated items or items in the original skipset.
    if skipset is None:
        skipset = set()
    for item in iterable:
        if item not in skipset:
            skipset.add(item)
            yield item


def remove_redundant(metaclasses):
    skipset = set([types.ClassType])
    for meta in metaclasses:
        skipset.update(inspect.getmro(meta)[1:])
        return tuple(skip_redundant(metaclasses, skipset))

memoized_metaclasses_map = {}


def get_noconflict_metaclass(bases, left_metas, right_metas):
    # Not intended to be used outside of this module, unless you know
    # what you are doing.

    # make tuple of needed metaclasses in specified priority order
    metas = left_metas + tuple(map(type, bases)) + right_metas
    needed_metas = remove_redundant(metas)

    # return existing confict-solving meta, if any
    if needed_metas in memoized_metaclasses_map:
        return memoized_metaclasses_map[needed_metas]
    # nope: compute, memoize and return needed conflict-solving meta
    elif not needed_metas:
        meta = type
    elif len(needed_metas) == 1:
        meta = needed_metas[0]

    # check for recursion, can happen i.e. for Zope ExtensionClasses
    elif needed_metas == bases:
        raise TypeError('Incompatible root metatypes', needed_metas)
    else:
        metaname = '_' + ''.join([m.__name__ for m in needed_metas])
        meta = classmaker()(metaname, needed_metas, {})
    memoized_metaclasses_map[needed_metas] = meta
    return meta


def classmaker(left_metas=(), right_metas=()):
    def make_class(name, bases, adict):
        metaclass = get_noconflict_metaclass(bases, left_metas, right_metas)
        return metaclass(str(name), bases, adict)
    return make_class
