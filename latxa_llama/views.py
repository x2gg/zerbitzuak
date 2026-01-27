import shutil
import concurrent
from urllib.parse import unquote
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .models import Kontsultak, EmaitzaFormatua
from .forms import LematizationInvitado, RegisterForm, LematizationForm, FileFieldForm
from .lematizatu import lemmatize_text
from .laguntzaileak import testu_sarrera, handle_uploaded_zip, txukundu_txt_apiarentzat, output_bateratua, output_bateratua_fitxategiak, save_uploaded_file, karpetak_sortu, doc_sarrera, txukundu_txt, txukundu_conll, txukundu_csv, txukundu_json, txukundu_pdf
from concurrent.futures import ThreadPoolExecutor
import os
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
from django.db.models import Q
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import os
import json

TSV_FITXATEGIAK = "lematizatzeko_fitxategiak"
OUTPUT = "output"
EMAITZAK = "emaitzak"
FITXATEGIAK = "fitxategi_guztiak"
OUTPUT_2 = "output_2"


# erregistro funtzioa
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        form2 = LematizationForm()
        form3 = FileFieldForm()
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return render(request, 'home.html', {'form': form2, 'form2': form3})
        else:
            error = _("Sartutako datuekin ez da posible erregistroa egitea.")
            return render(request, 'register.html', {'form': form, 'error': error}) 
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

#login funtzioa
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        form2 = LematizationForm()
        form3 = FileFieldForm()
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return render(request, 'home.html', {'form': form2, 'form2': form3})
        else:
            error = _("Erabiltzaile izena edo pasahitza ez dira zuzenak.")
            return render(request, 'login.html', {'form': form, 'error': error})
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

#saioa amaitu
@login_required
def user_logout(request):
    logout(request)
    form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def home(request):
    form2 = LematizationForm()
    form3 = FileFieldForm()
    return render(request, 'home.html', {'form': form2, 'form2': form3})

@login_required
def lematizatzailea_app(request):
    form2 = LematizationForm()
    form3 = FileFieldForm()
    return render(request, 'home.html', {'form': form2, 'form2': form3})

def invitado(request):
    form2 = LematizationForm()
    form3 = FileFieldForm()
    return render(request, 'invHome.html', {'form': form2, 'form2': form3})

