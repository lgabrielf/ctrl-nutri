import streamlit as st
import csv


def login_page():
    st.title('Login')

    # Campo de usuário e senha
    username = st.text_input('Usuário')
    password = st.text_input('Senha', type='password')

    # Botão de login
    if st.button('Login'):
        if username == 'admin' and password == 'admin123':
            st.session_state['username'] = username
            st.session_state['permissions'] = 'admin'
        else:
            st.error('Usuário ou senha incorretos.')

    # Botão de seguir como operador
    if st.button('Seguir como operador'):
        st.session_state['username'] = 'operador'
        st.session_state['permissions'] = 'operador'

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
        if item[2] == codigo:
            return i, item
    return None, None

def main():
    if 'username' not in st.session_state:
        login_page()
    else:
        # Carrega o estoque
        estoque = ler_estoque()

        # Título do aplicativo
        st.title('Controle de Estoque - Nutrição Hospitalar')

        sidebar_menu = st.sidebar.empty()
        menu = []

        if st.session_state['permissions'] == 'admin':
            menu = ['Visualizar Estoque', 'Cadastrar Item', 'Remover Item', 'Controle de Item']
        elif st.session_state['permissions'] == 'operador':
            menu = ['Visualizar Estoque', 'Controle de Item']

        opcao = sidebar_menu.selectbox('Selecione uma opção', menu)

        if opcao == 'Visualizar Estoque':
            st.header('Estoque Atual')
            st.table(estoque)

        elif opcao == 'Cadastrar Item' and st.session_state['permissions'] == 'admin':
            st.header('Cadastrar Item ao Estoque')
            nome_produto = st.text_input('Nome do Produto')
            quantidade = st.number_input('Quantidade', min_value=1, value=1)
            codigo = st.text_input('Código de Barras')
            consumo_mensal = st.text_input('Consumo Mensal')

            if st.button('Cadastrar'):
                if nome_produto.strip() == '':
                    st.warning('O campo "Nome do Produto" é obrigatório.')
                elif codigo.strip() == '':
                    st.warning('O campo "Código de Barras" é obrigatório.')
                elif consumo_mensal.strip() == '':
                    st.warning('O campo "Consumo Mensal" é obrigatório.')
                else:
                    index, item = encontrar_produto_por_codigo(codigo, estoque)
                    if item is not None:
                        st.warning('Item já existe no estoque.')
                    else:
                        novo_item = [nome_produto, quantidade, codigo, consumo_mensal]
                        estoque.append(novo_item)
                        gravar_estoque(estoque)
                        st.success('Item cadastrado com sucesso!')

        elif opcao == 'Remover Item' and st.session_state['permissions'] == 'admin':
            st.header('Remover Item do Estoque')
            codigo = st.text_input('Código de Barras do Item a ser removido')

            index, item = encontrar_produto_por_codigo(codigo, estoque)
            if item is not None:
                if st.button('Remover'):
                    estoque.pop(index)
                    gravar_estoque(estoque)
                    st.success('Item removido com sucesso!')
            else:
                st.warning('Item não encontrado.')

        elif opcao == 'Editar Item' and st.session_state['permissions'] == 'admin':
            st.header('Editar Item do Estoque')
            codigo = st.text_input('Código de Barras do Item a ser editado')

            index, item = encontrar_produto_por_codigo(codigo, estoque)
            if item is not None:
                st.subheader('Parâmetros do Produto')
                nome_produto = st.text_input('Nome do Produto', item[0])
                quantidade = st.number_input('Quantidade', min_value=1, value=int(item[1]))

                if st.button('Salvar Edição'):
                    item[0] = nome_produto
                    item[1] = str(quantidade)
                    gravar_estoque(estoque)
                    st.success('Item editado com sucesso!')
            else:
                st.warning('Item não encontrado.')

        elif opcao == 'Controle de Item':
            st.header('Controle de Item do Estoque')
            codigo = st.text_input('Código de Barras do Item')

            quantidade = st.number_input('Quantidade', min_value=1, value=1)

            col1, col2 = st.columns(2)

            if col1.button('Adicionar'):
                for item in estoque:
                    if item[2] == codigo:
                        item[1] = str(int(item[1]) + quantidade)
                        gravar_estoque(estoque)
                        st.success(f'Foram adicionadas {quantidade} unidades ao estoque do item {item[0]}.')
                        break

            if col2.button('Remover'):
                for item in estoque:
                    if item[2] == codigo:
                        new_quantity = int(item[1]) - quantidade
                        if new_quantity < 0:
                            st.warning('A quantidade a remover é maior do que a disponível no estoque.')
                        else:
                            item[1] = str(new_quantity)
                            gravar_estoque(estoque)
                            st.success(f'Foram removidas {quantidade} unidades do estoque do item {item[0]}.')
                        break

if __name__ == '__main__':
    main()