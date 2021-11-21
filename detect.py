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
stop_words = """эквайринг, абсолютно, действительно, гарантированно, очень, \
самый, наиболее, являться, осуществляться, производиться, надлежащий, данный, \
максимально, совершение, совершить, произвести, надлежащий, данное, проинформировать"""
stop_phrases = """денежные средства, провести соответствующее мероприятие, не требуется, на предмет взаимодействия, \
в целях, в настоящее время, в рамках, во избежание, в связи, по причине, в случае"""
stop_words = stop_words.split(', ')
stop_words = {word: ' '.join([w.lemma_ for w in model(word)]) for word in stop_words}


def complexity_analytics(text):
    standard_values = {'flesch_kincaid_grade': 5.610294117647054,
                       'flesch_reading_easy': 47.30264705882351,
                       'coleman_liau_index': 9.27248529411765,
                       'smog_index': 12.553279569776885,
                       'automated_readability_index': 9.27248529411765,
                       'lix': 55.55882352941177}
    rs = ReadabilityStats(text)
    real_values = rs.get_stats()
    real_values['flesch_reading_easy'] = -real_values['flesch_reading_easy']
    warnings = []
    for metric in real_values.keys():
        if real_values[metric] > standard_values[metric] + 1:
            warnings.append((metric, real_values[metric] - standard_values[metric]))
    if warnings:
        warn_text = []
        for metric, value in warnings:
            warn_text.append("**" + metric.capitalize() + "** на " + str(round(value)) + " больше нормального значения")
    else:
        warn_text = ['Все метрики соблюдены']
    return warn_text


def format_text(text):
    text = re.sub(' %', '%', text)  # убираем пробел перед %
    text = re.sub(r'[\'\"„](.+?)[\'\"“]', r'«\1»', text, flags=re.DOTALL)  # Приводим кавычки к одному виду
    spell_checked = speller.spelled(text)  # Исправляем орфографию
    # final = extractor.replace_groups(spell_checked)  # Меняем числа словами на цифры
    return spell_checked


def highlight_bad_words(text):
    sents = text.split('.')
    for sent in sents:
        doc = model(sent)
        for w in doc:
            if w.lemma_ in stop_words.keys():
                text = re.sub(w.text, '''<span style="color:green"> ''' + w.text + '</span>', text)
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
    sentences = text.split('.')

    # checking each sentence for its type
    for sentence in sentences:
        patterns = checkForSentType(str(sentence))
        if patterns:
            for pattern in patterns:
                text = re.sub(r'(' + pattern + r')', r'start \1stop', text)  # \\034[34m # \\034[0m
        text = text.replace('start', '''<span style="color:blue"> ''').replace('stop', '</span>')
    return text


def highlight_part(text):
    sentences = text.split('.')

    particip_patterns = []
    for sentence in sentences:
        doc = model(sentence)
        for token in doc:
            if token.morph.get("VerbForm"):
                if token.morph.get("VerbForm")[0] in ['Part', 'Conv'] and token.dep_ in ['acl', 'advcl']:
                    particip_patterns.append(token.text)
        if particip_patterns:
            for pattern in particip_patterns:
                text = re.sub(r'(' + pattern + r')', r'start \1stop', text)  # \\034[34m # \\034[0m
        text = text.replace('start', '''<span style="color:Purple;"> ''').replace('stop', '</span>')
    return text
