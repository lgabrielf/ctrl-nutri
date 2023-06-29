import streamlit as st
import csv, barcode, os, zipfile, string, ctypes
from barcode.writer import ImageWriter
from datetime import datetime, timedelta

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

def popup_confirmacao():
    result = ctypes.windll.user32.MessageBoxW(0, "Deseja registrar a entrada?", "Confirmação", 1)
    return result == 1

def verificar_item_existente(nome, unidade, estoque):
    for item in estoque:
        if len(item) >= 3 and item[0].lower() == nome.lower() and item[2].lower() == unidade.lower():
            return True
    return False

def gerar_codigo_barras(nome, unidade):
    nome_limpo = nome.translate(str.maketrans('', '', string.punctuation)).replace(' ', '').lower()
    unidade_limpa = unidade.translate(str.maketrans('', '', string.punctuation)).replace(' ', '').lower()
    codigo = barcode.get('code39', nome_limpo + '_' + unidade_limpa, writer=ImageWriter())
    barcode_folder_path = os.path.join(os.getcwd(), PASTA_IMAGENS)
    os.makedirs(barcode_folder_path, exist_ok=True)
    barcode_path = os.path.join(barcode_folder_path, nome_limpo + '_' + unidade_limpa)
    codigo.save(barcode_path)
    return nome, nome_limpo


def calcular_consumo_mensal(estoque):
    consumo_mensal = {}
    hoje = datetime.now()

    for item in estoque[1:]:
        codigo_barras = item[3]
        saidas = int(item[5]) if item[5] else 0
        data_ultima_saida = item[6]

        if saidas > 0 and data_ultima_saida:
            data_ultima_saida = datetime.strptime(data_ultima_saida, "%Y-%m-%d %H:%M:%S")
            dias_passados = (hoje - data_ultima_saida).days

            if dias_passados <= 30:
                consumo_mensal[codigo_barras] = consumo_mensal.get(codigo_barras, 0) + saidas

    return consumo_mensal

def ler_estoque():
    with open('estoque.csv', 'r', encoding='latin-1') as arquivo_csv:
        leitor_csv = csv.reader(arquivo_csv)
        estoque = list(leitor_csv)
    return estoque

def gravar_estoque(estoque):
    with open('estoque.csv', 'w', newline='', encoding='latin-1') as arquivo_csv:
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
                'Entrada de Produtos', 
                'Saída de Produtos'
            ]
        else:
            menu_options = ['Visualizar Estoque', 'Entrada de Produtos', 'Saída de Produtos']

        menu_selecionado = st.sidebar.radio('Menu', menu_options)

        # Página principal
        if menu_selecionado == 'Visualizar Estoque':
            st.header('Estoque Atual')

            # Calcular o consumo mensal
            consumo_mensal = calcular_consumo_mensal(estoque)

            # Adicionar o consumo mensal e dias restantes ao item de estoque
            for item in estoque[1:]:
                codigo_barras = item[3]
                quantidade = int(item[1]) if item[1] else 0
                estoque_seguranca = int(item[4]) if item[4] else 0
                consumo = consumo_mensal.get(codigo_barras, 0)
                dias_restantes = int(quantidade - estoque_seguranca) // consumo if consumo != 0 else 0
                item.extend([consumo, dias_restantes])

            # Criar uma cópia do estoque com as colunas adicionais
            estoque_display = [["Nome do Produto", "Quantidade", "Unidade", "Código de Barras", "Estoque de Segurança", "Saída", "Consumo Mensal", "Dias Restantes"]] + [item[:6] + item[7:] for item in estoque[1:]]
            
            # Exibir a tabela do estoque
            st.table(estoque_display)

        elif menu_selecionado == 'Cadastrar Novo Item' and st.session_state['permissions'] == 'admin':
            st.header('Cadastrar Novo Item ao Estoque')
            nome_produto = st.text_input('Nome do Produto')
            unidade = st.selectbox('Unidade do Item', ('KG', 'DUZIA (PACOTE)', 'CAIXA', 'UNIDADE'))
            estoque_seguranca = st.number_input('Estoque de segurança do Item', min_value=0)

            if st.button('Cadastrar'):
                if nome_produto.strip() == '':
                    st.warning('O campo "Nome do Produto" é obrigatório.')
                elif unidade.strip() == '':
                    st.warning('O campo "Unidade do Produto" é obrigatório.')
                elif estoque_seguranca is None or estoque_seguranca < 0:
                    st.warning('O campo "Estoque de Segurança" deve ser preenchido com um valor válido.')
                elif verificar_item_existente(nome_produto, unidade, estoque):
                    st.warning('O item já existe no estoque.')
                else:
                    nome_produto, nome_produto_limpo = gerar_codigo_barras(nome_produto, unidade)

                    novo_item = [nome_produto, '0', unidade, nome_produto_limpo, estoque_seguranca, '0', '']
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

        elif menu_selecionado == 'Ajuste de Inventário':

            st.header('Ajuste de Inventário do Estoque')
            codigo = st.text_input('Código de Barras do Item')

            quantidade = st.number_input('Quantidade', min_value=1, value=1)
            col1, col2 = st.columns(2)
            adicionar_button = col1.button('Adicionar', key='adicionar')
            remover_button = col2.button('Remover', key='remover')

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
                        item[5] = str(int(item[5]) + 1)
                        gravar_estoque(estoque)
                        st.success(f'Foram removidas {quantidade} unidades do estoque do item {item[0]}.')
                else:
                    st.warning('Item não encontrado.')

        elif menu_selecionado == 'Entrada de Produtos':
            st.write('<style>div.entry-header { background-color: blue; padding: 10px; border-radius: 5px; color: white; font-size: 20px; font-weight: bold; }</style>', unsafe_allow_html=True)
            st.write('<div class="entry-header">Entrada de Produtos</div>', unsafe_allow_html=True)
            "---"

            codigo1 = st.text_input('Código de Barras do Item')
            item = encontrar_produto_por_codigo(codigo1, estoque)

            if item is not None:
                quantidade = 1
                if st.button('Registrar entrada'):
                    confirmado = popup_confirmacao()
                    if confirmado:
                        item[1] = str(int(item[1]) + 1)
                        gravar_estoque(estoque)
                        st.success("Entrada registrada com sucesso.")
                    else:
                        st.info("A entrada de produtos não foi registrada.")
            else:
                st.warning("Item não encontrado.")


        elif menu_selecionado == 'Saída de Produtos':
            st.write('<style>div.exit-header { background-color: red; padding: 10px; border-radius: 5px; color: white; font-size: 20px; font-weight: bold; }</style>', unsafe_allow_html=True)
            st.write('<div class="exit-header">Saída de Produtos</div>', unsafe_allow_html=True)
            "---"

            codigo = st.text_input('Código de Barras do Item')
            item = encontrar_produto_por_codigo(codigo, estoque)

            if item is not None:
                quantidade = 1

                if st.button('Registrar saída'):
                    quantidade = int(item[1])
                    if quantidade > 0:
                        item[1] = str(quantidade - 1)
                        item[5] = str(int(item[5]) + 1)
                        item[6] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Atualiza a data da última saída
                        gravar_estoque(estoque)
                        st.success("Saída registrada com sucesso.")

                        # Atualiza o consumo mensal
                        consumo_mensal = calcular_consumo_mensal(estoque)
                    else:
                        st.warning("Não há estoque disponível desse item.")
            else:
                st.warning("Item não encontrado.")

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