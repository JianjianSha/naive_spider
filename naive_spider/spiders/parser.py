'''
DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE

Copyright (c) 2021 Jianjian Sha <501834524@qq.com>


Tag path:

<tag name>[[x]][.<cls>|#<id>][::|:<attr>]

tag name: Name of the destination tag. `tag name` can be a regular expr.

optional:

    [x]: In all tags with the name <tag name>, select the x-th tag. If omitted, select the first tag.
            If `x=*`, then we select all tags. Note that `x=*` cannot exist with `#<id>` at the 
            same time. `x` value starts from `0`.

    .<cls>|#<id>: Suffix. if specified with `.<cls`, then select the tag with a class <cls>,
                    if specified with `#<id>`, then select the tag with a id <id>.
                    You can specify many limitations with each other splitted by `|`, and these
                    specifiers have a logic of `OR`.

    ::|:<attr>: Extract the tag's content if given `::`, or the attribute <attr>'s value if given 
                    `:<attr>`.

1. You can specify many specifiers with each other splitted by a blank space `<space>`. Be note that 
the value extractor `::|:<attr>` can only be supplied for the last specifier.

2. Only the last specifier can have `[x]` when `x=*`, or else any specifier can have a `[x]`.
'''
from pickle import NONE
from bs4 import Tag, NavigableString, Comment
import re


def get_tag(tag, path):
    def _get_tag(t, p):
        '''
        p has a form of `<tag name>[[x]][.<cls>|#<id>]`, where the value extractor is splitted out.
        '''
        if t is None or not p:
            return t            # INVALID
        
        if p == '__next_sibling__':
            return t.find_next_sibling(lambda tt: isinstance(tt, Tag))
        
        if p[0] == '>':
            p = p[1:]
            recursive = False
        else:
            recursive = True
        
        # if t.name == 'table' and t.tbody:
        #     t = t.tbody

        for i in range(len(p)):
            if p[i] in '.#[':
                break
        if i < len(p) - 1:
            tname, suffix = p[:i], p[i:]
            if p[i] == '[':
                idx, suffix = suffix[1:].split(']')
                # idx = None if idx == '*' else int(idx)
                if idx == '*':
                    idx = None
                elif ':' in idx:
                    idx = [int(ss) if len(ss) > 0 else None for ss in idx.split(':')]
                    if idx[0] is None:
                        idx[0] = 0
                else:
                    idx = int(idx)
            else:
                idx = 0
        else:
            tname = p
            suffix = None
            idx = 0


        if suffix:
            for sp in suffix.split('|'):    # OR: return the first matched tag
                if sp[0] == '#':
                    id_ = sp[1:]
                    res = t.find(id=id_)
                    if res:
                        return res

                elif sp[0] == '.':
                    cls_ = sp[1:]
                    
                    res = t.find_all(lambda tt: isinstance(tt, Tag) and re.match(tname, tt.name) and tt.get('class') and (cls_ in tt.get('class')), recursive=recursive)
                    if res:
                        
                        if idx is None:
                            return res
                        if isinstance(idx, int) and 0 <= idx < len(res):
                            return res[idx]
                        if isinstance(idx, list):
                            if idx[1] is not None:
                                return res[idx[0]:idx[1]]
                            else:
                                return res[idx[0]:]
                        return None
        else:
            res = t.find_all(lambda tt: isinstance(tt, Tag) and re.match(tname, tt.name), recursive=recursive)
            if res:
                if idx is None:
                    return res
                if isinstance(idx, int) and 0 <= idx < len(res):
                    return res[idx]
                if isinstance(idx, list):
                    if idx[1] is not None:
                        return res[idx[0]:idx[1]]
                    else:
                        return res[idx[0]:]
        return None

    t = tag
    if ':::' in path:
        flag = 3
    elif '::' in path:
        flag = 2
        path = path.split('::')[0]
    elif ':' in path:
        lft, rgt = path.rsplit(':', 1)
        if ']' not in rgt:
            flag = 1
            path, attr = path.rsplit(':', 1)
        else:
            flag = 0
    else:
        flag = 0

    paths = path.split(' ')

    for p in paths:
        # orig = t
        t = _get_tag(t, p)
        if t is None:
            return None
    
    lf = isinstance(t, list)
    if flag == 1:
        res = t.get(attr) if not lf else [tt.get(attr) for tt in t]
        return [re.strip() for re in res if re] if lf else (res.strip() if res else None)
    if flag == 2:
        return get_tag_text(t) if not lf else [get_tag_text(tt) for tt in t]
    return t


def get_tag_text(tag):
    texts = []
    for tt in tag.children:
        if isinstance(tt, NavigableString) and not isinstance(tt, Comment):
            texts.append(str(tt).strip())
    return ''.join(texts)