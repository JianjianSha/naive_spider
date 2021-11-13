from ..basic.trie import DAT
from ..basic.tree import Tree
from pypinyin import lazy_pinyin, pinyin, Style
import jieba
import re


def roma_py(area):
    py = ''.join(l[0] for l in pinyin(area, style=Style.TONE2))
    py = tone2roma(py)
    return py


def tone2roma(tone):
    d = {
        'a3': 'aa',
        'a4': 'ah',
        'u4': 'uh',
        'i2': 'yi',
        'u2': 'wu',
        'u3': 'uu'
    }
    def _deal(m):
        r = m.group()
        if r in d:
            return d[r]
        else:
            return r[:1]

    return re.sub('[a-z]\d', _deal, tone)


class AreaTreeKey:
    def __init__(self, code, name, py) -> None:
        self.code = code
        self.name = name
        self.py = py


class Area2:
    def __init__(self, file='naive_spider/data/areas.pkl'):
        self.tree = Tree()



class Area:
    def __init__(self, file='naive_spider/data/areas.pkl') -> None:
        name2code = {}
        code2name = {}
        self.py2name_ = {}
        with open(file, 'r') as f:
            for line in f.readlines():
                if line.strip():
                    code, name = line.strip().split(' ')
                    code2name[code] = name
                    codes_ = name2code.get(name, [])
                    codes_.append(code)
                    if len(code) <= 4:
                        
                        py = roma_py(name)
                        if py in self.py2name_:
                            old_name = self.py2name_[py]
                            if name != old_name:
                                assert py not in self.py2name_, f"{name} and "\
                                    f"{self.py2name_[py]} has the same pinyin"
                        else:
                            self.py2name_[py] = name
                    if name not in name2code:
                        name2code[name] = codes_
        self.name2code_ = DAT()
        sorted_d = [(k, name2code[k]) for k in sorted(name2code.keys())]

        self.name2code_.build([t[0] for t in sorted_d], [t[1] for t in sorted_d])
        self.code2name_ = DAT()
        sorted_d = [(k, code2name[k]) for k in sorted(code2name.keys())]
        self.code2name_.build([t[0] for t in sorted_d], [t[1] for t in sorted_d])

    def code2name(self, code):
        return self.code2name_.get(code)

    def name2code(self, name):
        return self.name2code_.get(name)

    def py2name(self, py, level=0):
        '''only for province and city, not for county'''
        name = self.py2name_.get(py)
        if name is None:
            if not py.endswith('sheng'):
                name = self.py2name_.get(py+'sheng')
            else:
                name = self.py2name_.get(py[:-5])
        return name

    def guess_city(self, text, ns):
        if not text: return None
        words = list(jieba.cut(text))
        if words and len(words[0]) > 1:
            name = words[0]
        elif len(words) > 1 and len(words[1]) == 1:
            name = words[0] + words[1]
        else:
            return None
        if name[-1] in '县市' or len(name) > 3:
            return self.city(name, ns)
        else:
            city = self.city(name+'市', ns)
            if not city:
                city = self.city(name+'县', ns)
            return city

    def city(self, name, ns):
        '''
        @parameters:
        name: area name
        ns: namespace, which usually is the province,
            and you can use the form of zh or py
        
        @return:
        return the city name
        '''
        assert ns, "the province which used as namespace to "\
            "avoid of any indistince area name must be provided"

        # py to zh
        if all(ord(c) < 128 for c in ns):
            ns = self.py2name(ns)
        codes_ = self.name2code(ns)
        if codes_ is None or len(codes_) > 1:
            raise ValueError(
                f"parameter `ns`({ns}) is not py or zh of a province")
        province_code = codes_[0]

        ts = self.name2code_.prefix_match_kv(name)
        if not ts: 
            return None

        best_match = None
        
        for t in ts:
            codes_ = t[1]
            if not codes_: continue

            for code in codes_:
                if len(code) < 4 or not code.startswith(province_code):
                    continue

                if best_match is None or len(best_match[0]) < len(t[0]):
                    best_match = (t[0], code)
        if best_match:
            if len(best_match[1]) == 4:
                return best_match[0]
            return self.code2name(best_match[1][:4])
        return None


area = Area()        

def test():
    text = '青县科技工信和商务局'
    at = Area()
    print('input:', text)
    print('analyzed city:', at.guess_city(text, 'hebei'))
    
