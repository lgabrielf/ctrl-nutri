import streamlit as st
import csv
from datetime import datetime, timedelta
import subprocess

st.set_page_config(page_title='MGJM - NutriControl', page_icon='logo_h.png')

def login_page():

    
    # Configurando logo do projeto na página de login
    logo_image = 'logo.png'
    st.image(logo_image, width=500)

    st.title('Login')
    
    # Campo de usuário e senha
    username = st.text_input('Usuário')
    password = st.text_input('Senha', type='password')

    # Botão de login
    if st.button('Login'):
        if username == 'admin' and password == '123':
            st.session_state['username'] = username
            st.session_state['permissions'] = 'admin'
        elif username == 'operador' and password == '123':
            st.session_state['username'] = 'operador'
            st.session_state['permissions'] = 'operador'
        else:
            st.error('Usuário ou senha incorretos.')

def ler_estoque():
    with open('estoque.csv', 'r', encoding='latin-1') as arquivo_csv:
        leitor_csv = csv.reader(arquivo_csv)
        estoque = list(leitor_csv)
    return estoque


def gravar_estoque(estoque):
    with open('estoque.csv', 'w', newline='') as arquivo_csv:
        escritor_csv = csv.writer(arquivo_csv)
        escritor_csv.writerows(estoque)


def encontrar_produto_por_codigo(codigo, estoque):
    for i, item in enumerate(estoque):
        if item[3] == codigo:
            return item
    return None


def main():
    if 'username' not in st.session_state:
        login_page()
    else:
        # Carrega o estoque
        estoque = ler_estoque()

        # Título do aplicativo
        st.title('Controle de Estoque - Nutrição Hospitalar')

        # Opções do menu lateral
        if st.session_state['permissions'] == 'admin':
            menu_options = ['Visualizar Estoque', 'Cadastrar Item', 'Editar Item', 'Remover Item', 'Controle de Item']
        else:
            menu_options = ['Visualizar Estoque', 'Controle de Item']

        menu_selecionado = st.sidebar.radio('Menu', menu_options)

        # Página principal
        if menu_selecionado == 'Visualizar Estoque':
            st.header('Estoque Atual')
            st.table(estoque)

        elif menu_selecionado == 'Cadastrar Item' and st.session_state['permissions'] == 'admin':
            st.header('Cadastrar Item ao Estoque')
            nome_produto = st.text_input('Nome do Produto')
            unidade = st.text_input('Unidade do Produto')
            codigo = st.text_input('Código de Barras')
            consumo_mensal = st.text_input('Consumo Mensal')
            validade = st.date_input('Validade do Item')

            data_atual = datetime.now().date()
            dias_restantes = (validade - data_atual).days

            if st.button('Cadastrar'):
                if nome_produto.strip() == '':
                    st.warning('O campo "Nome do Produto" é obrigatório.')
                elif unidade.strip() == '':
                    st.warning('O campo "Unidade do Produto" é obrigatório.')
                elif codigo.strip() == '':
                    st.warning('O campo "Código de Barras" é obrigatório.')
                elif consumo_mensal.strip() == '':
                    st.warning('O campo "Consumo Mensal" é obrigatório.')
                else:
                    item = encontrar_produto_por_codigo(codigo, estoque)
                    if item is not None:
                        st.warning('Item já existe no estoque.')
                    else:
                        data_atual = datetime.now().date()
                        dias_restantes = (validade - data_atual).days
                        novo_item = [nome_produto, '0', unidade, codigo, consumo_mensal, dias_restantes]
                        estoque.append(novo_item)
                        gravar_estoque(estoque)
                        st.success('Item cadastrado com sucesso.')

        elif menu_selecionado == 'Editar Item' and st.session_state['permissions'] == 'admin':
            st.header('Editar Item do Estoque')
            codigo = st.text_input('Código de Barras do Item')

            item = encontrar_produto_por_codigo(codigo, estoque)
            if item is not None:
                nome_produto = st.text_input('Nome do Produto', item[0])
                quantidade = st.number_input('Quantidade em Estoque', min_value=0, value=int(item[1]))
                unidade = st.text_input('Unidade', item[2])
                consumo_mensal = st.text_input('Consumo Mensal', item[4])
                dias_restantes = st.number_input('Validade (dias)', min_value=0, value=int(item[5]))

                validade = datetime.now().date() + timedelta(days=dias_restantes)

                if st.button('Salvar'):
                    item[0] = nome_produto
                    item[1] = str(quantidade)
                    item[2] = unidade
                    item[4] = consumo_mensal
                    item[5] = str(dias_restantes)

                    gravar_estoque(estoque)
                    st.success('Item atualizado com sucesso.')

            else:
                st.warning('Item não encontrado.')

        elif menu_selecionado == 'Remover Item' and st.session_state['permissions'] == 'admin':
            st.header('Remover Item do Estoque')
            codigo = st.text_input('Código de Barras do Item a ser removido')

            item = encontrar_produto_por_codigo(codigo, estoque)
            if item is not None:
                if st.button('Remover'):
                    estoque.remove(item)
                    gravar_estoque(estoque)
                    st.success('Item removido com sucesso!')
            else:
                st.warning('Item não encontrado.')

        elif menu_selecionado == 'Controle de Item':

            st.header('Controle de Item do Estoque')
            codigo = st.text_input('Código de Barras do Item')

            quantidade = st.number_input('Quantidade', min_value=1, value=1)
            col1, col2 = st.columns(2)
            adicionar_button = col1.button('Adicionar')
            remover_button = col2.button('Remover')

            if adicionar_button:
                item = encontrar_produto_por_codigo(codigo, estoque)
                if item is not None:
                    item[1] = str(int(item[1]) + quantidade)
                    gravar_estoque(estoque)
                    st.success(f'Foram adicionadas {quantidade} unidades ao estoque do item {item[0]}.')
                else:
                    st.warning('Item não encontrado.')

            if remover_button:
                item = encontrar_produto_por_codigo(codigo, estoque)
                if item is not None:
                    new_quantity = int(item[1]) - quantidade
                    if new_quantity < 0:
                        st.warning('A quantidade a remover é maior do que a disponível no estoque.')
                    else:
                        item[1] = str(new_quantity)
                        gravar_estoque(estoque)
                        st.success(f'Foram removidas {quantidade} unidades do estoque do item {item[0]}.')
                else:
                    st.warning('Item não encontrado.')

        # Container para posicionar o botão no rodapé do menu        
        container = st.sidebar.container()

        # Adicionar o botão "Sair" no rodapé do menu
        with container:
            st.sidebar.markdown("---")
            if st.sidebar.button('Sair'):
                # Limpar a sessão atual e redirecionar para a tela de login
                del st.session_state['username']
                del st.session_state['permissions']
                st.experimental_rerun()

if __name__ == '__main__':
    main()