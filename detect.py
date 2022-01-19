from ruts import ReadabilityStats
import numpy as np
import re
import spacy
from pyaspeller import YandexSpeller
import difflib


speller = YandexSpeller()
model = spacy.load('ru_core_news_md')
# Словарь ненужных слов:
stop_words = """эквайринг, полученный, абсолютно, действительно, гарантированно, очень, необходимый, необходимо, \
самый, наиболее, являться, проинформировать, осуществляться, производить, осуществлять, производиться, надлежащий, \
данный, соответствующий, всесторонний, выполнять, дальнейший, значительный, изложенный, какой-либо, \
максимально, совершение, совершить, произвести, надлежащий, данное, списание, оказание, реальный, наиболее, \
немаловажный, немаловажно, обеспечить, обеспечивать, подвергаться, подвергнуться, позволять, соответственно, \
функционировать, каковой, вышеуказанный, вышеупомянутый"""

stop_phrases = """не требуется, ввиду, на предмет, в качестве, \
в целях, в настоящее время, в рамках, во избежание, в связи, по причине, в случае, таким образом, \
на протяжении, на текущий момент, в должной мере, по прошествии"""

stop_words = stop_words.split(', ')
stop_words = {word: ' '.join([w.lemma_ for w in model(word)]) for word in stop_words}


def complexity_analytics(text):
    """
    The function calculates readability metrics for given text
    and aggregates flesch_kincaid_grade and automated_readability_index
    comparing their mean to 10
    :param text: str
    :return: list
    """
    standard_values = {'flesch_kincaid_grade': 10,
                       'flesch_reading_easy': 47.30264705882351,
                       'coleman_liau_index': 9.27248529411765,
                       'smog_index': 12.553279569776885,
                       'automated_readability_index': 10,
                       'lix': 10}
    rs = ReadabilityStats(text)
    real_values = rs.get_stats()

    real_values['flesch_reading_easy'] = -real_values['flesch_reading_easy']
    delta = (real_values['flesch_kincaid_grade'] + real_values['automated_readability_index']) / 2 - \
            (standard_values['flesch_kincaid_grade'] + standard_values['automated_readability_index']) / 2
    sent_lens = max([len(sent.split()) for sent in text.split('. ')])
    warn_text = []
    if delta > 1:
        warn_text.append('*Текст перегружен.*')
    else:
        warn_text.append('*Все метрики соблюдены.*')
    if sent_lens > 15:
        warn_text.append('*Предложения длинее 15 слов лучше разбивать на более короткие.*')
    return warn_text


def format_text(text):
    """
    The function is responsible for text formatting
    it works with:
    - whitespaces before %
    - dashes between words
    - lower and upper case
    - dot in the end of the text
    :param text: str
    :return: str, bool
    """
    text = speller.spelled(text)  # Исправляем орфографию
    you_list = ['Вы', 'Вас', 'Вам', 'Вами']
    for i in you_list:  # Меняем Вы на нижний регистр
        text = re.sub(r'([^\.!\?] )\b{}\b'.format(i), r'\1{}'.format(i.lower()), text)
    text = re.sub(r'Ваш', r'ваш', text)  # Меняем Ваш на нижний регистр
    return text


def format_punct(text):
    text = re.sub(' %', '%', text)  # Убираем пробел перед %
    text = re.sub(r'[\'\"„](.+?)[\'\"“]', r'«\1»', text, flags=re.DOTALL)  # Приводим кавычки к одному виду
    text = re.sub('\b - \b', '\b — \b', text)  # Выравниваем тире и добавляем неразрывный пробел
    text = re.sub(r'№(\d)', r'№ \1', text)  # После номера, но перед числом пробел
    text = re.sub(r'(\d)( *?Р\.*)|( *?[рР]уб\.*)', r'\1 ₽', text)  # Приводим разные написания рубля к одному виду
    text = re.sub(r'(\d{2})/(\d{2})/(\d{4})', r'\1\.\2\.\3', text)  # Форматируем даты
    text_new = text.strip('.')
    flag_punct = 0
    if text_new != text:
        flag_punct = 1
    return text_new, flag_punct


