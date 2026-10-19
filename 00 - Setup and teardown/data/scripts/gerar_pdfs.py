#!/usr/bin/env python3
"""
Gerador de PDFs sintéticos da Vida+ Saúde.

Cria documentos pertinentes ao domínio (rol de cobertura, regras de autorização,
prazos de atendimento, FAQ) coerentes com os procedimentos do gerador.
Usa fonte Unicode para acentuação pt-BR.

Compatível com fpdf2.
"""

import os
import sys
from datetime import datetime
from fpdf import FPDF

# Diretório de saída
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Font file
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
if not os.path.exists(FONT_PATH):
    print(f"ERRO: Font {FONT_PATH} not found!")
    sys.exit(1)

# Procedimentos do gerador (todos requerem autorização prévia)
PROCEDIMENTOS = [
    ("consulta_cardiologia", "Consulta em Cardiologia", 14),
    ("ressonancia_magnetica", "Ressonância Magnética", 21),
    ("tomografia", "Tomografia Computadorizada", 21),
    ("endoscopia", "Endoscopia Diagnóstica", 10),
    ("cirurgia_ortopedica", "Cirurgia Ortopédica", 21),
    ("ultrassom", "Ultrassom (Diagnóstico)", 3),
    ("fisioterapia", "Fisioterapia", 3),
    ("internacao", "Internação Hospitalar", 21),
]

