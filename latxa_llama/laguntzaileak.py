import json
import os
import shutil
import PyPDF2
from django.conf import settings
import docx
import re
import csv
import ast
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.utils.translation import gettext_lazy as _

TSV_FITXATEGIAK = "lematizatzeko_fitxategiak"
OUTPUT = "output"
EMAITZAK = "emaitzak"
FITXATEGIAK = "fitxategi_guztiak"
OUTPUT_2 = "output_2"



def amaiera():
    # Exekuzioa amaitzean karpetak ezbatu. Gero hasieran berriz sortzen dira.
    shutil.rmtree(TSV_FITXATEGIAK, ignore_errors=True)
    shutil.rmtree(OUTPUT, ignore_errors=True)
    shutil.rmtree(EMAITZAK, ignore_errors=True)
    shutil.rmtree(FITXATEGIAK, ignore_errors=True)


# Emaitza fitxategia pdf formatuan sortzeko
def txukundu_pdf(input_file):

    with open(input_file, "r", encoding='utf-8') as reader:
        lines = reader.readlines()

    
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    namef = f"{base_name}.pdf"
    emaitza = os.path.join(EMAITZAK, namef)

    
    pdf = SimpleDocTemplate(emaitza, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    story = []  

   
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['BodyText']
    error_style = styles['Italic']

   
    title = Paragraph("LEMATIZAZIOA", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))  

    
    table_data = []
    table_data.append([_('Oinarrizko hitza'),_('Dagokion lema')])  

    for line in lines:
        try:
            name, form = line.split(' ', 1)
        except ValueError:
            table_data.append([name, "ERROR"])
            continue
        try:   
            lemma = _apply_lemma_rule(name, form.strip())
            table_data.append([name, lemma])
        except ValueError as ve:
               
            print(f"Error processing the line: {line} -> {ve}")
            table_data.append([name, "ERROR"])

    
    table = Table(table_data, colWidths=[2 * inch, 4 * inch])
    
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    story.append(table)

    
    pdf.build(story)

# Emaitza fitxategia txt formatuan sortzeko
def txukundu_txt(input_file):
    
    with open(input_file, "r", encoding='utf-8') as reader:
        lines = reader.readlines()

   
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    namef = f"{base_name}.txt"
    emaitza = os.path.join(EMAITZAK, namef)

    
    with open(emaitza, mode='w', encoding='utf-8') as txtfile:
        formatted_string = _('Oinarrizko hitza --> Dagokion lema \n\n')
        txtfile.write(str(formatted_string))
        for line in lines:
            try:   
                name, form = line.split(' ', 1)
            except ValueError:
                txtfile.write(f"{name} ERROR\n")
                continue
            try:        
                lemma = _apply_lemma_rule(name, form.strip())
                txtfile.write(f"{name} --> {lemma}\n")
            except ValueError as ve:
                    
                print(f"Error al procesar la línea: {line} -> {ve}")
                txtfile.write(f"{name} ERROR\n")

def txukundu_txt_apiarentzat(input_file):
    word_lemma_dict = {}  
    
    with open(input_file, "r", encoding='utf-8') as reader:
        lines = reader.readlines()

    for line in lines:
        try:   
            name, form = line.split(' ', 1)
        except ValueError:
            word_lemma_dict[name] = 'ERROR'  
            continue
        
        try:        
            lemma = _apply_lemma_rule(name, form.strip())
            word_lemma_dict[name] = lemma  
        except ValueError as ve:
            print(f"Error al procesar la línea: {line} -> {ve}")
            word_lemma_dict[name] = 'ERROR'  

    return word_lemma_dict  