def highlight_bad_words(text):
    """
    The function highlights words stylistically inappropriate
    for the given text based on word dictionary
    :param text: str
    :return: str
    """
    sents = text.split('.')
    detected = []
    for sent in sents:
        doc = model(sent)
        for w in doc:
            if w.lemma_ in stop_words.keys() and w.text not in detected:
                detected.append(w.text)
                text = re.sub(w.text, '''<span style="color:green">''' + w.text + '</span>', text)
    for stop_phrase in stop_phrases.split(', '):
        text = re.sub(stop_phrase, '''<span style="color:green">''' + stop_phrase + '</span>', text)
        text = re.sub(stop_phrase.capitalize(), \
                      '''<span style="color:green">''' + stop_phrase.capitalize() + '</span>', text)
    return text


def checkForSentType(inputSentence):
    """
    The function detects passive constuction subjects in the given text
    and creates patterns with the closest verb
    :param inputSentence: str
    :return: list
    """

    # running the model on sentence
    getDocFile = model(inputSentence.strip())

    # getting the syntactic dependency
    getPassTags = [token.text
                   for token in getDocFile if token.dep_ == 'nsubj:pass']
    if getPassTags:
        getPassIdx = [idx
                      for idx, token in enumerate(getDocFile) if token.dep_ == 'nsubj:pass']
        getVerbIdx = [idx
                      for idx, token in enumerate(getDocFile) if token.pos_ == 'VERB']
        patterns = []
        for i in getPassIdx:
            deltas = abs(np.array(getVerbIdx) - i)
            min_idx = deltas.argmin()
            pass_verb = getDocFile[getVerbIdx[min_idx]].text
            if getVerbIdx[min_idx] > i:
                pattern = getDocFile[i].text + '.+' + pass_verb
            elif getVerbIdx[min_idx] < i:
                pattern = pass_verb + '.+' + getDocFile[i].text
            patterns.append(pattern)
        return patterns
    else:
        return ''


def highlight_passive(text):
    """
    The function highlights passive patterns found by checkForSentType()
    :param text: str
    :return: str
    """
    sentences = text.split('. ')
    text_upd = []
    # checking each sentence for its type
    for sentence in sentences:
        patterns = checkForSentType(str(re.sub(r'<.+?>', r'', sentence)))
        sentence_upd = sentence
        if patterns:
            for pattern in patterns:
                sentence_upd = re.sub(r'(' + pattern + r')', r'start\1stop', sentence_upd)  # \\034[34m # \\034[0m
        text_upd.append(sentence_upd)
    text = '. '.join(text_upd)
    text = text.replace('start', '''<span style="color:blue">''').replace('stop', '</span>')
    return text


def highlight_verbs(text):
    """
    The function detects and highlights constructions
    with 3 and more verbs in a row
    :param text: str
    :return: str
    """
    sentences = text.split('. ')
    text_upd = []
    for sentence in sentences:
        sentence_upd = sentence
        doc = model(sentence)
        verb_patterns = []
        curr_pattern = []
        for tok_idx in range(len(doc)):
            if doc[tok_idx].pos_ == 'VERB' and doc[tok_idx].text.isalpha():
                curr_pattern.append(tok_idx)
            else:
                if len(curr_pattern) >= 3:
                    verb_patterns.append(doc[curr_pattern[0]].text + '.+' + doc[curr_pattern[-1]].text)
                curr_pattern = []
        if len(curr_pattern) >= 3:
            verb_patterns.append(doc[curr_pattern[0]].text + '.+' + doc[curr_pattern[-1]].text)
        if verb_patterns:
            for pattern in verb_patterns:
                sentence_upd = re.sub(r'(' + pattern + r')', r'START\1STOP', sentence_upd)  # \\034[34m # \\034[0m
        text_upd.append(sentence_upd)
    text = '. '.join(text_upd)
    text = text.replace('START', '''<span style="color:red;">''').replace('STOP', '</span>')
    return text