class PDFVidaSaude(FPDF):
    """Classe customizada de PDF para Vida+ Saúde."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_color = (30, 100, 150)
        self.title_text = ""

        # Registrar fonte Unicode
        self.add_font("Arial", "", FONT_PATH)
        self.add_font("Arial", "B", FONT_PATH)
        self.add_font("Arial", "I", FONT_PATH)

    def header(self):
        self.set_fill_color(*self.logo_color)
        self.rect(0, 0, 210, 15, style="F")

        self.set_font("Arial", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "VIDA+ SAÚDE", new_x="LMARGIN", new_y="NEXT")

        self.set_text_color(0, 0, 0)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "Documento fictício para fins de treinamento.", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, f"Página {self.page_no()} | Emitido em {datetime.now().strftime('%d/%m/%Y')}")

    def section_title(self, title):
        self.set_font("Arial", "B", 14)
        self.set_text_color(*self.logo_color)
        self.ln(5)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def subsection_title(self, title):
        self.set_font("Arial", "B", 11)
        self.set_text_color(50, 50, 50)
        self.ln(3)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def normal_text(self, text):
        self.set_font("Arial", "", 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, text)
        self.ln(1)

def create_rol_cobertura():
    """PDF 1: Rol de Cobertura."""
    pdf = PDFVidaSaude()
    pdf.add_page()

    pdf.section_title("ROL DE COBERTURA")
    pdf.normal_text(
        "Este documento apresenta os procedimentos cobertos pelo plano Vida+ Saúde. "
        "Todos os procedimentos listados requerem autorização prévia, solicitada pelo prestador. "
        "Cobertura válida a partir de 01/01/2026."
    )

    pdf.subsection_title("Procedimentos Cobertos")
    for code, nome, prazo in PROCEDIMENTOS:
        pdf.normal_text(f"• {nome} (Prazo máximo de realização: {prazo} dias úteis)")

    pdf.ln(2)
    pdf.subsection_title("Exclusões Gerais")
    exclusoes = [
        "Procedimentos estéticos (exceto por indicação médica comprovada);",
        "Tratamentos experimentais não aprovados pelo CFM;",
        "Medicamentos não registrados na ANVISA;",
        "Procedimentos sem comprovação científica;",
        "Atendimento fora da rede credenciada (exceto em urgência/emergência).",
    ]
    for exclusao in exclusoes:
        pdf.normal_text(f"- {exclusao}")

    if pdf.will_page_break(10):
        pdf.add_page()

    pdf.ln(2)
    pdf.subsection_title("Autorização Prévia para Todos os Procedimentos")
    pdf.normal_text(
        "Todos os procedimentos cobertos, sem exceção, requerem autorização prévia emitida por Vida+ Saúde "
        "antes da realização. A solicitação é encaminhada pelo prestador através do portal ou central de autorização. "
        "A análise é realizada pela equipe médica em até 5 dias úteis."
    )

    pdf.output(os.path.join(OUTPUT_DIR, "01_rol_cobertura.pdf"))
    print("✓ 01_rol_cobertura.pdf criado")

def create_regras_autorizacao():
    """PDF 2: Regras de Autorização Prévia."""
    pdf = PDFVidaSaude()
    pdf.add_page()

    pdf.section_title("REGRAS DE AUTORIZAÇÃO PRÉVIA")
    pdf.normal_text(
        "Todo procedimento coberto requer autorização prévia. Esta guia apresenta "
        "o fluxo, critérios e motivos de negativa."
    )

    pdf.subsection_title("Fluxo de Análise")
    fluxo = [
        "1. Solicitada: Prestador envia formulário com dados do beneficiário e procedimento;",
        "2. Em Análise: Equipe médica avalia a solicitação (máximo 5 dias úteis);",
        "3. Aprovada: Beneficiário realiza procedimento com cobertura total;",
        "4. Negada: Beneficiário recebe comunicação com motivo médico explícito.",
    ]
    for etapa in fluxo:
        pdf.normal_text(etapa)

    pdf.ln(2)
    pdf.subsection_title("Critérios de Aprovação")
    criterios = [
        "Procedimento incluído no rol de cobertura;",
        "Benefício vigente e sem restrições;",
        "Indicação clínica apropriada pelo médico solicitante;",
        "Conformidade com prazos de carência (se aplicável).",
    ]
    for criterio in criterios:
        pdf.normal_text(f"• {criterio}")

    if pdf.will_page_break(30):
        pdf.add_page()

    pdf.ln(2)
    pdf.subsection_title("Motivos Comuns de Negativa")
    pdf.normal_text(
        "Autorização negada quando: procedimento fora do rol, benefício inativo, indicação clínica insuficiente, "
        "limite de sessões/procedimentos anual atingido, ou procedimento em carência."
    )

    pdf.output(os.path.join(OUTPUT_DIR, "02_regras_autorizacao.pdf"))
    print("✓ 02_regras_autorizacao.pdf criado")

def create_prazos_atendimento():
    """PDF 3: Prazos de Atendimento (ANS)."""
    pdf = PDFVidaSaude()
    pdf.add_page()

    pdf.section_title("PRAZOS DE ATENDIMENTO")
    pdf.normal_text(
        "De acordo com a Resolução Normativa RN 259 da ANS, os prazos máximos para "
        "realização de procedimentos na Vida+ Saúde são:"
    )

    pdf.ln(2)
    pdf.subsection_title("Prazos Máximos por Procedimento (Dias Úteis)")
    for code, nome, prazo in PROCEDIMENTOS:
        categoria = "Urgência" if prazo <= 3 else ("Padrão" if prazo <= 14 else "Eletivo")
        pdf.normal_text(f"• {nome}: {prazo} dias úteis ({categoria})")

    pdf.ln(2)
    pdf.subsection_title("Definições de Prazo")
    pdf.normal_text(
        "Urgência (até 3 dias): Procedimentos que requerem atendimento rápido para evitar agravamento. "
        "Padrão (4 a 14 dias): Procedimentos de complexidade moderada. "
        "Eletivo (acima de 14 dias): Procedimentos agendáveis conforme disponibilidade."
    )

    if pdf.will_page_break(20):
        pdf.add_page()

    pdf.ln(2)
    pdf.subsection_title("Prazos de Análise de Autorização Prévia")
    pdf.normal_text(
        "A análise de solicitação de autorização prévia deve ser completada em: "
        "24 horas para procedimentos de urgência/emergência; "
        "5 dias úteis para procedimentos de padrão e eletivo."
    )

    pdf.output(os.path.join(OUTPUT_DIR, "03_prazos_atendimento.pdf"))
    print("✓ 03_prazos_atendimento.pdf criado")

def create_faq_prestador():
    """PDF 4: FAQ do Prestador."""
    pdf = PDFVidaSaude()
    pdf.add_page()

    pdf.section_title("PERGUNTAS FREQUENTES - PRESTADORES")

    faqs = [
        (
            "P: Como solicitar autorização para um procedimento?",
            "R: Utilize o portal Vida+ Saúde (www.vidasaude-prestador.example) "
            "ou contate nossa central (0800 000 0000). Forneça dados do beneficiário, procedimento e justificativa clínica."
        ),
        (
            "P: Qual é o prazo máximo para análise?",
            "R: 24 horas para urgências; 5 dias úteis para os demais procedimentos."
        ),
        (
            "P: O que significa cada status?",
            "R: Solicitada (recebimento confirmado), Em Análise (avaliação em curso), "
            "Aprovada (autorizado), Negada (rejeitado com justificativa)."
        ),
        (
            "P: Como receber reembolso fora da rede credenciada?",
            "R: Reembolsos apenas em urgência/emergência comprovada. Contacte a central de relacionamento."
        ),
        (
            "P: Como atualizar dados cadastrados?",
            "R: Acesse o portal ou envie documentação para credenciamento@vidasaude.example"
        ),
    ]

    for pergunta, resposta in faqs:
        pdf.subsection_title(pergunta)
        pdf.normal_text(resposta)
        pdf.ln(1)

    pdf.output(os.path.join(OUTPUT_DIR, "04_faq_prestador.pdf"))
    print("✓ 04_faq_prestador.pdf criado")

def create_termos_condicoes():
    """PDF 5: Termos e Condições."""
    pdf = PDFVidaSaude()
    pdf.add_page()

    pdf.section_title("TERMOS E CONDIÇÕES")

    pdf.subsection_title("1. Vigência do Benefício")
    pdf.normal_text(
        "O benefício começa no 1º dia do mês seguinte ao da contratação, "
        "observados os prazos de carência conforme legislação ANS."
    )

    pdf.subsection_title("2. Carência")
    pdf.normal_text(
        "30 dias para procedimentos ambulatoriais; "
        "60 dias para internações (exceto emergência)."
    )

    pdf.subsection_title("3. Cobertura em Emergência")
    pdf.normal_text(
        "Procedimentos de emergência são cobertos independente de carência, "
        "mediante comprovação médica."
    )

    pdf.subsection_title("4. Rede de Prestadores")
    pdf.normal_text(
        "Cobertura integral na rede credenciada. "
        "Reembolsos parciais fora da rede conforme tabela ANS."
    )

    if pdf.will_page_break(20):
        pdf.add_page()

    pdf.subsection_title("5. Cancelamento")
    pdf.normal_text(
        "O beneficiário pode cancelar com aviso de 30 dias. "
        "Sem débito pendente no mês do cancelamento."
    )

    pdf.subsection_title("6. Responsabilidades do Beneficiário")
    pdf.normal_text(
        "Manter dados atualizados, informar mudança de atividade profissional, "
        "utilizar a rede credenciada, respeitar períodos de carência."
    )

    pdf.output(os.path.join(OUTPUT_DIR, "05_termos_condicoes.pdf"))
    print("✓ 05_termos_condicoes.pdf criado")

def create_guia_beneficiario():
    """PDF 6: Guia do Beneficiário."""
    pdf = PDFVidaSaude()
    pdf.add_page()

    pdf.section_title("GUIA DO BENEFICIÁRIO")

    pdf.subsection_title("Bem-vindo à Vida+ Saúde!")
    pdf.normal_text(
        "Você é beneficiário do plano Vida+ Saúde. Este guia apresenta "
        "informações essenciais para utilizar sua cobertura."
    )

    pdf.subsection_title("Como Usar o Plano")
    passos = [
        "1. Escolha um prestador credenciado (visite www.vidasaude.example/rede);",
        "2. Agende a consulta ou procedimento;",
        "3. Apresente seu cartão de beneficiário;",
        "4. Para qualquer procedimento, verifique se foi pré-autorizado.",
    ]
    for passo in passos:
        pdf.normal_text(passo)

    pdf.ln(2)
    pdf.subsection_title("Contatos Úteis")
    pdf.normal_text(
        "Central de Atendimento: 0800 000 0000\n"
        "Atendimento: 24h, 7 dias por semana\n"
        "Email: atendimento@vidasaude.example\n"
        "Portal: www.vidasaude.example"
    )

    pdf.ln(2)
    pdf.subsection_title("Autorização Prévia Obrigatória")
    pdf.normal_text(
        "Todo procedimento requer autorização prévia. O prestador solicita diretamente. "
        "Você pode acompanhar o status pelo portal ou telefone usando seu CPF e número de beneficiário."
    )

    pdf.output(os.path.join(OUTPUT_DIR, "06_guia_beneficiario.pdf"))
    print("✓ 06_guia_beneficiario.pdf criado")

def create_procedimentos_cancelamento():
    """PDF 7: Procedimentos de Cancelamento."""
    pdf = PDFVidaSaude()
    pdf.add_page()

    pdf.section_title("PROCEDIMENTOS DE CANCELAMENTO")

    pdf.subsection_title("Motivos de Cancelamento")
    pdf.normal_text(
        "Você pode cancelar o benefício a qualquer momento, sem justificativa. "
        "Cancelamentos podem ser solicitados pelo beneficiário, titular do contrato ou administrador."
    )

    pdf.subsection_title("Passo a Passo para Cancelamento")
    passos = [
        "1. Notifique com 30 dias de antecedência (portal, telefone ou carta);",
        "2. Regularize qualquer débito pendente;",
        "3. Confirme a data de cancelamento (último dia do mês);",
        "4. Mantenha cobertura ativa até a data final.",
    ]
    for passo in passos:
        pdf.normal_text(passo)

    pdf.ln(2)
    pdf.subsection_title("Penalidades")
    pdf.normal_text(
        "Não há multa ou penalidade por cancelamento. "
        "O benefício é rescindido conforme legislação ANS."
    )

    pdf.ln(2)
    pdf.subsection_title("Reativação")
    pdf.normal_text(
        "Beneficiários que cancelaram nos últimos 12 meses podem reativar "
        "sem carência mediante aprovação por escrito."
    )

    pdf.output(os.path.join(OUTPUT_DIR, "07_procedimentos_cancelamento.pdf"))
    print("✓ 07_procedimentos_cancelamento.pdf criado")

def create_coberturas_especiais():
    """PDF 8: Coberturas Especiais."""
    pdf = PDFVidaSaude()
    pdf.add_page()

    pdf.section_title("COBERTURAS ESPECIAIS")

    pdf.subsection_title("Programa de Prevenção")
    pdf.normal_text(
        "Beneficiários têm direito a 2 consultas preventivas anuais com cardiologista, "
        "incluindo eletrocardiograma e avaliação básica, ambas com autorização prévia."
    )

    pdf.subsection_title("Reabilitação e Fisioterapia")
    pdf.normal_text(
        "Cobertura de até 30 sessões anuais de fisioterapia para procedimentos "
        "ortopédicos pós-operatórios, com autorização prévia. Cada sessão segue prazo de 3 dias úteis."
    )

    pdf.subsection_title("Procedimentos de Urgência/Emergência")
    pdf.normal_text(
        "Todos os procedimentos de emergência têm cobertura integral sem pré-autorização, "
        "independente de carência. Justificativa médica obrigatória para reembolso."
    )

    if pdf.will_page_break(25):
        pdf.add_page()

    pdf.subsection_title("Acompanhamento Pós-Internação")
    pdf.normal_text(
        "Internações incluem até 2 consultas pós-alta (máximo 14 dias úteis cada) "
        "com o médico responsável, cobertas integralmente com autorização."
    )

    pdf.subsection_title("Cobertura de Exames Diagnósticos")
    pdf.normal_text(
        "Ressonância magnética (21 dias úteis), tomografia (21 dias úteis) "
        "e ultrassom diagnóstico (3 dias úteis) têm cobertura integral quando solicitados por médico especialista."
    )

    pdf.output(os.path.join(OUTPUT_DIR, "08_coberturas_especiais.pdf"))
    print("✓ 08_coberturas_especiais.pdf criado")

def create_politica_reembolso():
    """PDF 9: Política de Reembolso."""
    pdf = PDFVidaSaude()
    pdf.add_page()

    pdf.section_title("POLÍTICA DE REEMBOLSO")

    pdf.subsection_title("Quando Solicitar Reembolso")
    pdf.normal_text(
        "Reembolsos são processados quando procedimentos são realizados "
        "em prestadores não credenciados em situações de emergência comprovada."
    )

    pdf.subsection_title("Tabela de Reembolso")
    pdf.normal_text(
        "Reembolsos seguem tabela de honorários da ANS, ajustada mensalmente. "
        "Para urgência/emergência: até 100% dos custos comprovados."
    )

    pdf.subsection_title("Procedimento para Reembolso")
    procedimento = [
        "1. Solicite via portal ou central (0800 000 0000);",
        "2. Apresente: recibo, notas fiscais, prescrição médica;",
        "3. Auditoria analisa (máximo 10 dias úteis);",
        "4. Aprovação e depósito em conta (5 dias úteis após).",
    ]
    for item in procedimento:
        pdf.normal_text(item)

    if pdf.will_page_break(20):
        pdf.add_page()

    pdf.subsection_title("Documentação Necessária")
    docs = [
        "Recibo original ou nota fiscal;",
        "Prescrição médica com CRM visível;",
        "Comprovante de pagamento;",
        "Relatório médico justificando urgência.",
    ]
    for doc in docs:
        pdf.normal_text(f"• {doc}")

    pdf.output(os.path.join(OUTPUT_DIR, "09_politica_reembolso.pdf"))
    print("✓ 09_politica_reembolso.pdf criado")

def main():
    """Gera todos os PDFs."""
    print("Gerando PDFs da Vida+ Saúde com fonte Unicode...")
    create_rol_cobertura()
    create_regras_autorizacao()
    create_prazos_atendimento()
    create_faq_prestador()
    create_termos_condicoes()
    create_guia_beneficiario()
    create_procedimentos_cancelamento()
    create_coberturas_especiais()
    create_politica_reembolso()
    print(f"\n✓ PDFs gerados em: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
