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
st.sidebar.markdown("**Важно!** Этот интструмент лишь подсказывает возможные ошибки, но не гарантирует их наличие.")
st.sidebar.markdown("С замечаниями и предложениями писать Анне Аксеновой *tg: aksenysh*")

with st.form(key='my_form'):
    text_to_check = st.text_input(label='Введите текст')
    submit_button = st.form_submit_button(label="Обработать")
if submit_button:
    if text_to_check:
        metrics = detect.complexity_analytics(text_to_check)
        formatted = detect.format_text(text_to_check)
        bad_checked = detect.highlight_bad_words(formatted)
        passive_checked = detect.highlight_passive(bad_checked)
        particips = detect.highlight_part(passive_checked)
        verbs = detect.highlight_verbs(particips)
        output = detect.highlight_nouns(verbs)
        st.write("""*Спасибо за ожидание! Вот, что получилось:*""")
        for metric in metrics:
            st.markdown(metric)
    else:
        output = '*Хм, сначала введите текст*'
    st.markdown('\n')
    st.markdown(output, unsafe_allow_html=True)
