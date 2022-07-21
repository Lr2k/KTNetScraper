import unicodedata

def len_sepa(string):
    # 半角を1、全角を2として文字列の長さをカウントする。
    string = str(string)

    len_list = list()
    for letter in string:
        
        letter_type = unicodedata.east_asian_width(letter)
        if letter_type in 'FWA':
            len_list.append(2)
        else:
            len_list.append(1)
    
    return len_list

# 半角を1文字、全角を2文字としてカウントする
def len_zen2(string):
    len_list = len_sepa(string)

    length = 0
    for i in len_list:
        length += i
    
    return length

# emmbeding_letter=' ' : 左詰めであいた右側を埋めるのに使う文字
def ljust_zen(word_count, string, emmbeding_letter=' '):
    string = str(string)
    len_list = len_sepa(string)

    # 何文字目まで残せるかカウントする
    length = 0
    for i in range(len(len_list)):
        # あと何文字埋められるかカウント
        if word_count - (length+len_list[i]) > -1:
            length += len_list[i]
            i += 1
        else:
            break

    left_letters = string[0:length]
    
    letters = left_letters + str(emmbeding_letter)*(word_count-length)

    return letters

def rjust_zen(string, word_count, emmbeding_letter=' '):
    len_list = len_sepa(string)

    # 何文字目まで残せるかカウントする
    length = 0
    for i in range(len(len_list)):
        # あと何文字埋められるかカウント
        if word_count- (length+len_list[i]) > -1:
            length += len_list[i]
            i += 1
        else:
            break
    left_letters = string[0:i]
    
    letters = str(emmbeding_letter)*(word_count-length) + left_letters

    return letters