# Emaitza fitxategia csv formatuan sortzeko
def txukundu_csv(input_file):
    
    with open(input_file, "r", encoding='utf-8') as reader:
        lines = reader.readlines()

    
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    namef = f"{base_name}.csv"
    emaitza = os.path.join(EMAITZAK, namef)

    _('Oinarrizko hitza'),_('Dagokion lema')
    datos = [
        [_('Oinarrizko hitza'),_('Dagokion lema')], 
    ]

   
    for line in lines:
        try:
            name, form = line.split(' ', 1)
        except ValueError:
            datos.append([name, "ERROR"])
            continue

        try:       
            lemma = _apply_lemma_rule(name, form.strip())
            datos.append([name, lemma])
        except ValueError as ve:
               
            print(f"Error al procesar la línea: {line} -> {ve}")
            datos.append([name, "ERROR"])

    with open(emaitza, mode='w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';') 
        csvwriter.writerows(datos)

# Emaitza fitxategia conll formatuan sortzeko
def txukundu_conll(input_file):


    with open(input_file, "r", encoding='utf-8') as reader:
        lines = reader.readlines()

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    namef = f"{base_name}.conll"
    emaitza = os.path.join(EMAITZAK, namef)

    with open(emaitza, mode='w', encoding='utf-8') as conllfile:
        conllfile.write("# ID\tFORM\tLEMMA\tPOS\tHEAD\tDEPREL\n")
        kont = 0
        
        for line in lines:
            kont = kont + 1
            try:
                name, form = line.split(' ', 1)
            except ValueError:
                conllfile.write(f"{kont}\t{name}\tERROR\t_\t_\t_\n")
                continue
            try:
                lemma = _apply_lemma_rule(name, form.strip())
                conllfile.write(f"{kont}\t{name}\t{lemma}\t_\t_\t_\n")
            except ValueError as ve:
                print(f"Error processing line: {line} -> {ve}")
                conllfile.write(f"{kont}\t{name}\ttERROR\t_\t_\t_\n")

# Emaitza fitxategia json formatuan sortzeko
def txukundu_json(input_file):
    with open(input_file, "r", encoding='utf-8') as reader:
        lines = reader.readlines()

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    namef = f"{base_name}.json"
    emaitza = os.path.join(EMAITZAK, namef)

    documents = []

    kont = 0

    for line in lines:
        kont += 1
        try:
            name, form = line.split(' ', 1)
        except ValueError:
            documents.append({
                "id": kont,
                "text": name,
                "lemma": "ERROR",
                #"pos": "_",
                #"tag": "_",
                #"dep": "_",
                "shape": name,
                "is_alpha": name.isalpha()
                #"is_stop": False
            })
            continue
 
        try:
            lemma = _apply_lemma_rule(name, form.strip())

            token_info = {
                "id": kont,
                "text": name,
                "lemma": lemma,
                #"pos": "_", 
                #"tag": "_", 
                #"dep": "_", 
                "shape": name,
                "is_alpha": name.isalpha()
                #"is_stop": False 
            }
            documents.append(token_info)
        except ValueError as ve:
            print(f"Error al procesar la línea: {line} -> {ve}")
            documents.append({
                "id": kont,
                "text": name,
                "lemma": "ERROR",
                #"pos": "_",
                #"tag": "_",
                #"dep": "_",
                "shape": name,
                "is_alpha": name.isalpha()
                #"is_stop": False
            }) 

    with open(emaitza, mode='w', encoding='utf-8') as jsonfile:
        json.dump(documents, jsonfile, ensure_ascii=False, indent=4)

# pdfak irakurtzeko funtzioa
def read_pdf(file_path):
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in range(len(reader.pages)):
                text += reader.pages[page].extract_text()  
            return text.strip()  
    except Exception:
        return ""

# docx formatuko fitxategiak irakurtzeko funtzioa
def read_docx(file_path):
    try:
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text]).strip()  
    except Exception:
        return ""

# txt formatuko fitxategiak irakurtzeko funtzioa
def read_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read().strip()  
    except Exception:
        return ""

# karpeta desberdinak batera sortzeko funtzioa    
def karpetak_sortu():
    karpeta_sortu(FITXATEGIAK)
    karpeta_sortu(TSV_FITXATEGIAK)
    karpeta_sortu(OUTPUT)
    karpeta_sortu(EMAITZAK)
    karpeta_sortu(OUTPUT_2)
    karpeta_sortu(settings.MEDIA_EMAITZAK)
    karpeta_sortu(settings.MEDIA_FITXATEGIAK)
    
# sarrera fitxategia denean, eduki hori lematizatzeko prestatzeko funtzioa
def doc_sarrera(file_path):
    if not file_path:
        return
    karpeta_sortu(TSV_FITXATEGIAK)
    karpeta_sortu(OUTPUT)

    file_name = os.path.basename(file_path)
    base_name, ext = os.path.splitext(file_name)

    if ext.lower() == '.pdf':
        content = read_pdf(file_path)
    elif ext.lower() == '.docx':
        content = read_docx(file_path)
    elif ext.lower() == '.txt':
        content = read_txt(file_path)
    else:
        return  

    phrases = re.split(r'(?<=[.!?]) +', content.strip())
    for kont, phrase in enumerate(filter(bool, map(str.strip, phrases))):  
        tsv_file_path = os.path.join(TSV_FITXATEGIAK, f"{base_name}_{kont}.tsv")
        words = re.findall(r'\w+', phrase) 

        if words:
            with open(tsv_file_path, 'w', encoding='utf-8') as tsv_file:
                tsv_file.write("text\n")
                tsv_file.write("\n".join(words))
                tsv_file.write("\n")

# sarrera testua denean, eduki hori lematizatzeko prestatzeko funtzioa    
def testu_sarrera(testua):
    if testua:
        karpeta_sortu(FITXATEGIAK)
        karpeta_sortu(TSV_FITXATEGIAK)
        karpeta_sortu(OUTPUT)
        karpeta_sortu(EMAITZAK)
        karpeta_sortu(OUTPUT_2)
        karpeta_sortu(settings.MEDIA_EMAITZAK)
        karpeta_sortu(settings.MEDIA_FITXATEGIAK)
        kont = 0
        
        phrases = re.split(r'(?<=[.!?]) +', testua.strip())
        for phrase in phrases:
            if not phrase.strip():
                continue

            tsv_file_path = os.path.join(TSV_FITXATEGIAK, f"input_text_{kont}.tsv")
            kont += 1
            words = re.findall(r'\w+', phrase)  
            if words:
                with open(tsv_file_path, 'w', encoding='utf-8') as tsv_file:
                    tsv_file.write("text")
                    tsv_file.write("\n")
                    
                    for word in words:
                        tsv_file.write(f"{word}\n")  
                    tsv_file.write("\n") 

