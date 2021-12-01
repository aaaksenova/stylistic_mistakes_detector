from ruts import ReadabilityStats
import numpy as np
import re
import spacy
from pyaspeller import YandexSpeller

# from extractor import NumberExtractor

speller = YandexSpeller()
# extractor = NumberExtractor()
model = spacy.load('ru_core_news_md')

# Словарь сложных слов:
stop_words = """эквайринг, полученный, абсолютно, действительно, гарантированно, очень, необходимо, необходимый, \
самый, наиболее, являться, осуществляться, производить, осуществлять, производиться, надлежащий, данный, соответствующий, \
максимально, совершение, совершить, произвести, надлежащий, данное, списание, оказание, реальный"""
stop_phrases = """не требуется, на предмет, \
в целях, в настоящее время, в рамках, во избежание, в связи, по причине, в случае, таким образом, на текущий момент"""
stop_words = stop_words.split(', ')
stop_words = {word: ' '.join([w.lemma_ for w in model(word)]) for word in stop_words}


def complexity_analytics(text):
    standard_values = {'flesch_kincaid_grade': 10,
                       'flesch_reading_easy': 47.30264705882351,
                       'coleman_liau_index': 9.27248529411765,
                       'smog_index': 12.553279569776885,
                       'automated_readability_index': 10,
                       'lix': 10}
    rs = ReadabilityStats(text)
    real_values = rs.get_stats()
    real_values['flesch_reading_easy'] = -real_values['flesch_reading_easy']
    # warnings = []
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
    # for metric in real_values.keys():
    #     if real_values[metric] > standard_values[metric] + 1:
    #         warnings.append((metric, real_values[metric] - standard_values[metric]))
    # if warnings:
    #     warn_text = []
    #     for metric, value in warnings:
    #         warn_text.append("**" + metric.capitalize() + "** на " + str(round(value)) + " больше нормального значения")

    return warn_text


def format_text(text):
    text = re.sub(' %', '%', text)  # Убираем пробел перед %
    text = re.sub(r'[\'\"„](.+?)[\'\"“]', r'«\1»', text, flags=re.DOTALL)  # Приводим кавычки к одному виду
    text = re.sub(' - это', ' – это', text)  # Выравниваем тире
    text = speller.spelled(text)  # Исправляем орфографию
    you_list = ['Вы', 'Вас', 'Вам', 'Вами'] #'Ваш', 'Вашего','Вашему', 'Вашем', 'Ваше', 'Вашим', 'Ваша', 'Вашей', 'Вашу']
    for i in you_list:  # Меняем Вы на нижний регистр
        text = re.sub(r'\b{}\b'.format(i), r'\b{}\b'.format(i.lower()), text)
    text = re.sub(r'Ваш', r'ваш', text) # Меняем Ваш на нижний регистр
    #text = re.sub(r'вашин', r'Вашин', text)
    # final = extractor.replace_groups(spell_checked)  # Меняем числа словами на цифры
    return text


def highlight_bad_words(text):
    sents = text.split('.')
    for sent in sents:
        doc = model(sent)
        for w in doc:
            if w.lemma_ in stop_words.keys():
                text = re.sub(w.text, '''<span class="words" style="color:green">''' + w.text + '</span>', text)
    for stop_phrase in stop_phrases.split(', '):
        text = re.sub(stop_phrase, '''<span class="words" style="color:green">''' + stop_phrase + '</span>', text)
        text = re.sub(stop_phrase.capitalize(), \
                      '''<span class="words" style="color:green">''' + stop_phrase.capitalize() + '</span>', text)
    return text


# function to check the type of sentence
def checkForSentType(inputSentence):
    # running the model on sentence
    getDocFile = model(inputSentence.strip())

    # getting the syntactic dependency
    getPassTags = [token.text
                   for token in getDocFile if token.dep_ == 'nsubj:pass'
                   ]
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
    sentences = text.split('. ')
    text_upd = []
    # checking each sentence for its type
    for sentence in sentences:
        patterns = checkForSentType(str(sentence))
        sentence_upd = sentence
        if patterns:
            for pattern in patterns:
                sentence_upd = re.sub(r'(' + pattern + r')', r'start\1stop', sentence_upd)  # \\034[34m # \\034[0m
        text_upd.append(sentence_upd)
        text = '. '.join(text_upd)
        text = text.replace('start', '''<span style="color:blue">''').replace('stop', '</span>')
    return text


def highlight_verbs(text):
    sentences = text.split('. ')

    text_upd = []
    for sentence in sentences:
        sentence_upd = sentence
        doc = model(sentence)
        verb_patterns = []
        curr_pattern = []
        for tok_idx in range(len(doc)):
            if doc[tok_idx].pos_ == 'VERB':
                curr_pattern.append(tok_idx)
            else:
                if len(curr_pattern) >= 3:
                    verb_patterns.append(doc[curr_pattern[0]].text + '.+' + doc[curr_pattern[-1]].text)
                curr_pattern = []
        if verb_patterns:
            for pattern in verb_patterns:
                sentence_upd = re.sub(r'(' + pattern + r')', r'START\1STOP', sentence_upd)  # \\034[34m # \\034[0m
        text_upd.append(sentence_upd)
        text = '. '.join(text_upd)
        text = text.replace('START', '''<span style="color:red;">''').replace('STOP', '</span>')
    return text


def highlight_part(text):
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
