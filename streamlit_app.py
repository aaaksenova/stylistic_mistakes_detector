import detect
import streamlit as st
import pandas as pd


st.title('Главред для НРМ')
st.sidebar.subheader("Это инструмент для выявления стилистических ошибок в тексте")
st.sidebar.markdown('''<span style="color:green">Таким</span> цветом выделяются канцеляризмы и вводные слова \n''',
                    unsafe_allow_html=True)
st.sidebar.markdown('''<span style="color:blue">Таким</span> – пассивные конструкции \n''',
                    unsafe_allow_html=True)
st.sidebar.markdown('''<span style="color:purple">Таким</span> – причастия и деепричастия \n''',
                    unsafe_allow_html=True)
st.sidebar.markdown('''<span style="color:red">Таким</span> – сложные глагольные конструкции \n''',
                    unsafe_allow_html=True)
st.sidebar.markdown('''<span style="color:orange">Таким</span> – сложные конструкции существительных \n''',
                    unsafe_allow_html=True)
st.sidebar.markdown("**Важно!** Этот инструмент лишь подсказывает возможные ошибки, но не гарантирует их наличие.")
st.sidebar.markdown("С замечаниями и предложениями писать Анне Аксеновой *tg: aksenysh*")


@st.cache(suppress_st_warning=True)
def read_abbr_file():
    df_abbrs = pd.read_excel('abbreviations.xlsx', engine='openpyxl',)
    return df_abbrs


df_abbrs = read_abbr_file()


with st.form(key='my_form'):
    text_to_check = st.text_area(label='Введите текст')
    run_processing = st.form_submit_button(label="Обработать")
if run_processing:
    if not text_to_check:
        st.session_state['output'] = '*Хм, сначала введите текст*'
    else:
        st.session_state['metrics'] = detect.complexity_analytics(text_to_check)
        bad_abbrs, replace_abbrs, text_to_check = detect.get_abbrs(text_to_check, df_abbrs)
        st.session_state['bad_abbrs'] = bad_abbrs
        st.session_state['replce_abbrs'] = replace_abbrs
        formatted, st.session_state['flag_punct'] = detect.format_text(text_to_check)
        passive_checked = detect.highlight_passive(formatted)
        bad_checked = detect.highlight_bad_words(passive_checked)
        particips = detect.highlight_part(bad_checked)
        verbs = detect.highlight_verbs(particips)
        st.session_state['output'] = detect.highlight_nouns(verbs)
    st.markdown('\n')
    st.markdown(st.session_state['output'], unsafe_allow_html=True)
    if st.session_state['metrics']:
        with st.expander('Открыть комментарии'):
            for metric in st.session_state['metrics']:
                st.markdown(metric)
            if st.session_state['flag_punct']:
                st.markdown('*Я убрал точку в конце*')
            if st.session_state['bad_abbrs']:
                if len(st.session_state['bad_abbrs']) > 1:
                    st.markdown('*Расшифруйте аббревиатуры: *' + ', '.join(st.session_state['bad_abbrs']))
                else:
                    st.markdown('*Расшифруйте аббревиатуру: *' + st.session_state['bad_abbrs'][0])
            if st.session_state['replce_abbrs']:
                st.markdown('*Замените: *')
                for abbr in st.session_state['replce_abbrs'].keys():
                    st.markdown(abbr + ' на ' + st.session_state['replce_abbrs'][abbr])
        st.session_state.clear()
