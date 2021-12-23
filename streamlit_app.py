import detect
import streamlit as st

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


@st.cache
df_abbrs = detect.read_abbr_file()


with st.form(key='my_form'):
    text_to_check = st.text_area(label='Введите текст')
    submit_button = st.form_submit_button(label="Обработать")
if submit_button:
    if text_to_check:
        metrics = detect.complexity_analytics(text_to_check)
        bad_abbrs, replce_abbrs, text_to_check = detect.get_abbrs(text_to_check)
        formatted, flag_punct = detect.format_text(text_to_check)
        passive_checked = detect.highlight_passive(formatted)
        bad_checked = detect.highlight_bad_words(passive_checked)
        particips = detect.highlight_part(bad_checked)
        verbs = detect.highlight_verbs(particips)
        output = detect.highlight_nouns(verbs)
        for metric in metrics:
            st.markdown(metric)
    else:
        output = '*Хм, сначала введите текст*'
    st.markdown('\n')
    st.markdown(output, unsafe_allow_html=True)
    if flag_punct:
        st.markdown('*Я убрал точку в конце*')
    if bad_abbrs:
        if len(bad_abbrs) > 1:
            st.markdown('*Расшифруйте аббревиатуры: *' + ', '.join(bad_abbrs))
        else:
            st.markdown('*Расшифруйте аббревиатуру: *' + bad_abbrs[0])
    if replce_abbrs:
        st.markdown('*Замените: *')
        for abbr in replce_abbrs.keys():
            st.markdown(abbr + ' на ' + replce_abbrs[abbr])