#emaitza lortu, erabiltzaile erregistratuak
@login_required
def lortu_emaitza(request):
    if request.method == 'POST':
        form2 = FileFieldForm(request.POST, request.FILES)
        form = LematizationForm(request.POST)
        erroreak = []
        if form.is_valid(): 
            sOpt = form.cleaned_data.get('option') #sarrera mota
            iOpts = form.cleaned_data.get('options') #emaitza nola jaso nahi den
            if sOpt == 'text': # sarreran testua
                # testua tratatu
                testua = form.cleaned_data.get('text_area')
                if not testua.strip():
                    e1 = _("Ez duzu lematizatzeko edukirik sartu.")
                    erroreak.append(e1)

                testu_sarrera(testua)

                lematizatzeko_fitxateagiak = sorted(os.listdir(TSV_FITXATEGIAK))
                
                # lematizazioa esaldika
                for lem_f in lematizatzeko_fitxateagiak:
                    lemmatize_text(os.path.join(TSV_FITXATEGIAK, lem_f))

                #emaitza guztia fitxategi batean idatzi 
                output_bateratua()
                outputFin = os.listdir(OUTPUT_2)[0]
                testua_output = ""
                if not iOpts:
                    e2 = _("Aukeratu emaitza nola jaso nahi duzun.")
                    erroreak.append(e2)
                else:
                    txukundu_txt(os.path.join(OUTPUT_2, outputFin))
                    finalOut = os.listdir(EMAITZAK)[0]
                    source_path = os.path.join(EMAITZAK, finalOut)
                    destination_path = os.path.join(settings.MEDIA_EMAITZAK, finalOut)
                    if os.path.isfile(source_path):
                        shutil.move(source_path, destination_path)
                    emaitzaTxt = os.listdir(settings.MEDIA_EMAITZAK)[0]
                    print(emaitzaTxt)
                    with open(os.path.join(settings.MEDIA_EMAITZAK, emaitzaTxt), 'r') as f:
                        testua_output = f.read()
                    if '2' in iOpts: # emaitza pdf formatuan
                        txukundu_pdf(os.path.join(OUTPUT_2, outputFin))
                    if '3' in iOpts:  # emaitza csv formatuan
                        txukundu_csv(os.path.join(OUTPUT_2, outputFin))
                    if '4' in iOpts:  # emaitza conll formatuan
                        txukundu_conll(os.path.join(OUTPUT_2, outputFin))
                    if '5' in iOpts:  # emaitza json formatuan
                        txukundu_json(os.path.join(OUTPUT_2, outputFin))
                
                emaitzaFitxategiak = []
                emaitzaFitxategiak2 = []
                emaitzak_files = os.listdir(EMAITZAK)

                for fileN in emaitzak_files:
                    emaitzaFitxategiak2.append(fileN)
               
                for file_name in emaitzak_files:
                    source_path = os.path.join(EMAITZAK, file_name)
                    destination_path = os.path.join(settings.MEDIA_EMAITZAK, file_name)

                    if os.path.isfile(source_path):
                       
                        shutil.move(source_path, destination_path)
                       
                        emaitzaFitxategiak.append(f'emaitzak/{file_name}')
                emaitzaF = zip(emaitzaFitxategiak, emaitzaFitxategiak2)
                if not erroreak:
                    emaitza_formatua = EmaitzaFormatua(emaitza = iOpts)
                    emaitza_formatua.save()
                    if emaitza_formatua:
                        kontsulta = Kontsultak( #kontsula objetu bat sortu
                            user=request.user,  
                            inputText=testua,   
                            soluzioa=testua_output, 
                            emaitzaFormatua=emaitza_formatua  
                        )
                        kontsulta.save() #kontsulta datu basea gorde

                    #emaitza orrialdea erakutsi
                    if not '1' in iOpts:
                        return render(request, 'emaitzak.html', {'testua':testua, 'MEDIA_URL': settings.MEDIA_URL, 'testua_output': "", 'options':iOpts, 'emaitzaFitxategiak':emaitzaF, 'sarreraMota':sOpt})     
                    return render(request, 'emaitzak.html', {'testua':testua,  'MEDIA_URL': settings.MEDIA_URL, 'testua_output': testua_output, 'options':iOpts, 'emaitzaFitxategiak':emaitzaF, 'sarreraMota':sOpt})     
            
            elif sOpt == 'upload' and form2.is_valid(): # sarreran fitxategiak igo dira
                files = request.FILES.getlist('file_field') # erabiltzaileak igo dituen fitxategiak eskuratu
                if not files:
                    e3 = _("Ez duzu fitxategirik igo.")
                    erroreak.append(e3)
                else:
                    if not iOpts:
                        e4 = _("Aukeratu emaitza nola jaso nahi duzun.")
                        erroreak.append(e4)
                    else:
                        karpetak_sortu()
                        allowend_extensions = ['.pdf', '.txt', '.docx'] #onartzen diren formatuak
                        
                        # media karpetara mugitu
                        moved_files = [save_uploaded_file(file, FITXATEGIAK) for file in files]
                        moved_files_2 = [save_uploaded_file(file, settings.MEDIA_FITXATEGIAK) for file in files]

                        all_files_1 = list(moved_files)  # Start with files saved to FITXATEGIAK
                        all_files_2 = list(moved_files_2)

                        # igo diren fitxategiak aztertu
                        for mvFile in moved_files:
                            extension = os.path.splitext(mvFile)[1]
                            if extension == '.zip':
                                zfiles_1 = handle_uploaded_zip(mvFile, FITXATEGIAK, allowend_extensions)
                                zfiles_2 = handle_uploaded_zip(mvFile, settings.MEDIA_FITXATEGIAK, allowend_extensions)

                                all_files_1.extend(zfiles_1)
                                all_files_2.extend(zfiles_2)
                            elif extension.lower() not in allowend_extensions:
                                e8 = _("Solik testu fitxategiak onartzen dira.")
                                erroreak.append(e8)
                                form = LematizationForm()  
                                form2 = FileFieldForm()
                                return render(request, 'home.html', {'erroreak':erroreak, 'form': form, 'form2': form2})
                        
                        all_files_1 = [f for f in all_files_1 if os.path.splitext(f)[1] != '.zip']
                        all_files_2 = [f for f in all_files_2 if os.path.splitext(f)[1] != '.zip']
                        
                        #igo diren fitxategiak tratatu
                        for kont, moved_file in enumerate(all_files_1, start=1):
                            extension = os.path.splitext(moved_file)[1]
                            if not extension == '.zip':
                                doc_sarrera(moved_file)
                            
                            lematizatzeko_fitxateagiak = os.listdir(TSV_FITXATEGIAK)
                            for lem_f in lematizatzeko_fitxateagiak:
                                lemmatize_text(os.path.join(TSV_FITXATEGIAK, lem_f))
                            
                            output_bateratua_fitxategiak(kont)
                            

                        testua_output = ""
                       
                        fitxategiakOut2 = os.listdir(OUTPUT_2)
                        if len(fitxategiakOut2) > 1 and '1' in iOpts:
                            e5 = _("Fitxategi bat baino gehiago lematizatzea nahi baduzu, emaitza ezin duzu pantailan jaso.")
                            erroreak.append(e5)
                        elif len(fitxategiakOut2) == 1 and '1' in iOpts:
                            txukundu_txt(os.path.join(OUTPUT_2, fitxategiakOut2[0]))
                            txtEmaitza = os.listdir(EMAITZAK)[0]
                            with open(os.path.join(EMAITZAK, txtEmaitza), 'r') as f:
                                testua_output = f.read()

                        if '2' in iOpts: #emaitza pdf
                            for fileOut2 in fitxategiakOut2:
                                txukundu_pdf(os.path.join(OUTPUT_2, fileOut2))
                        if '3' in iOpts: #emaitza csv
                            for fileOut2 in fitxategiakOut2:
                                txukundu_csv(os.path.join(OUTPUT_2, fileOut2))
                        if '4' in iOpts: #emaitza conll
                            for fileOut2 in fitxategiakOut2:
                                txukundu_conll(os.path.join(OUTPUT_2, fileOut2))
                        if '5' in iOpts: #emaitza json
                            for fileOut2 in fitxategiakOut2:
                                txukundu_json(os.path.join(OUTPUT_2, fileOut2))

                        
                        emaitzaFitxategiak = []
                        emaitzaFitxategiak2 = []
                        emaitzak_files = os.listdir(EMAITZAK)
                        
                        # emaitza fitxategiak gero erakustea posible izan dadin media karpetan gorde
                        for fileN in emaitzak_files:
                            emaitzaFitxategiak2.append(fileN)
                        for file_name in emaitzak_files:
                            source_path = os.path.join(EMAITZAK, file_name)
                            destination_path = os.path.join(settings.MEDIA_EMAITZAK, file_name)
                            if os.path.isfile(source_path):
                                shutil.move(source_path, destination_path)
                                emaitzaFitxategiak.append(f'/emaitzak/{file_name}')
                        
                        emaitzaF = zip(emaitzaFitxategiak, emaitzaFitxategiak2)
                        if not erroreak:
                            # emaitza orrialdera bideratu erabiltzailea
                            return render(request, 'emaitzak.html', {'testua_output': testua_output, 'MEDIA_URL': settings.MEDIA_URL, 'emaitzaFitxategiak': emaitzaF, 'options':iOpts, 'sarrera_files': [os.path.basename(f) for f in moved_files_2], 'sarreraMota':sOpt})

       
            else: #form2 is not valid
                e6 = _("Formulario okerra.")
                erroreak.append(e6)
        else: #form is not valid
            e7 = _("Formulario okerra.")
            erroreak.append(e7)
    else: 
        form = LematizationForm()  
        form2 = FileFieldForm()

    if erroreak:
        form = LematizationForm()  
        form2 = FileFieldForm()
        return render(request, 'home.html', {'erroreak':erroreak, 'form': form, 'form2': form2})
    
    return render(request, 'emaitzak.html')

