import json
import sys
import random

dictionary_file = "dictionary.json"


def lang_name(lang: str) -> str:
    langs_dict = {"en": "english", "sp": "spanish", "ru": "russian"}
    return langs_dict[lang]


def get_langs(pair:str) -> list:
    l0, l1 = pair.split('_')
    lang0 = [f"{l0}_{l1}", lang_name(l0), lang_name(l1)]
    lang1 = [f"{l1}_{l0}", lang_name(l1), lang_name(l0)]
    return [lang0, lang1]


def get_dict(pair:str) -> dict:
    global dictionary_file
    with open(dictionary_file, encoding='utf8') as f:
        words = json.loads(f.read())["dictionary"]
    print("Number of words:")
    for l in words:
        print(f"\t{l}: {len(words[l])}")
    langs = get_langs(pair)
    dicts = {langs[0][0]: [], langs[1][0]: []}

    for l in langs:
        for word in words[l[1]]:
            if l[2] in words[l[1]][word]:
                for tr in words[l[1]][word][l[2]]:
                    w = words[l[1]][word][l[2]][tr]
                    dicts[l[0]].append([word, tr, w])
    return dicts


def save_dict(dicts: dict):
    # dicts = {"en_sp": [["hello", "hola", 0], ...], "sp_en": [["hola", "hello", 0]]}
    global dictionary_file
    with open(dictionary_file, encoding='utf8') as f:
        words = json.loads(f.read())
    for d in dicts:
        main_lang = lang_name(d.split('_')[0])
        sec_lang = lang_name(d.split('_')[1])
        for w in dicts[d]:
            if w[0] in words["dictionary"][main_lang]:
                if sec_lang in words["dictionary"][main_lang][w[0]]:
                    words["dictionary"][main_lang][w[0]][sec_lang][w[1]] = w[2]
                else:
                    words["dictionary"][main_lang][w[0]][sec_lang] = {}
                    words["dictionary"][main_lang][w[0]][sec_lang][w[1]] = w[2]
            else:
                words["dictionary"][main_lang][w[0]] = {sec_lang: {w[1]: w[2]}}
    text = json.dumps(words, sort_keys = True, ensure_ascii=False, indent=4)
    with open(dictionary_file, 'w', encoding='utf8') as f:
        f.write(text)


def add_node(nodes: list, node: list):
    for n in nodes:
        if n[0] == node[0] and n[1] == node[1]:
            return
    nodes.append(node)


def add_nodes(dicts: dict, words: dict, lang0, lang1):
    pair = f"{lang0}_{lang1}"
    for w0 in words[lang0]:
        for w1 in words[lang1]:
            if pair not in dicts:
                dicts[pair] = []
            add_node(dicts[pair], [w0, w1, 0])


def add_translation(dicts: dict, graph: str):
    example = "en: leaf, sheet; sp: la hoja; ru: лист"
    a = graph.split(';')
    words = {}
    for i in range(len(a)):
        l = []
        lang = a[i].split(':')[0].strip()
        trs = a[i].split(':')[1]
        for w in trs.split(','):
            l.append(w.strip())
        words[lang] = l

    langs = list(words.keys())
    if len(langs) < 2:
        print(f"Error: incorrect request. Try like this: {example}")
        return
    if len(langs) == 2:
        add_nodes(dicts, words, langs[0], langs[1])
        add_nodes(dicts, words, langs[1], langs[0])
    elif len(langs) == 3:
        add_nodes(dicts, words, langs[0], langs[1])
        add_nodes(dicts, words, langs[1], langs[0])

        add_nodes(dicts, words, langs[0], langs[2])
        add_nodes(dicts, words, langs[2], langs[0])

        add_nodes(dicts, words, langs[1], langs[2])
        add_nodes(dicts, words, langs[2], langs[1])
    save_dict(dicts)


def translations(word: str, dicts: list):
    trxs = []
    for a in dicts:
        if a[0] == word:
            trxs.append(a[1])
    return trxs


def wait_for_answer(dicts: dict, word: list, possible_translations: list[str], counter: int, tries: int):
    if tries >= len(possible_translations):
        print(f"Incorrect! Expected answer is: {word[1]}")
        word[2] -= 1
        return 0
    print(f"{counter}/256 {word[0]}: ", end='', flush=True)
    user_input = input()
    if user_input[:6] == "--exit" or user_input[:6] == "--quit":
        return -1
    elif user_input[:5] == "--add":
        add_translation(dicts, user_input[5:])
        return wait_for_answer(dicts, word, possible_translations, counter, tries)
    else:
        if user_input == word[1]:
            print("Correct!")
            word[2] += 1
        elif user_input in possible_translations:
            print(f"Correct, but there is other translation, try again")
            return wait_for_answer(dicts, word, possible_translations, counter, tries+1)
        else:
            print(f"Incorrect! Correct answer is: {' or '.join(possible_translations)}")
            word[2] -= 1
        return 0


def prepare_dict(words: list) -> list:
    make_random = False
    if make_random:
        random.shuffle(words)
        return words
    else:
        return sorted(words, key=lambda x: x[2])



def poll(dicts: dict):
    print("Polling")
    for i in range(0, 256, 2):
        langs = list(dicts.keys())
        dicts[langs[0]] = prepare_dict(dicts[langs[0]])
        if -1 == wait_for_answer(dicts, dicts[langs[0]][0], translations(dicts[langs[0]][0][0], dicts[langs[0]]), i, 0):
            return
        save_dict(dicts)
        dicts[langs[1]] = prepare_dict(dicts[langs[1]])
        if -1 == wait_for_answer(dicts, dicts[langs[1]][0], translations(dicts[langs[1]][0][0], dicts[langs[1]]), i+1, 0):
            return
        save_dict(dicts)


def main(dict_file: str, pair: str):
    dicts = get_dict(pair)
    poll(dicts)


if __name__ == "__main__":
    help_string = "Set which pair you want to train: en_sp, en_ru, sp_ru"
    if len(sys.argv) == 1:
        print(help_string)
    elif len(sys.argv) == 2:
        if sys.argv[1] in ["en_sp", "en_ru", "sp_ru"]:
            main(dictionary_file, sys.argv[1])
        else:
            print(f"Incorrect argument: {sys.argv[1]}. {help_string}")
    else:
        print(f"Too many arguments. {help_string}")