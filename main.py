import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import google.generativeai as genai
import uvicorn

# 1. Configurações Iniciais da IA
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 2. Criação do Servidor (Obrigatório vir ANTES das rotas e middlewares)
app = FastAPI(title="API de Inteligência Comercial")

# 3. Montagem do Front-end e Middlewares
# Por que fazer isso? Isso avisa ao FastAPI que a pasta "static" contém arquivos do front-end (CSS, JS, imagens) e os deixa acessíveis.
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROMPT_COMERCIAL = """
Atue como um Consultor Estratégico Sênior de Inteligência Comercial e Desenvolvedor Front-end Especialista. OBJETIVO DO PROJETO: Sua tarefa é receber dados brutos de apresentações comerciais (ex: faturamento, volume, margem, logística, sell-out) via upload de arquivos e transformá-los em um Relatório Executivo PREMIUM, estritamente analítico e acionável, entregue EXCLUSIVAMENTE em formato HTML/CSS (único arquivo auto-contido).

REGRA DE OURO 1 (PRINCÍPIO MECE - ANTI-REDUNDÂNCIA E PROGRESSÃO): Aja de forma cirúrgica. NENHUM insight, explicação analítica ou diagnóstico pode ser repetido em mais de uma seção. Cada bloco do relatório tem uma função única. Exceção estratégica: Você pode (e deve) referenciar um KPI central (ex: "queda de 3% no volume") já citado no Sumário como o [Dado Gatilho] no Plano de Ação, mas a análise e a solução devem avançar e ser inéditas. Não repita os motivos, entregue a ação.

REGRA DE OURO 2 (ESTILO TELEGRÁFICO E LIMITE DE EXTENSÃO): O relatório é voltado para a alta diretoria (C-Level/Compradores Sêniores) e DEVE ser extremamente denso, curto e objetivo.
* Estilo: Corte adjetivos, introduções educadas, jargões vazios e explicações óbvias. Vá direto ao dado numérico e à ação. Frases curtas e diretas. Proibido parágrafos com mais de 4 linhas.
* Extensão: O documento final não pode ultrapassar 3 páginas quando impresso.

REGRA DE OURO 3 (CAUSALIDADE OBRIGATÓRIA E CONTEXTO): Em hipótese alguma adicione informações soltas. Toda métrica apresentada deve estar obrigatoriamente atrelada ao seu "porquê" (sua causa raiz suportada pelos dados). Cada número deve justificar um contexto, e cada contexto deve justificar uma ação.

ESTRUTURA OBRIGATÓRIA DO HTML (Siga a ordem estritamente):
1. CABEÇALHO COMPACTO
* Logo textual: "Relatório Executivo Analítico" + [Data Atual] + [Nome do Arquivo/Marca analisada]. (Tudo na mesma linha ou com margens mínimas).
* Linha horizontal divisória limpa.
2. SUMÁRIO MACRO (O QUÊ ACONTECEU)
* Máximo de 3 bullet points diretos com os KPIs centrais e o diagnóstico geral do negócio. Sem texto corrido. Apenas os fatos quantitativos atrelados ao seu contexto direto.
3. DIAGNÓSTICO SWOT (POR QUE ACONTECEU)
* Tabela/Grid 2x2 extremamente compacto: Forças (verde) | Fraquezas (vermelho) | Oportunidades (azul) | Ameaças (laranja).
* Máximo de 2 a 3 itens por quadrante. Frases de no máximo 10 palavras por item.
* Proibido repetir os KPIs puros do Sumário. Traga estritamente os motivos operacionais, mercadológicos ou logísticos evidenciados nos dados que causaram aqueles números.
4. PLANO DE AÇÃO INTEGRADO (COMO RESOLVER)
* Limite-se a MÁXIMO 4 Cards de Ação Estratégica (as mais críticas para o negócio).
* Cada card deve conter os seguintes elementos de forma concisa:
  * [Dado Gatilho]: A evidência numérica exata que gerou a ação (em itálico ou blockquote curto).
  * [Ação Recomendada]: O que fazer (inicie com verbo no imperativo).
  * [Área Responsável]: Quem executará a ação (ex: Trade Marketing, Logística, Vendas).
  * [Tags de Execução]: Prioridade (Alta/Média/Baixa) | Esforço (Alto/Médio/Baixo). Use cores diferentes para as tags (ex: verde para alta prioridade).
  * [Impacto]: O resultado financeiro/operacional projetado (uma frase curta, justificando o porquê da ação).

REGRAS DE ESTILO CSS (FOCO EM LEGIBILIDADE E IMPRESSÃO):
* Paleta Executiva: Azul Marinho (#1a365d) para títulos, Cinza Ártico (#f7fafc) para fundos de bloco, acentos em #2b6cb0.
* Fonte OBRIGATÓRIA: font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
* CSS de Impressão OBRIGATÓRIO: Inclua a diretiva @media print com quebras de página evitadas (break-inside: avoid) e cores pretas.

RESTRIÇÕES FINAIS E PENSAMENTO EM CADEIA:
* ZERO ALUCINAÇÃO: É ESTRITAMENTE PROIBIDO inventar dados.
* PROIBIDO criar Índice, Conclusão, Introdução.
* EXTRAÇÃO E MECE: Inicie o código estruturando seu raciocínio em um comentário HTML invisível ().
* FORMATO DE SAÍDA: Retorne ABSOLUTAMENTE APENAS o código HTML completo. O primeiro caractere deve ser <!DOCTYPE html> e o último </html>. Sem markdown.
"""

# 4. Rotas de Navegação e API
@app.get("/", response_class=HTMLResponse)
async def read_index():
    # Por que FileResponse? Ele carrega e devolve o arquivo HTML para o navegador do usuário com os cabeçalhos corretos de resposta HTTP.
    return FileResponse('static/index.html')

@app.post("/gerar-relatorio")
async def gerar_relatorio(file: UploadFile = File(...)):
    temp_file_path = f"{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())

        gemini_file = genai.upload_file(temp_file_path)
        # Atenção: Se o 2.5 falhar, tente o 'gemini-1.5-flash'
        model = genai.GenerativeModel('gemini-2.5-flash') 
        
        response = model.generate_content([gemini_file, PROMPT_COMERCIAL])
        html_final = response.text.replace("```html", "").replace("```", "").strip()

        os.remove(temp_file_path)
        genai.delete_file(gemini_file.name)

        return HTMLResponse(content=html_final)

    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return {"erro": f"Ocorreu um erro no processamento: {str(e)}"}

# 5. Bloco de Inicialização (Sempre por último)
if __name__ == "__main__":
    # Por que usar os.environ.get? O Cloud Run aloca uma porta dinâmica aleatória a cada inicialização através desta variável de ambiente. Se tentarmos forçar a porta 8080 rígida, o container falhará ao iniciar.
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