def highlight_nouns(text):
    """
    The function detects and highlights constructions
    with 3 and more nouns in a row
    and conditioning nominal constructions like 'при зачислении'
    :param text: str
    :return: str
    """
    sentences = text.split('. ')
    text_upd = []
    for sentence in sentences:
        sentence_upd = sentence
        doc = model(sentence)
        noun_patterns = []
        curr_pattern = []
        for tok_idx in range(len(doc)):
            if doc[tok_idx].pos_ == 'NOUN' and doc[tok_idx].text.isalpha():
                curr_pattern.append(tok_idx)
            else:
                if len(curr_pattern) >= 3:
                    noun_patterns.append(' '.join([doc[curr_pattern[i]].text for i in range(len(curr_pattern))]))
                curr_pattern = []
        if len(curr_pattern) >= 3:
            noun_patterns.append(doc[curr_pattern[0]].text + '.+' + doc[curr_pattern[-1]].text)
        if noun_patterns:
            for pattern in noun_patterns:
                sentence_upd = re.sub(r'(' + pattern + r')', r'START\1STOP', sentence_upd)  # \\034[34m # \\034[0m
        text_upd.append(sentence_upd)
    text = '. '.join(text_upd)
    text = text.replace('START', '''<span style="color:orange;">''').replace('STOP', '</span>')
    text = re.sub(r'(' + r'[Пп]ри \w+[ит]и\b' + r')', r'START\1STOP', text)
    text = text.replace('START', '''<span style="color:orange;">''').replace('STOP', '</span>')
    return text


def highlight_part(text):
    """
    The function detects and highlights participles and converbs
    :param text: str
    :return: str
    """
    sentences = text.split('. ')
    particip_patterns = []
    text_upd = []
    for sentence in sentences:
        sentence_upd = sentence
        doc = model(sentence)
        for token in doc:
            if token.morph.get("VerbForm"):
                if token.morph.get("VerbForm")[0] in ['Part', 'Conv'] and token.dep_ in ['acl', 'advcl']:
                    particip_patterns.append(token.text)
        particip_patterns = list(set(particip_patterns))
        if particip_patterns:
            for pattern in particip_patterns:
                sentence_upd = re.sub(r'(' + pattern + r')', r'start\1stop', sentence_upd)  # \\034[34m # \\034[0m
        text_upd.append(sentence_upd)
    text = '. '.join(text_upd)
    text = text.replace('start', '''<span style="color:Purple;">''').replace('stop', '</span>')
    return text


def get_abbrs(text, df_abbrs):
    """
    The function extracts abbreviations unknown for customers
    :param text: str, df_abbrs: DataFrame
    :return: list
    """
    abbrs = re.findall(r'\b[А-Я][А-Я]+\b', text)
    if abbrs:
        bad_abbrs = []
        replce_abbrs = {}
        abbrs = list(set(abbrs))
        for abbr in abbrs:
            a_class = df_abbrs[df_abbrs['abbreviation'] == abbr]
            if a_class.abbr_class.values.size > 0:
                a_class = a_class.abbr_class.values[0]
                if a_class == 1:
                    bad_abbrs.append(abbr)
                elif a_class == 'замена':
                    replce_abbrs[abbr] = df_abbrs[df_abbrs['abbreviation'] == abbr]['replace'].values[0]
                elif a_class == 'капс':
                    text = re.sub(r'\b{}\b'.format(abbr), abbr.lower(), text)
            else:
                bad_abbrs.append(abbr)
        return bad_abbrs, replce_abbrs, text
    else:
        return '', '', text


def detect_differences(text1, text2):
    txt1_list = text1.split()
    txt2_list = text2.split()

    diff = difflib.unified_diff(txt1_list, txt2_list)
    text_with_diff = '###'.join(diff) + '###'
    before = re.findall(r'###-(.+?)###', text_with_diff)
    after = re.findall(r'###\+(.+?)###', text_with_diff)
    collected_differences = []
    if before:
        for i, j in zip(before, after):
            if i+' → '+j not in collected_differences:
                collected_differences.append(i+' → '+j)
        return collected_differences
    else:
        return ''
