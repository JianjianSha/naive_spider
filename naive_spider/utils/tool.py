from colorama import init, Fore, Back, Style
import random
import re
import hashlib


COLORS = ['cyan', 'yellow', 'blue', 'magenta', 'green', 'red',
          'lightblue', 'lightyellow', 'lightcyan', 'lightgreen',
          'lightmagenta', 'lightred']

# color print
def cprint(*o, color=None):
    if color is None:
        color = random.choice(COLORS)
    elif color not in COLORS:
        color = COLORS[hash(color) % len(COLORS)]
    suf = Fore.RESET
    if color == 'red':
        pre = Fore.RED
    elif color == 'cyan':
        pre = Fore.CYAN
    elif color == 'yellow':
        pre = Fore.YELLOW
    elif color == 'blue':
        pre = Fore.BLUE
    elif color == 'magenta':
        pre = Fore.MAGENTA
    elif color == 'green':
        pre = Fore.GREEN
    # elif color == 'white':
    #     pre = Fore.WHITE
    elif color == 'lightblue':
        pre = Fore.LIGHTBLUE_EX
    elif color == 'lightyellow':
        pre = Fore.LIGHTYELLOW_EX
    elif color == 'lightcyan':
        pre = Fore.LIGHTCYAN_EX
    elif color == 'lightgreen':
        pre = Fore.LIGHTGREEN_EX
    elif color == 'lightmagenta':
        pre = Fore.LIGHTMAGENTA_EX
    elif color == 'lightred':
        pre = Fore.LIGHTRED_EX
    else:
        pre = ''
        suf = ''
    o = ' '.join(str(i) for i in o)
    print(f'{pre}{o}{suf}')

def green_print(*args):
    cprint(*args, color='green')


def parse_time_from_text(text):
    m = re.search('\d{4}[./-]\d{2}[./-]?\d{2}', text)
    if m:
        text = m.group().replace('/', '-')
        if len(text) == 9:
            text = text[:7] + '-' +text[7:]
        if re.match('^\d{4}-\d{2}-\d{2}$', text):
            segs = text.split('-')
            if 1900 < int(segs[0]) < 3000 and 0 < int(segs[1]) < 13 and 0 < int(segs[2]) < 32:
                return text
    else:
        m = re.search('\d{4}[/-]\d{2}', text)
        if m:
            text = m.group().replace('/', '-')
            text += '-01'
            if re.match('^\d{4}-\d{2}-\d{2}$', text):
                segs = text.split('-')
                if 1900 < int(segs[0]) < 3000 and 0 < int(segs[1]) < 13 and 0 < int(segs[2]) < 32:
                    return text
    return None


def md5_16(text):
    return md5(text)[:16]

    
def md5(text):
    return hashlib.md5(bytes(text, encoding='utf8')).hexdigest()