#erabiltzaile gonbidatuentzat lematizazioa
def emaitzak_invitado(request):
    if request.method == 'POST':
        form = LematizationInvitado(request.POST)
        erroreak = []
        print("post")
        if form.is_valid():
            print("form")
            # testua tratatu
            testua = form.cleaned_data.get('text_area')
            if not testua.strip():
                e1 = _("Ez duzu lematizatzeko edukirik sartu.")
                erroreak.append(e1)

            #testua tratatzeko prestatu
            testu_sarrera(testua)
            lematizatzeko_fitxateagiak = os.listdir(TSV_FITXATEGIAK)
            
            #lematizazioa esaldika
            for lem_f in lematizatzeko_fitxateagiak:
                lemmatize_text(os.path.join(TSV_FITXATEGIAK, lem_f))

            #emaitza fitxategi bakar batean idatzi                  
            output_bateratua()
            outputFin = os.listdir(OUTPUT_2)[0]
            testua_output = ""

            txukundu_txt(os.path.join(OUTPUT_2, outputFin)) #txt emaitza sortu, gero hori irakurri eta erakusteko
            finalOut = os.listdir(EMAITZAK)[0]
            source_path = os.path.join(EMAITZAK, finalOut)
            destination_path = os.path.join(settings.MEDIA_EMAITZAK, finalOut)
            if os.path.isfile(source_path):
                shutil.move(source_path, destination_path)
                
            emaitzaTxt = os.listdir(settings.MEDIA_EMAITZAK)[0]
            with open(os.path.join(settings.MEDIA_EMAITZAK, emaitzaTxt), 'r') as f:
                testua_output = f.read()
                                    
            if not erroreak:
                return render(request, 'invEmaitzak.html', {'testua':testua, 'testua_output': testua_output})     

    else:
        form = LematizationForm()  
    return render(request, 'invHome.html', { 'form': form})
    