# emaitza fitxategi desberdinak batera jartzeko funtzioa, sarrera testua denean
def output_bateratua():
    o_files = os.listdir(OUTPUT)
    
    # Sort files by the numerical value in their names
    def extract_number(file_name):
        match = re.search(r'_(\d+)_', file_name)  
        return int(match.group(1)) if match else float('inf')  
    
    sorted_files = sorted(o_files, key=extract_number)
    
    
    final_output = os.path.join(OUTPUT_2, "finalOut.tsv")  
    with open(final_output, 'w', encoding='utf-8') as outfile:
        for file_name in sorted_files:
            file_path = os.path.join(OUTPUT, file_name)
            if os.path.isfile(file_path):     
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)

# emaitza fitxategi desberdinak batera jartzeko funtzioa, sarreran fitxategiak daudenean
def output_bateratua_fitxategiak(kont):
    o_files = sorted(os.listdir(OUTPUT))
    final_output = os.path.join(OUTPUT_2, f"outfile_s{kont}.tsv")  
    with open(final_output, 'w', encoding='utf-8') as outfile:
        for file_name in o_files:
            file_path = os.path.join(OUTPUT, file_name)
            if os.path.isfile(file_path):     
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)

# karpeta bat sortzeko funtzioa
def karpeta_sortu(karpeta):
    folder_path = os.path.abspath(karpeta)
    if os.path.exists(folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  
    else:
        os.makedirs(folder_path)


# emaitza interpretatzeko funtzioa. 
#Hitz bakoitza nola lematizatzen den adierazten duen kodea interpretatu, eta oinarrizko forma lortu
def _apply_lemma_rule(form, lemma_rule):
    if ';' not in lemma_rule:
        raise ValueError('lemma_rule %r for form %r missing semicolon' % (lemma_rule, form))
    
    casing, rule = lemma_rule.split(";", 1)
    
    if rule.startswith("a"):
        lemma = rule[1:]
    else:
        form = form.lower()
        rules, rule_sources = rule[1:].split("¦"), []
        
        assert len(rules) == 2
        for rule in rules:
            source, i = 0, 0
            while i < len(rule):
                if rule[i] == "→" or rule[i] == "-":
                    source += 1
                else:
                    assert rule[i] == "+"
                    i += 1
                i += 1
            rule_sources.append(source)

        lemma, form_offset = "", 0
        for i in range(2):
            j, offset = 0, (0 if i == 0 else len(form) - rule_sources[1])
            while j < len(rules[i]):
                if rules[i][j] == "→":
                    lemma += form[offset]
                    offset += 1
                elif rules[i][j] == "-":
                    offset += 1
                else:
                    assert (rules[i][j] == "+")
                    lemma += rules[i][j + 1]
                    j += 1
                j += 1
            if i == 0:
                lemma += form[rule_sources[0]: len(form) - rule_sources[1]]

    for rule in casing.split("¦"):
        if rule == "↓0":
            continue  # The lemma is lowercased initially
        if not rule:
            continue  # Empty lemma might generate empty casing rule
        case, offset = rule[0], int(rule[1:])
        lemma = lemma[:offset] + (lemma[offset:].upper() if case == "↑" else lemma[offset:].lower())
        
    return lemma

# fitxategi bat adierazten den karpeta horretan gordetzeko
def save_uploaded_file(file, destination_dir):
   
    os.makedirs(destination_dir, exist_ok=True)

   
    destination_path = os.path.join(destination_dir, file.name)

    
    with open(destination_path, 'wb') as destination:
        for chunk in file.chunks():  
            destination.write(chunk)

    return destination_path

import zipfile
from pathlib import Path

import os
import zipfile

# zip fitxategiak kontrolatzeko
def handle_uploaded_zip(zip_file, extract_to, allowed_extensions):

    extracted_files = []

    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            for file_info in zf.infolist():
                file_name = os.path.basename(file_info.filename)  # Get the base file name (ignores folders)
                file_extension = os.path.splitext(file_name)[1].lower()

                # Check if the file extension is allowed
                if file_extension in allowed_extensions and file_name:
                    # Ensure the extraction directory exists
                    if not os.path.exists(extract_to):
                        os.makedirs(extract_to)
                    
                    # Define the full path for the extracted file
                    extracted_path = os.path.join(extract_to, file_name)

                    # Extract the file content and write it directly to the target path
                    with zf.open(file_info) as source_file, open(extracted_path, 'wb') as target_file:
                        target_file.write(source_file.read())
                    
                    extracted_files.append(extracted_path)
                else:
                    print(f"Skipped {file_info.filename}: Unallowed file extension or empty file name")
    except zipfile.BadZipFile:
        print("The uploaded file is not a valid zip file.")
    
    return extracted_files



