'''
DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE

Copyright (c) 2021 Jianjian Sha <501834524@qq.com>
'''
import numpy as np
from numpy.core.fromnumeric import nonzero

class _Node:
    def __init__(self, l=0, r=0, d=0) -> None:
        self.code  = 0
        self.depth = d
        self.left  = l
        self.right = r
    
    def __str__(self) -> str:
        return f"code: {self.code}, depth: {self.depth}, left: {self.left}"\
            f", right: {self.right}"


class DAT:
    BUF_SIZE = 16384
    UNIT_SIZE = 8

    def __init__(self) -> None:
        self._check = None
        self._base  = None
        self._used  = set()
        self._size  = 0
        
        self._key   = []
        # self._value = []
        self._v     = []
        self._error = 0

        # self._length       = []
        # self._allocSize    = 0
        self._nextCheckPos = 0
        self._progress     = 0  

    @property
    def size(self):
        return len(self._v)

    def build(self, keys, values):
        '''
        Invoke this method to build a DAT according to the
            given keys and values

        @parameters:
        keys: keys which are stored in this double-array-trie.
            Usually, keys is a list of strings
        values: values associated with keys. values is a list,
            whose element can be an object of any type you're
            interested in.

        @return:
            If failed, return a negative int value, or else 
                a zero value.
        '''
        assert keys and values and len(keys) == len(values),\
            "keys and values must not be empty and must have the same elements"
        self._key = keys
        self._v   = values
        self._resize(65536*32)
        self._base[0] = 1
        self._nextCheckPos = 0

        root = _Node(0, len(keys), 0)
        siblings = self._fetch_siblings(root)
        self._insert(siblings)
        self._used = None
        self._key  = None
        return self._error


    def _resize(self, size):
        b2 = np.zeros((size,), dtype=np.int32)
        c2 = np.zeros((size,), dtype=np.int32)
        if self._base:
            b2[:self._base.shape[0]] = self._base
            c2[:self._check.shape[0]] = self._check
        self._base  = b2
        self._check = c2


    def _fetch_siblings(self, p):
        if self._error < 0: return None
        siblings = []
        prev = 0
        for i in range(p.left, p.right):
            if len(self._key[i]) < p.depth:
                continue
            cur = ord(self._key[i][p.depth])+1 \
                if len(self._key[i]) != p.depth else 0
            
            # 
            if prev > cur:
                self._error = -3
                return None
            
            if cur != prev or not siblings:
                tmp = _Node(l=i, d=p.depth+1)
                tmp.code = cur
                if siblings:
                    siblings[-1].right = i
                siblings.append(tmp)

            prev = cur
        # end for
        if siblings:
            siblings[-1].right = p.right
        return siblings

    def _insert(self, siblings):
        if self._error < 0: return 0

        begin = 0
        nonzero_num = 0
        first = 0

        pos = max(siblings[0].code + 1, self._nextCheckPos) - 1

        if self._base.shape[0] <= pos:
            self._resize(pos + 2)

        while True:
            pos += 1
            if self._base.shape[0] <= pos:
                self._resize(pos + 1)
            
            if self._check[pos] != 0:
                nonzero_num += 1
                continue

            if first == 0:
                self._nextCheckPos = pos
                first = 1

            begin = pos - siblings[0].code
            if self._base.shape[0] <= (begin + siblings[-1].code):
                self._resize(begin + siblings[-1].code + (1<<16) - 1)
            if begin in self._used:
                continue

            for i in range(1, len(siblings)):
                if self._check[begin + siblings[i].code] != 0:
                    break   # exit for loop and reenter while loop
            else:
                break   # exit while loop
        
        if 1.0 * nonzero_num / (pos - self._nextCheckPos + 1) >= 0.95:
            self._nextCheckPos = pos

        self._used.add(begin)

        if self._size < begin + siblings[-1].code + 1:
            self._size = begin + siblings[-1].code + 1

        for s in siblings:
            self._check[begin + s.code] = begin

        for s in siblings:
            new_siblings = self._fetch_siblings(s)
            if new_siblings is None: return 0

            if len(new_siblings) == 0:  # leaf node
                self._base[begin + s.code] = -s.left - 1
                self._progress += 1
            else:
                h = self._insert(new_siblings)
                self._base[begin + s.code] = h
        return begin

    def prefix_match(self, key):
        '''
        get all items which are prefix-matched by key

        @parameters:
        key: a key string, used to prefix-match sth. in this trie

        @return:
        a list of all prefix-matched items' indices
        '''
        return self._prefix_match(self, key, 0, len(key), 0)

    def _prefix_match(self, key, start, length, node_pos):
        assert 0 <= start <= len(key)
        assert 0 <= node_pos < self._size

        end = start + length
        if start >= end or end > len(key):
            end = len(key)

        res = []
        b = self._base[node_pos]

        for i in range(start, end):
            p = b + ord(key[i]) + 1
            if p < self._size and b == self._check[p]:
                b = self._base[p]
            else:
                return res
            p = b
            n = self._base[p]
            if b == self._check[p] and n < 0:
                res.append(-n -1)
        return res

    def exact_match(self, key):
        '''
        Exactly match an item by a given key.

        @return:
        the index of exactly matched item in _v.
        '''
        return self._exact_match(key, 0, len(key), 0)

    def _exact_match(self, key, start, length, node_pos):
        assert 0 <= start <= len(key)
        assert 0 <= node_pos < self._size, \
            f'node_pos: {node_pos}, size: {self._size}'

        end = start + length
        if start >= end or end > len(key):
            end = len(key)

        p = 0
        b = self._base[node_pos]

        for i in range(start, end):
            p = b + ord(key[i]) + 1
            if p < self._size and b == self._check[p]:
                b = self._base[p]
            else:
                return -1

        p = b
        n = self._base[p]
        if b == self._check[p] and n < 0:
            return -n-1

        return -1

    def prefix_match_kv(self, key):
        return self._prefix_match_kv(key, 0, len(key), 0)

    def _prefix_match_kv(self, key, start, length, node_pos):
        '''
        prefix match, and return all prefix matched keys and
            its asscioated values
        '''
        assert 0 <= start <= len(key)
        assert 0 <= node_pos < self._size
        end = start + length
        if start >= end or end > len(key):
            end = len(key)

        res = []
        b = self._base[node_pos]

        for i in range(start, end):
            p = b
            n = self._base[p]
            if b == self._check[p] and n < 0:
                res.append((key[start:i], self._v[-n-1]))
            p = b + ord(key[i]) + 1
            if p < self._size and b == self._check[p]:
                b = self._base[p]
            else:
                return res
        
        p = b
        n = self._base[p]
        if b == self._check[p] and n < 0:
            res.append((key[start:end], self._v[-n-1]))
        return res

    def __getitem__(self, key):
        idx = self.exact_match(key)
        if idx >= 0:
            return self._v[idx]
        
        raise KeyError(f"key '{key}' does not exist")

    def get(self, key, default=None):
        idx = self.exact_match(key)
        if idx >= 0:
            return self._v[idx]
        return default

    def __setitem__(self, key, value):
        idx = self.exact_match(key)
        if idx >= 0:
            self._v[idx] = value
        raise KeyError(f"key '{key}' does not exist")

    def set(self, key, value):
        idx = self.exact_match(key)
        if idx >= 0:
            self._v[idx] = value
            return True
        return False

    
    def test(self):
        print(self._base[:50])
        print(self._check[:50])
        