import requests
import os
import shutil
from urllib.parse import unquote
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

#switchboardetik gure tresnaren atzipena kontrolatzeko funtzioa
@csrf_exempt
def emaitzak_invitado_switchboard(request):
    if request.method == 'GET':  
        try:
            data_url = request.GET.get('data', '').strip() #data atributuko informazioa eskuratu
            if not data_url:
                return JsonResponse({'error': 'Ez duzu datu URLrik sartu.'}, status=400)

            decoded_url = unquote(data_url) # data atributuko informazioa erabilgarri bihurtu

            response = requests.get(decoded_url)
            if response.status_code != 200:
                return JsonResponse({'error': 'Ezin izan da testua deskargatu.'}, status=400)

            text = response.text.strip() # erabiltzaileak switchboardean kargatu duen edukia eskuratu
            if not text:
                return JsonResponse({'error': 'Deskargatutako fitxategia hutsik dago.'}, status=400)

            #edukia tratatu
            testu_sarrera(text)
            lematizatzeko_fitxateagiak = os.listdir(TSV_FITXATEGIAK)
            
            for lem_f in lematizatzeko_fitxateagiak:
                lemmatize_text(os.path.join(TSV_FITXATEGIAK, lem_f))
                                
            output_bateratua()
            outputFin = os.listdir(OUTPUT_2)[0]
            testua_output = ""

            txukundu_txt(os.path.join(OUTPUT_2, outputFin))
            finalOut = os.listdir(EMAITZAK)[0]
            source_path = os.path.join(EMAITZAK, finalOut)
            destination_path = os.path.join(settings.MEDIA_EMAITZAK, finalOut)
            if os.path.isfile(source_path):
                shutil.move(source_path, destination_path)
                
            emaitzaTxt = os.listdir(settings.MEDIA_EMAITZAK)[0]
            with open(os.path.join(settings.MEDIA_EMAITZAK, emaitzaTxt), 'r') as f:
                testua_output = f.read()

            # Store results in the session
            request.session['testua'] = text
            request.session['testua_output'] = testua_output

            # Redirect to the result page
            return redirect('emaitzak_page')  

        except Exception as e:
            return JsonResponse({'error': f'Unexpected error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Only GET method is allowed.'}, status=405)


