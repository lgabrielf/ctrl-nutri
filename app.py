import streamlit as st
import csv, barcode, os, zipfile
from datetime import datetime, timedelta
from barcode.writer import ImageWriter

PASTA_IMAGENS = os.path.abspath("barcode_item")

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

def gerar_codigo_barras(nome_item):

    codigo = barcode.get('code128', nome_item, writer=ImageWriter())
    nome_arquivo = f"{nome_item}"
    caminho_arquivo = os.path.join("barcode_item", nome_arquivo)
    codigo.save(caminho_arquivo, options={'module_width': 0.4, 'module_height': 8.0})

    return nome_arquivo

def ler_estoque():
    with open('estoque.csv', 'r', encoding='latin-1') as arquivo_csv:
        leitor_csv = csv.reader(arquivo_csv)
        estoque = list(leitor_csv)
    return estoque

def gravar_estoque(estoque):
    with open('estoque.csv', 'w', newline='') as arquivo_csv:
        writer = csv.writer(arquivo_csv)
        writer.writerows(estoque)

def encontrar_produto_por_codigo(codigo, estoque):
    for item in estoque:
        if item[3] == codigo:
            return item
    return None

def download_todas_imagens():
    barcode_folder = "barcode_item"
    output_zip_file = "codigos_barras.zip"

    # Lista todos os arquivos na pasta de códigos de barras
    codigos_barras_files = os.listdir(barcode_folder)

    # Cria um arquivo ZIP para armazenar as imagens
    with zipfile.ZipFile(output_zip_file, "w") as zip_file:
        # Adiciona cada imagem ao arquivo ZIP
        for arquivo in codigos_barras_files:
            caminho_arquivo = os.path.join(barcode_folder, arquivo)
            zip_file.write(caminho_arquivo, arcname=arquivo)

    # Disponibiliza o arquivo ZIP para download
    with open(output_zip_file, "rb") as file:
        st.download_button(
            label="Baixar Códigos de barras",
            data=file,
            file_name=output_zip_file,
            mime="application/zip"
        )

    # Remove o arquivo ZIP após o download
    os.remove(output_zip_file)

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
            menu_options = [
                'Visualizar Estoque', 
                'Cadastrar Novo Item', 
                'Editar Item', 
                'Ajuste de Inventário',
                'Controle de Item',
                'Entrada de Produtos', 
                'Saída de Produtos'
            ]
        else:
            menu_options = ['Visualizar Estoque', 'Controle de Item']

        menu_selecionado = st.sidebar.radio('Menu', menu_options)

        # Página principal
        if menu_selecionado == 'Visualizar Estoque':
            st.header('Estoque Atual')
            st.table(estoque)

        elif menu_selecionado == 'Cadastrar Novo Item' and st.session_state['permissions'] == 'admin':
            st.header('Cadastrar Novo Item ao Estoque')
            nome_produto = st.text_input('Nome do Produto')
            unidade = st.selectbox('Unidade do Item',('KG', 'DUZIA (PACOTE)', 'CAIXA', 'UNIDADE'))
            estoque_seguranca = st.number_input('Estoque de segurança do Item', min_value=0)
            # validade = st.date_input('Validade do Item')

            # data_atual = datetime.now().date()
            # dias_restantes = (validade - data_atual).days

            if st.button('Cadastrar'):
                if nome_produto.strip() == '':
                    st.warning('O campo "Nome do Produto" é obrigatório.')
                elif unidade.strip() == '':
                    st.warning('O campo "Unidade do Produto" é obrigatório.')
                elif estoque_seguranca is None or estoque_seguranca < 0:
                    st.warning('O campo "Estoque de Segurança" deve ser preenchido com um valor válido.')
                else:
                    codigo_produto = gerar_codigo_barras(nome_produto)

                    novo_item = [nome_produto, '0', unidade, codigo_produto, estoque_seguranca, '', '']
                    estoque.append(novo_item)
                    gravar_estoque(estoque)
                    st.success('Item cadastrado com sucesso.')

        elif menu_selecionado == 'Editar Item' and st.session_state['permissions'] == 'admin':
            st.header('Editar Item do Estoque')
            codigo = st.text_input('Código de Barras do Item')

            item = encontrar_produto_por_codigo(codigo, estoque)
            if item is not None:
                nome_produto = st.text_input('Nome do Produto', item[0])
                unidade = st.selectbox('Unidade do Item',('KG', 'DUZIA (PACOTE)', 'CAIXA', 'UNIDADE'))


                if st.button('Salvar'):
                    item[0] = nome_produto
                    item[2] = unidade

                    gravar_estoque(estoque)
                    st.success('Item atualizado com sucesso.')

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


        st.sidebar.markdown("---")


        # Container para posicionar o botão no rodapé do menu        
        container = st.sidebar.container()
        
        with container:
            download_todas_imagens()

        # adicionando logo
        st.sidebar.markdown("---")
        logo_image = 'logo_h.png'
        logo_col, _ = st.sidebar.columns([1, 4])
        logo_col.image(logo_image, width=200)

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