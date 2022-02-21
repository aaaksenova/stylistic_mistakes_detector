import detect
import streamlit as st
import pandas as pd
import os
import re


st.title('СберГлавред')
st.sidebar.subheader("Это инструмент для выявления стилистических ошибок в тексте")
st.sidebar.markdown('''<span style="color:green">Зеленым</span> цветом выделяются канцеляризмы и вводные слова \n''',
                    unsafe_allow_html=True)
with st.sidebar.expander('Пример'):
    st.sidebar.markdown('''<span style="color:green">В настоящее время</span> клиентам могут начисляться бонусы на заказы, 
    оплаченные наличными 
    => Сейчас вы получаете бонусы за каждый заказ, который оплатили наличными. \n''',
                        unsafe_allow_html=True)
st.sidebar.markdown('''<span style="color:blue">Синим</span> – пассивные конструкции \n''',
                    unsafe_allow_html=True)
with st.sidebar.expander('Пример'):
    st.sidebar.markdown('''В чате <span style="color:blue">предоставляется только справочная информация</span> по продуктам 
    и услугам банка => В чате мы даём только справочную информацию \n''',
                        unsafe_allow_html=True)
    st.sidebar.markdown('''<span style="color:blue">Открытие вклада осуществляется </span> только в офисе банка или с 
    помощью мобильного приложения => Открыть вклад вы можете самостоятельно — это легко сделать в приложении 
    СберБанк Онлайн. Или приходите в офис с паспортом — мои коллеги помогут! \n''',
                        unsafe_allow_html=True)
st.sidebar.markdown('''<span style="color:purple">Фиолетовым</span> – причастия и деепричастия \n''',
                    unsafe_allow_html=True)
with st.sidebar.expander('Пример'):
    st.sidebar.markdown('''<span style="color:purple">Делая</span> перевод по номеру телефона в СберБанк Онлайн, вы экономите 
    время, <span style="color:purple">принадлежащее</span> вам и получателю => Переводите деньги по номеру телефона — 
    это быстрее, чем заполнять номер карты \n''',
                        unsafe_allow_html=True)
st.sidebar.markdown('''<span style="color:red">Красным</span> – сложные глагольные конструкции \n''',
                    unsafe_allow_html=True)
with st.sidebar.expander('Пример'):
    st.sidebar.markdown('''<span style="color:red">Могу порекомендовать вам обратиться</span> в отделение банка и предъявить 
    документ, удостоверяющий личность, чтобы обновить ваши паспортные данные => Приходите в офис банка с паспортом, 
    мои коллеги обновят данные. \n''',
                        unsafe_allow_html=True)
st.sidebar.markdown('''<span style="color:orange">Оранжевым</span> – сложные конструкции существительных \n''',
                    unsafe_allow_html=True)
with st.expander('Пример'):
    st.sidebar.markdown('''Укажите <span style="color:orange">адрес офиса приобретения устройства</span> и данные сотрудника банка,
     осуществлявшего помощь в покупке => Укажите адрес офиса, где покупали SberBox. А ещё будет здорово, если вы вспомните 
     имя сотрудника, который помогал вам с покупкой. \n''',
                        unsafe_allow_html=True)
st.sidebar.markdown("**Важно! **"
                    "Цвета обозначают ошибки разного типа, но не показывают их критичность. ")
st.sidebar.markdown("С замечаниями и предложениями писать Анне Аксеновой *tg: aksenysh почта: aaleaksenova@sberbank.ru*")





@st.cache(suppress_st_warning=True)
def read_abbr_file():
    df_abbrs = pd.read_excel('abbreviations.xlsx', engine='openpyxl',)
    return df_abbrs


df_abbrs = read_abbr_file()


#@st.cache(suppress_st_warning=True)
def prepare_glavred_data():
    glavred_params = {}
    for file in os.listdir('./support_data'):
        glavred_params[file.split('.')[0]] = open(os.path.join('./support_data', file)).read().strip().split('\n')
        glavred_params[file.split('.')[0]] = {i.split(',')[0]: i.split(',')[1] for i in
                                              glavred_params[file.split('.')[0]]}
    return glavred_params


glavred_params = prepare_glavred_data()


with st.form(key='my_form'):
    text_to_check = st.text_area(label='Введите текст')
    run_processing = st.form_submit_button(label="Обработать")
if run_processing:
    if text_to_check:
        st.session_state['metrics'] = detect.complexity_analytics(text_to_check)
        bad_abbrs, replace_abbrs, text_to_check = detect.get_abbrs(text_to_check, df_abbrs)
        st.session_state['bad_abbrs'] = bad_abbrs
        st.session_state['replace_abbrs'] = replace_abbrs
        formatted = detect.format_text(text_to_check)
        differences = detect.detect_differences(text_to_check, formatted)
        formatted, st.session_state['flag_punct'] = detect.format_punct(formatted)
        passive_checked = detect.highlight_passive(formatted)
        bad_checked, detected_bad_words = detect.highlight_bad_words(passive_checked, glavred_params)
        st.session_state['bad_words'] = detected_bad_words
        particips = detect.highlight_part(bad_checked)
        verbs = detect.highlight_verbs(particips)
        st.session_state['output'] = detect.highlight_nouns(verbs)
        st.session_state['output'] = re.sub(r'(<span.+>.+?)<span.+?>(.+?)</span>(.+?</span>)', r'\1\2\3',
                                            st.session_state['output'])
        st.markdown('\n')
        st.markdown(st.session_state['output'], unsafe_allow_html=True)
        if st.session_state['metrics']:
            with st.expander('Открыть комментарии'):
                for metric in st.session_state['metrics']:
                    st.markdown(metric)
                if st.session_state['flag_punct']:
                    st.markdown('*Я убрал точку в конце*')
                if differences:
                    st.markdown('*Были исправлены опечатки:*')
                    for diff in differences:
                        st.markdown(f'*{diff}*')
                if st.session_state['bad_abbrs']:
                    if len(st.session_state['bad_abbrs']) > 1:
                        st.markdown('*Расшифруйте аббревиатуры: *' + ', '.join(st.session_state['bad_abbrs']))
                    else:
                        st.markdown('*Расшифруйте аббревиатуру: *' + st.session_state['bad_abbrs'][0])
                if st.session_state['replace_abbrs']:
                    st.markdown('*Замените: *')
                    for abbr in st.session_state['replace_abbrs'].keys():
                        st.markdown(abbr + ' на ' + st.session_state['replace_abbrs'][abbr])
                if st.session_state['bad_words']:
                    st.markdown('*Возможно, стоит заменить: *')
                    for suggestion in st.session_state['bad_words']:
                        st.markdown(suggestion.capitalize())
            st.session_state.clear()
    else:
        st.markdown("*Хм, сначала введите текст*")
