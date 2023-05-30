import streamlit as st
import csv

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
    # Carrega o estoque
    estoque = ler_estoque()

    # Título do aplicativo
    st.title('Controle de Estoque - Nutrição Hospitalar')

    # Opções do menu
    menu = ['Visualizar Estoque', 'Adicionar Item', 'Remover Item', 'Editar Item']
    opcao = st.sidebar.selectbox('Selecione uma opção', menu)

    if opcao == 'Visualizar Estoque':
        st.header('Estoque Atual')
        st.table(estoque)

    elif opcao == 'Adicionar Item':
        st.header('Adicionar Item ao Estoque')
        nome_produto = st.text_input('Nome do Produto')
        quantidade = st.number_input('Quantidade', min_value=1, value=1)
        codigo = st.text_input('Código de Barras')

        if st.button('Adicionar'):
            if nome_produto.strip() == '':
                st.warning('O campo "Nome do Produto" é obrigatório.')
            elif codigo.strip() == '':
                st.warning('O campo "Código de Barras" é obrigatório.')
            else:
                index, item = encontrar_produto_por_codigo(codigo, estoque)
                if item is not None:
                    st.warning('Item já existe no estoque.')
                else:
                    novo_item = [nome_produto, quantidade, codigo]
                    estoque.append(novo_item)
                    gravar_estoque(estoque)
                    st.success('Item adicionado com sucesso!')

    elif opcao == 'Remover Item':
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

    elif opcao == 'Editar Item':
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

if __name__ == '__main__':
    main()