def render_emaitzak_page_switchboard(request):
    # Retrieve processed text from the session
    testua = request.session.get('testua', '')
    testua_output = request.session.get('testua_output', '')

    return render(request, 'invEmaitzak.html', {'testua': testua, 'testua_output': testua_output})

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

#lematizazioa API. Endpoint batera deia egin, ta emaitza zuzenean JSON formatuan jasotzea ahalbidetzen duen funtzioa
@csrf_exempt  
@require_http_methods(["POST"]) 
def lematizaioa_api(request):
    try:
        # Parse the JSON body
        body = json.loads(request.body.decode('utf-8')) #POST eskaeraren body
        text = body.get('text', '').strip() # eskaerako body-tik text atributuko edukia eskuratu
        if not text:
            return JsonResponse({'error': 'No text provided for lemmatization'}, status=400)
        
        #bidalitako edukia tratatu
        testu_sarrera(text)
        lematizatzeko_fitxateagiak = os.listdir(TSV_FITXATEGIAK)
            
        for lem_f in lematizatzeko_fitxateagiak:
            lemmatize_text(os.path.join(TSV_FITXATEGIAK, lem_f))
                                
        output_bateratua()
        outputFin = os.listdir(OUTPUT_2)[0]
        

        #json formatuko emaitza sortu
        emaitzajson = txukundu_txt_apiarentzat(os.path.join(OUTPUT_2, outputFin))
        
        return JsonResponse({'emaitza': emaitzajson})

    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

#kontsultak datu basetik eskuratzeko funtzioa
@login_required
def kontsultak_ikusi(request):
    query = request.GET.get('search', '')  
    sort_by = request.GET.get('sort_by', 'kontsulta_data') 
    order = request.GET.get('order', 'asc')  
  
    if order == 'desc':
        sort_by = f'-{sort_by}'  
    
    kontsultak_list = Kontsultak.objects.filter(user=request.user)

    if query:
        kontsultak_list = kontsultak_list.filter(
            Q(inputText__icontains=query) | 
            Q(kontsulta_data__icontains=query)
        )
    
    kontsultak_list = kontsultak_list.order_by(sort_by)

    paginator = Paginator(kontsultak_list, 10)
    page_number = request.GET.get('page')
    kontsultak = paginator.get_page(page_number)

    return render(request, 'historiala.html', {
        'kontsultak': kontsultak,
        'search': query,
        'sort_by': sort_by.lstrip('-'),  
        'order': order
    })

@login_required
def delete_kontsulta(request, kontsulta_id):
    kontsulta = get_object_or_404(Kontsultak, id=kontsulta_id, user=request.user) #kontsulta bilatu ta berreskuratu edo 404 errorea
    kontsulta.delete() #kontsulta ezabatu
    return render(request, 'kontsulta_ezabatua.html', {'kontsulta': kontsulta})
    
    




