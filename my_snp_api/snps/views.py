from django.shortcuts import render
from django.conf import settings as conf_settings
from django.contrib import messages
from .forms import CsvModelForm
from .forms import TxtModelForm
from .forms import TraitModelForm
from .forms import PvalueModelForm
from .forms import AncestryModelForm
from .forms import RefPopulationModelForm
from .models import Genome
from .models import Csv
from .models import Txt
from .models import TraitChoice
from .models import PvalueChoice
from .models import AncestryChoice
from .models import RefPopulationChoice
from .models import GWAS
from .models import PHEGENI
from .models import Ancestry
from .models import FREQUENCY
import csv
import json
import pandas as pd
import os
import glob
import time
import warnings
import numpy as np
from django.http import HttpResponse
from django.http import HttpResponseRedirect
#from django.urls import reverse
from django.http import JsonResponse
from django.utils.datastructures import MultiValueDict

def cleanMedia(path,hours,extension):
    filelist_csv = glob.glob(os.path.join(path, "*." + extension))
    now = time.time()
    for f_csv in filelist_csv:
        if ((time.time() - os.stat(f_csv).st_mtime) > (3600 * hours)):
            try:
                os.remove(f_csv)
            except FileNotFoundError:
                True

def initChoices():
    traits_count_df_recomputed = pd.read_csv(os.path.join(conf_settings.BASE_DIR.parent, 'static/work/Traits_writeoff_recomputed.csv'), index_col=0)
    traits_count_df_recomputed = traits_count_df_recomputed[traits_count_df_recomputed['trait_count']>=2]
    traits_count_df_recomputed['trait'] = traits_count_df_recomputed.index
    traits_count_df_recomputed['activated'] = False
    df_records = traits_count_df_recomputed.to_dict('records')
    TraitChoice.objects.all().delete()
    model_instances = [TraitChoice(trait=record['trait'], count=record['trait_count'], activated=record['activated'], ) for
                       record in df_records]
    TraitChoice.objects.bulk_create(model_instances)

    PvalueChoice.objects.all().delete()
    pvaluechoice_file = open(os.path.join(conf_settings.BASE_DIR.parent, 'static/input/PvalueChoice'))
    pvaluechoices = pvaluechoice_file.read()
    pvalues_str = pvaluechoices.splitlines()
    pvalues_list = [float(x) for x in pvalues_str]
    pvaluechoice_file.close()
    for i in pvalues_list:
        PvalueChoice.objects.create(pvalue=i, activated=False)

    RefPopulationChoice.objects.all().delete()
    RefPopulationChoice_file = open(os.path.join(conf_settings.BASE_DIR.parent, 'static/input/RefPopulationChoice'))
    refpopchoices = RefPopulationChoice_file.read()
    refpop_str = refpopchoices.splitlines()
    RefPopulationChoice_file.close()
    for population in refpop_str:
        RefPopulationChoice.objects.create(population=population)

    return

def upload_file_view(request):
    if not request.session.session_key:
        request.session.create()
        request.session['numSuccessUploads'] = 0
    if (request.method == 'POST'):
        warnings.simplefilter(action='ignore', category=FutureWarning)
        request.session.flush()
        request.session.create()
        request.session['numSuccessUploads'] = 0
        form_csv = CsvModelForm(request.POST or None, request.FILES or None)
        file_csv = request.FILES.getlist('upload_ancestry_file')[0]
        file_extension_csv = str(file_csv).split('.')[-1]
        request.session['numSuccessUploads'] = 0
        cleanup_frequency = float(os.environ.get('CLEANUP_FREQUENCY_HOURS'))
        if (file_extension_csv == 'csv'):
            form_csv = CsvModelForm(request.POST or None, MultiValueDict({'upload_ancestry_file': [file_csv]}) or None)
            if form_csv.is_valid():
                cleanMedia(conf_settings.MEDIA_ROOT + '/csvs/', cleanup_frequency, "csv")
                form_csv.save()
                if 'numSuccessUploads' in request.session:
                    request.session['numSuccessUploads'] += 1

        form_txt = TxtModelForm(request.POST or None, request.FILES or None)
        file_txt = request.FILES.getlist('upload_genome_file')[0]
        file_extension_txt = str(file_txt).split('.')[-1]
        if (file_extension_txt == 'txt'):
            form_txt = TxtModelForm(request.POST or None, MultiValueDict({'upload_genome_file': [file_txt]}) or None)
            if form_txt.is_valid():
                cleanMedia(conf_settings.MEDIA_ROOT + '/txts/', cleanup_frequency, "txt")
                form_txt.save()
                if 'numSuccessUploads' in request.session:
                    request.session['numSuccessUploads'] += 1

        if (('numSuccessUploads' in request.session) & (request.session['numSuccessUploads']==2)):
            cleanMedia(conf_settings.MEDIA_ROOT + '/', cleanup_frequency, "csv")
            genome_file_path = conf_settings.MEDIA_ROOT + '/txts/' + str(file_txt)
            ancestry_file_path = conf_settings.MEDIA_ROOT + '/csvs/' + str(file_csv)
            request.session['ancestry_file_path'] = ancestry_file_path
            #for path, subdirs, files in os.walk(conf_settings.MEDIA_ROOT):
            #    for name in files:
            #        print(os.path.join(path, name))
            try:
                Ancestry.get_master_23andme(request=request,ancestry_path=ancestry_file_path,genome_path=genome_file_path)
            except:
                messages.info(request,"There seems to be something wrong with the files. Please try uploading different files..")
                request.session.flush()
                request.session.create()
                request.session['numSuccessUploads'] = 0
                form_txt = TxtModelForm()
                form_csv = CsvModelForm()
                return render(request, 'upload.html', {'form_csv': form_csv, 'form_txt': form_txt, 'nbar': 'upload'})
            if (os.environ.get('SETUP_DATABASE_FLAG') == 'True'):
                FREQUENCY.master_frequency(genome_file_path)
                GWAS.objects.all().delete()
                PHEGENI.objects.all().delete()
                GWAS.parseTraits(path=os.path.join(conf_settings.BASE_DIR.parent,'static/input/gwas_catalog_v1.0.2-associations_e100_r2021-03-25.csv'))
                PHEGENI.parseTraits(file=os.path.join(conf_settings.BASE_DIR.parent, 'static/input/PheGenI_Association_full.tab'))
                initChoices()

            _ = parse_master(request)
            messages.info(request,"Files uploaded successfully! Your results are ready. You can see them in the View Results tab.")
        else:
            messages.info(request,"There is something wrong with the files. Please try uploading different files..")

    elif (request.method == 'GET'):
        pd.set_option('display.float_format', '{:.2E}'.format)
        form_txt = TxtModelForm()
        form_csv = CsvModelForm()
    return render(request, 'upload.html', {'form_csv': form_csv, 'form_txt': form_txt,'nbar':'upload'})

def displayFAQ(request):
    if not request.session.session_key:
        request.session.create()
        request.session['numSuccessUploads'] = 0
    return render(request, 'faq.html', {'nbar':'FAQ'})

def parse_master(request):
    Master_file_default = os.path.join(conf_settings.BASE_DIR.parent,'static/work/Master_file_default.csv')
    Master_file_user = conf_settings.MEDIA_ROOT + '/temp_master_' + str(request.session.session_key) + '.csv'
    if((os.environ.get('SETUP_DATABASE_FLAG'))=='False'):
        if (not os.path.isfile(Master_file_user)):
            if ('numSuccessUploads' in request.session):
                if (request.session['numSuccessUploads'] == 2):
                    df_master = get_master(request)

                    traits_writeoff_df_manual = pd.read_csv(
                        os.path.join(conf_settings.BASE_DIR.parent, 'static/work/Traits_writeoff_manual.csv'), index_col=0)
                    master_df_overriden = pd.merge(df_master, traits_writeoff_df_manual, how='left', left_on='trait',
                                                   right_index=True)
                    master_df_overriden['trait'] = np.where(~master_df_overriden['writeoff'].isnull(),
                                                            master_df_overriden['writeoff'], master_df_overriden['trait'])
                    del df_master
                    traits_count_df_recomputed = master_df_overriden[master_df_overriden['trait'].notna()].groupby(
                        ['trait', 'writeoff'], dropna=False).size().reset_index(name='Size')
                    traits_count_df_recomputed = traits_count_df_recomputed[
                        (~traits_count_df_recomputed['writeoff'].isnull()) | (traits_count_df_recomputed['Size'] >= 20)]
                    traits_count_df_recomputed = traits_count_df_recomputed.sort_values(by='Size', ascending=False)
                    traits_count_df_recomputed = traits_count_df_recomputed.rename(columns={'Size': "trait_count"})
                    traits_count_df_recomputed = traits_count_df_recomputed.set_index('trait')

                    master_df_overriden_recomputed = pd.merge(master_df_overriden, traits_count_df_recomputed, how='left',
                                                              left_on='trait', right_index=True)
                    del traits_count_df_recomputed
                    master_df_overriden_recomputed = master_df_overriden_recomputed.drop(['trait_count_x', 'writeoff_x'],
                                                                                         axis=1)
                    master_df_overriden_recomputed = master_df_overriden_recomputed.rename(
                        columns={"trait_count_y": "trait_count", "writeoff_y": "writeoff"})

                    master_df_overriden_recomputed = master_df_overriden_recomputed[
                        (master_df_overriden_recomputed['trait_count'] >= 20) | (
                            ~master_df_overriden_recomputed['writeoff'].isnull())]
                    master_df_overriden_recomputed = master_df_overriden_recomputed.sort_values(by=['trait_count'],
                                                                                                ascending=False)

                    master_df_overriden = master_df_overriden_recomputed[['rsid','SNP','Ancestry_copy1','Ancestry_copy2','trait','pvalue','trait_count',
                                                               'European','AfroCaribbean','LatinAmerican','Other','African','AfroAmerican',
                                                               'Asian','SouthAsian','EastAsian','OtherAsian','World','Count']]
                    del master_df_overriden_recomputed
                    master_df_overriden.to_csv(Master_file_user)
                    return master_df_overriden
                else:
                    master_df_overriden = pd.read_csv(Master_file_default, index_col=0)
                    return master_df_overriden
            else:
                master_df_overriden = pd.read_csv(Master_file_default, index_col=0)
                return master_df_overriden
        else:
            master_df_overriden = pd.read_csv(Master_file_user, index_col=0)
            return master_df_overriden
    else:
        if 'Master_file_default_created_flag' in request.session:
            master_df_overriden = pd.read_csv(Master_file_default, index_col=0)
            return master_df_overriden
        if (os.path.isfile(Master_file_default)):
            if ('numSuccessUploads' in request.session):
                if (request.session['numSuccessUploads'] < 2):
                    master_df_overriden = pd.read_csv(Master_file_default, index_col=0)
                    return master_df_overriden
            else:
                print('numSuccessUploads not found in request.session')

        df_master = get_master(request)
        path_TraitsCount = os.path.join(conf_settings.BASE_DIR.parent, 'static/input/TraitsCount.csv')
        if not os.path.isfile(path_TraitsCount):
            traits_count_df = df_master[df_master['trait'].notna()]['trait'].to_frame().groupby(
                'trait').size().to_frame()
            traits_count_df = traits_count_df.sort_values(by=[0], ascending=False)
            traits_count_df = traits_count_df.rename(columns={0: "trait_count"})
            traits_count_df.to_csv(path_TraitsCount)

        traits_writeoff_df_manual = pd.read_csv(
            os.path.join(conf_settings.BASE_DIR.parent, 'static/work/Traits_writeoff_manual.csv'),
            index_col=0)
        master_df_overriden = pd.merge(df_master, traits_writeoff_df_manual, how='left', left_on='trait',
                                       right_index=True)
        master_df_overriden['trait'] = np.where(~master_df_overriden['writeoff'].isnull(),
                                                master_df_overriden['writeoff'], master_df_overriden['trait'])
        del df_master
        traits_count_df_recomputed = master_df_overriden[master_df_overriden['trait'].notna()].groupby(
            ['trait', 'writeoff'], dropna=False).size().reset_index(name='Size')
        traits_count_df_recomputed = traits_count_df_recomputed[
            (~traits_count_df_recomputed['writeoff'].isnull()) | (traits_count_df_recomputed['Size'] >= 20)]
        traits_count_df_recomputed = traits_count_df_recomputed.sort_values(by='Size', ascending=False)
        traits_count_df_recomputed = traits_count_df_recomputed.rename(columns={'Size': "trait_count"})
        traits_count_df_recomputed = traits_count_df_recomputed.set_index('trait')

        master_df_overriden_recomputed = pd.merge(master_df_overriden, traits_count_df_recomputed, how='left',
                                                  left_on='trait', right_index=True)
        del traits_count_df_recomputed
        master_df_overriden_recomputed = master_df_overriden_recomputed.drop(['trait_count_x', 'writeoff_x'],
                                                                             axis=1)
        master_df_overriden_recomputed = master_df_overriden_recomputed.rename(
            columns={"trait_count_y": "trait_count", "writeoff_y": "writeoff"})

        master_df_overriden_recomputed = master_df_overriden_recomputed[
            (master_df_overriden_recomputed['trait_count'] >= 20) | (
                ~master_df_overriden_recomputed['writeoff'].isnull())]
        master_df_overriden_recomputed = master_df_overriden_recomputed.sort_values(by=['trait_count'],ascending=False)
        master_df_overriden = master_df_overriden_recomputed.drop(['writeoff'], axis=1)
        del master_df_overriden_recomputed
        master_df_overriden = master_df_overriden[
            ['rsid', 'SNP', 'Ancestry_copy1', 'Ancestry_copy2', 'trait', 'pvalue', 'trait_count',
             'European', 'AfroCaribbean', 'LatinAmerican', 'Other', 'African', 'AfroAmerican',
             'Asian', 'SouthAsian', 'EastAsian', 'OtherAsian', 'World', 'Count']]
        master_df_overriden.to_csv(Master_file_default)
        request.session['Master_file_default_created_flag'] = True
    return master_df_overriden

def filterMaster(request):
    if not request.session.session_key:
        request.session.create()
        request.session['numSuccessUploads'] = 0
    form = TraitModelForm()
    form2 = PvalueModelForm(initial={'pvalue':(PvalueChoice.objects.filter(pvalue=1.0E-5).values('id'))[0]['id']})
    request.session['TraitChoice'] = 'nose morphology measurement'
    request.session['PValueChoice'] = 1.0E-05

    return render(request,'load_traits.html',{'FORM': form,'FORM2': form2, 'nbar':'filter'})

def ancestryMaster(request):
    if not request.session.session_key:
        print('ancestryMaster: no session was found')
        request.session.create()
        request.session['numSuccessUploads'] = 0
    request.session['PValueChoice'] = 1.0E-05
    if ('numSuccessUploads' in request.session.keys()):
        if (request.session['numSuccessUploads'] < 2):
            request.session['AncestryChoice'] = 'Unknown'
        else:
            request.session['AncestryChoice'] = 'Unknown'
    else:
        request.session['numSuccessUploads'] = 0
        request.session['AncestryChoice'] = 'Unknown'
    form2 = PvalueModelForm(initial={'pvalue':(PvalueChoice.objects.filter(pvalue=1.0E-5).values('id'))[0]['id']})
    AncestryChoice.objects.all().update(activated=False)
    PvalueChoice.objects.all().update(activated=False)

    df_master = parse_master(request)
    ancestry_list = list(set(df_master['Ancestry_copy1'].unique()) | set(df_master['Ancestry_copy2'].unique()))

    database_list = list(AncestryChoice.objects.values_list('ancestry', flat=True))

    list_diff = list(set(ancestry_list) - set(database_list))
    model_instances = [AncestryChoice(ancestry=record, activated=False, ) for
                       record in list_diff]
    AncestryChoice.objects.bulk_create(model_instances)
    form = AncestryModelForm(queryset=AncestryChoice.objects.filter(ancestry__in=ancestry_list))

    return render(request,'load_ancestry.html',{'FORM': form,'FORM2': form2, 'nbar':'ancestry'})

def frequencyMaster(request):
    if not request.session.session_key:
        request.session.create()
        request.session['numSuccessUploads'] = 0
    request.session['PValueChoice'] = 1.0E-05
    request.session['RefPopulationChoice'] = 'World'
    form = PvalueModelForm(initial={'pvalue':(PvalueChoice.objects.filter(pvalue=1.0E-5).values('id'))[0]['id']})
    form2 = RefPopulationModelForm(initial={'population':(RefPopulationChoice.objects.filter(population='World').values('id'))[0]['id']})

    return render(request,'load_frequency.html',{'FORM': form, 'FORM2': form2, 'nbar':'frequency'})

def rareMaster(request):
    if not request.session.session_key:
        request.session.create()
        request.session['numSuccessUploads'] = 0
    return render(request,'load_rare.html',{'nbar':'rare'})

def get_master(request):
    userUploadedFlag = False
    if (os.environ.get('SETUP_DATABASE_FLAG')=='False'):
        if ('numSuccessUploads' in request.session.keys()):
            if (request.session['numSuccessUploads'] == 2):
                userUploadedFlag = True
    if userUploadedFlag:
        df_Ancestry = pd.read_csv(conf_settings.MEDIA_ROOT + '/temp_ancestry_' + str(request.session.session_key) + '.csv')
    else:
        queryset_Ancestry = Ancestry.objects.all()
        df_Ancestry = pd.DataFrame.from_records(queryset_Ancestry.values())

    queryset_GWAS = GWAS.objects.all()
    df_GWAS = pd.DataFrame.from_records(queryset_GWAS.values())
    queryset_PHEGENI = PHEGENI.objects.all()
    df_PHEGENI = pd.DataFrame.from_records(queryset_PHEGENI.values())
    df_traits = pd.concat([df_GWAS, df_PHEGENI]).drop_duplicates(subset='rsid', keep='first').reset_index(drop=True)
    queryset_FREQUENCY = FREQUENCY.objects.all()
    df_FREQUENCY = pd.DataFrame.from_records(queryset_FREQUENCY.values())

    df_master = pd.merge(df_Ancestry, df_traits, how='left',left_on='rsid',right_on='rsid')
    df_master = pd.merge(df_master, df_FREQUENCY, how='left',left_on='rsid',right_on='rsid')
    del df_FREQUENCY
    del df_traits
    del df_PHEGENI
    return df_master

def getName_trait(request):
    trait_list = str(request).split('trait_id=')
    if (len(trait_list)==2):
        trait_id = trait_list[1].replace('\'>','')
        if (trait_id==''):
            request.session['TraitChoice'] = 'nose morphology measurement'
        else:
            request.session['TraitChoice'] = pd.DataFrame(TraitChoice.objects.filter(id=trait_id).all().values()).loc[0, 'trait']
    pvalue_list = str(request).split('pvalue_id=')
    if (len(pvalue_list)==2):
        pvalue_id = pvalue_list[1].replace(' HTTP/1.1','').replace('\'>','')
        if(pvalue_id==''):
            request.session['PValueChoice'] = 1.0E-05
        else:
            request.session['PValueChoice'] = pd.DataFrame(PvalueChoice.objects.filter(id=pvalue_id).all().values()).loc[0, 'pvalue']

def loadMaster(request):
    try:
        getName_trait(request)
        Trait_name = request.session['TraitChoice']
        Pvalue_name = request.session['PValueChoice']
        Pvalue_name = float(Pvalue_name)
        df_master = parse_master(request)
    except:
        request.session.flush()
        request.session.create()
        request.session['numSuccessUploads'] = 0
        form_txt = TxtModelForm()
        form_csv = CsvModelForm()
        return HttpResponseRedirect('/faq/')

    FullSeries_temp = pd.concat([df_master['Ancestry_copy1'], df_master['Ancestry_copy2']])
    df_statistics_full = round(FullSeries_temp.value_counts( normalize=True) * 100, 2).to_frame()

    FullMotherSeries_temp = pd.concat([df_master['Ancestry_copy1']])
    df_statistics_Motherfull = round(FullMotherSeries_temp.value_counts( normalize=True) * 100, 2).to_frame()

    FullFatherSeries_temp = pd.concat([df_master['Ancestry_copy2']])
    df_statistics_Fatherfull = round(FullFatherSeries_temp.value_counts( normalize=True) * 100, 2).to_frame()

    df_master_filtered = df_master.loc[(df_master['trait']== Trait_name) & (df_master['pvalue']<= Pvalue_name)]

    FilteredSeries_temp = pd.concat([df_master_filtered['Ancestry_copy1'], df_master_filtered['Ancestry_copy2']])
    df_statistics_filtered = round(FilteredSeries_temp.value_counts( normalize=True) * 100, 2).to_frame()

    FilteredMotherSeries_temp = pd.concat([df_master_filtered['Ancestry_copy1']])
    df_statistics_MotherFiltered = round(FilteredMotherSeries_temp.value_counts( normalize=True) * 100, 2).to_frame()

    FilteredFatherSeries_temp = pd.concat([df_master_filtered['Ancestry_copy2']])
    df_statistics_FatherFiltered = round(FilteredFatherSeries_temp.value_counts( normalize=True) * 100, 2).to_frame()

    df_statistics_combined = pd.merge(df_statistics_filtered,df_statistics_full,how='right',left_index=True,right_index=True)
    df_statistics_combined = df_statistics_combined.rename(columns={df_statistics_combined.columns[0]: "Combined", df_statistics_combined.columns[1]: "Combined_Benchmark"})

    df_statistics_mother = pd.merge(df_statistics_MotherFiltered,df_statistics_Motherfull,how='right',left_index=True,right_index=True)
    df_statistics_mother = df_statistics_mother.rename(columns={df_statistics_mother.columns[0]: "Mother", df_statistics_mother.columns[1]: "Mother_Benchmark"})

    df_statistics_father = pd.merge(df_statistics_FatherFiltered,df_statistics_Fatherfull,how='right',left_index=True,right_index=True)
    df_statistics_father = df_statistics_father.rename(columns={df_statistics_father.columns[0]: "Father", df_statistics_father.columns[1]: "Father_Benchmark"})

    df_statistics = pd.merge(df_statistics_mother,df_statistics_combined,how='right',left_index=True,right_index=True)
    df_statistics = pd.merge(df_statistics_father,df_statistics,how='right',left_index=True,right_index=True)
    df_statistics.reset_index(level=0, inplace=True)
    df_statistics = df_statistics.rename(columns={df_statistics.columns[0]: "Ethnicity"}).fillna('')

    df_statistics.loc[df_statistics['Father']!='','Father'] = df_statistics['Father'].astype(str)+'%'
    df_statistics.loc[df_statistics['Mother']!='','Mother'] = df_statistics['Mother'].astype(str)+'%'
    df_statistics.loc[df_statistics['Combined']!='','Combined'] = df_statistics['Combined'].astype(str)+'%'
    df_json = df_statistics.to_json(orient = 'records')
    return JsonResponse({"data":json.loads(df_json)})

def getName_ancestry(request):
    ancestry_list = str(request).split('ancestry_id=')
    if (len(ancestry_list)==2):
        ancestry_id = ancestry_list[1].replace('\'>','')
        if ancestry_id == '':
            request.session['AncestryChoice'] = 'Unknown'
        else:
            request.session['AncestryChoice'] = pd.DataFrame(AncestryChoice.objects.filter(id=ancestry_id).all().values()).loc[0, 'ancestry']


    pvalue_list = str(request).split('pvalue_id=')
    if (len(pvalue_list) == 2):
        pvalue_id = pvalue_list[1].replace(' HTTP/1.1','').replace('\'>','')
        if pvalue_id == '':
            request.session['PValueChoice'] = 1e-05
        else:
            request.session['PValueChoice'] = pd.DataFrame(PvalueChoice.objects.filter(id=pvalue_id).all().values()).loc[0, 'pvalue']

def loadAncestry(request):
    try:
        getName_ancestry(request)
        Ancestry_name = request.session['AncestryChoice']
        Pvalue_name = request.session['PValueChoice']
        Pvalue_name = float(Pvalue_name)
        df_master = parse_master(request)
    except:
        request.session.flush()
        request.session.create()
        request.session['numSuccessUploads'] = 0
        form_txt = TxtModelForm()
        form_csv = CsvModelForm()
        return render(request, 'upload.html', {'form_csv': form_csv, 'form_txt': form_txt, 'nbar': 'upload'})

    df_master_father = df_master.loc[(df_master['Ancestry_copy2'] == Ancestry_name) & (df_master['pvalue'] <= Pvalue_name)][['trait', 'trait_count']]
    df_master_father = df_master_father.groupby('trait').agg({'trait': 'count', 'trait_count': 'max'})
    df_master_father = df_master_father.rename(columns={'trait': "Ancestry_count_father",'trait_count':'Total_count_father'})
    df_master_father['percentage_father'] = round(df_master_father['Ancestry_count_father'] / df_master_father['Total_count_father'] * 100,2)

    df_master_mother = df_master.loc[(df_master['Ancestry_copy1'] == Ancestry_name) & (df_master['pvalue'] <= Pvalue_name)][['trait', 'trait_count']]
    df_master_mother = df_master_mother.groupby('trait').agg({'trait': 'count', 'trait_count': 'max'})
    df_master_mother = df_master_mother.rename(columns={'trait': "Ancestry_count_mother",'trait_count':'Total_count_mother'})
    df_master_mother['percentage_mother'] = round(df_master_mother['Ancestry_count_mother'] / df_master_mother['Total_count_mother'] * 100,2)

    df_master_all = pd.merge(df_master_father,df_master_mother,how='outer',left_index=True,right_index=True)
    df_master_all['Ancestry_count_combined'] = df_master_all['Ancestry_count_mother'].fillna(0) + df_master_all['Ancestry_count_father'].fillna(0)
    df_master_all['Total_count'] = df_master_all[['Ancestry_count_combined','Total_count_father','Total_count_mother']].max(axis=1)
    df_master_all['percentage_combined'] = (round((df_master_all['Ancestry_count_combined'] / df_master_all['Total_count']) * 100, 2))
    df_master_all = df_master_all.sort_values(by=['percentage_combined'], ascending=False)
    df_master_all['percentage_combined'] = df_master_all['percentage_combined'].astype(str) + '%'

    df_master_all.reset_index(level=0, inplace=True)
    df_master_all = df_master_all.fillna('')
    df_json = df_master_all.to_json(orient = 'records')

    return JsonResponse({"data":json.loads(df_json)})

def getName_frequency(request):
    pvalue_list = str(request).split('pvalue_id=')
    if (len(pvalue_list)==2):
        pvalue_id = pvalue_list[1].replace(' HTTP/1.1','').replace('\'>','')
        if pvalue_id == '':
            request.session['PValueChoice'] = 1.0E-05
        else:
            request.session['PValueChoice'] = pd.DataFrame(PvalueChoice.objects.filter(id=pvalue_id).all().values()).loc[0, 'pvalue']

    population_list = str(request).split('population_id=')
    if (len(population_list) == 2):
        population_id = population_list[1].replace(' HTTP/1.1', '').replace('\'>', '')
        if population_id == '':
            request.session['RefPopulationChoice'] = 'World'
        else:
            request.session['RefPopulationChoice'] = pd.DataFrame(RefPopulationChoice.objects.filter(id=population_id).all().values()).loc[0, 'population']


def loadFrequency(request):
    pd.options.mode.chained_assignment = None
    try:
        getName_frequency(request)
        Pvalue_name = request.session['PValueChoice']
        RefPopulation_name = request.session['RefPopulationChoice']
        Freq_file_user_path = conf_settings.MEDIA_ROOT + '/temp_freq_' + str(request.session.session_key) + '.csv'
        Freq_file_default_path = os.path.join(conf_settings.BASE_DIR.parent, 'static/work/temp_freq_default.csv')
    except:
        request.session.flush()
        request.session.create()
        request.session['numSuccessUploads'] = 0
        form_txt = TxtModelForm()
        form_csv = CsvModelForm()
        return HttpResponseRedirect('/faq/')
    if ((Pvalue_name == 1.0E-05) & (RefPopulation_name=='World')):
        if ('numSuccessUploads' in request.session.keys()):
            if (request.session['numSuccessUploads']==2):
                if (os.path.isfile(Freq_file_user_path)):
                    master_df_freq = pd.read_csv(Freq_file_user_path)
                    df_json = master_df_freq.to_json(orient='records')
                    return JsonResponse({"data": json.loads(df_json)})
            else:
                master_df_freq = pd.read_csv(Freq_file_default_path)
                df_json = master_df_freq.to_json(orient='records')
                return JsonResponse({"data": json.loads(df_json)})
        if (((os.environ.get('SETUP_DATABASE_FLAG')=='True') & ('Freq_default_created_flag' in request.session))):
            if (os.path.isfile(Freq_file_default_path)):
                master_df_freq = pd.read_csv(Freq_file_default_path)
                df_json = master_df_freq.to_json(orient='records')
                return JsonResponse({"data": json.loads(df_json)})

    list_refpop = [RefPopulation_name]
    try:
        df_master = parse_master(request)
    except FileNotFoundError:
        request.session.flush()
        request.session.create()
        request.session['numSuccessUploads'] = 0
        form_txt = TxtModelForm()
        form_csv = CsvModelForm()
        return HttpResponseRedirect('/faq/')
    master_df = df_master[df_master['pvalue'] <= Pvalue_name]  # UPDATE
    master_df = master_df[master_df['World'].notna() & master_df['SNP'].notna() & master_df['trait'].notna()]
    master_df = master_df[(~master_df['SNP'].str.contains('I')) & (~master_df['SNP'].str.contains('D')) & (~master_df['SNP'].str.contains('-'))]
    for refpop in list_refpop:
        master_df[refpop] = ('{"' + master_df[refpop].str.replace(',', ',"').str.replace(':', '":') + '}').apply(json.loads)

    master_df['SNP_len'] = master_df['SNP'].str.len()

    master_df_1 = master_df[master_df['SNP_len'] == 1]
    if not (master_df_1.shape[0]==0):
        for refpop in list_refpop:
            master_df_1[refpop + '_dist'] = master_df_1.apply(lambda x: x[refpop].get(x['SNP']), axis=1)

    master_df_2 = master_df[master_df['SNP_len'] == 2]
    master_df_2['coef'] = master_df_2.apply(lambda x: 0.01 if (x['SNP'][0] == x['SNP'][1]) else 0.02, axis=1)
    for refpop in list_refpop:
        master_df_2[refpop + '_dist'] = master_df_2['coef'] * (master_df_2.apply(lambda x: x[refpop].get(x['SNP'][0]), axis=1) * master_df_2.apply(lambda x: x[refpop].get(x['SNP'][1]), axis=1))

    master_df_2 = master_df_2.drop(['coef'], axis=1)

    master_df_freq = pd.concat([master_df_2, master_df_1])
    master_df_freq = master_df_freq.drop(['SNP_len'], axis=1)

    rarity_threshold = 5
    for refpop in list_refpop:
        master_df_freq[refpop + '_rare'] = (master_df_freq[refpop + '_dist'] <= rarity_threshold).astype(int)

    master_df_freq = master_df_freq.groupby('trait').agg({RefPopulation_name+'_rare': 'sum', 'trait_count': 'max'})

    for refpop in list_refpop:
        master_df_freq[refpop + '_rarepct'] = round((master_df_freq[refpop + '_rare'] / master_df_freq['trait_count']) * 100,2)

    master_df_freq.reset_index(level=0, inplace=True)
    master_df_freq = master_df_freq.fillna('')
    master_df_freq['selected_rare'] = master_df_freq[RefPopulation_name + '_rare']
    master_df_freq['selected_pct'] = master_df_freq[RefPopulation_name + '_rarepct'].astype(str)+'%'
    master_df_freq = master_df_freq[['trait','selected_rare','trait_count','selected_pct']]
    master_df_freq = master_df_freq.sort_values(by=['selected_rare', 'selected_pct'], ascending=False)
    if ((Pvalue_name == 1.0E-05) & (RefPopulation_name=='World')):
        if ('numSuccessUploads' in request.session.keys()):
            if (request.session['numSuccessUploads'] == 2):
                if (not os.path.isfile(Freq_file_user_path)):
                    master_df_freq.to_csv(Freq_file_user_path)
                    request.session['Freq_user_created_flag'] = True
        if (os.environ.get('SETUP_DATABASE_FLAG')=='True'):
            master_df_freq.to_csv(Freq_file_default_path)
            request.session['Freq_default_created_flag'] = True
    df_json = master_df_freq.to_json(orient='records')
    return JsonResponse({"data":json.loads(df_json)})

def loadRare(request):
    pd.options.mode.chained_assignment = None
    Rare_file_user_path = conf_settings.MEDIA_ROOT + '/temp_rare_' + str(request.session.session_key) + '.csv'
    Rare_file_default_path = os.path.join(conf_settings.BASE_DIR.parent, 'static/work/temp_rare_default.csv')
    if ('numSuccessUploads' in request.session.keys()):
        if (request.session['numSuccessUploads']==2):
            if (os.path.isfile(Rare_file_user_path)):
                df_master = pd.read_csv(Rare_file_user_path)
                df_json = df_master.to_json(orient='records')
                return JsonResponse({"data": json.loads(df_json)})
        else:
            df_master = pd.read_csv(Rare_file_default_path)
            df_json = df_master.to_json(orient='records')
            return JsonResponse({"data": json.loads(df_json)})
    if ((os.environ.get('SETUP_DATABASE_FLAG')=='True') & ('Rare_default_created_flag' in request.session)):
        if (os.path.isfile(Rare_file_default_path)):
            df_master = pd.read_csv(Rare_file_default_path)
            df_json = df_master.to_json(orient='records')
            return JsonResponse({"data": json.loads(df_json)})
    try:
        df_master = parse_master(request)
    except FileNotFoundError:
        request.session.flush()
        request.session.create()
        request.session['numSuccessUploads'] = 0
        form_txt = TxtModelForm()
        form_csv = CsvModelForm()
        return HttpResponseRedirect('/faq/')
    df_master['Reference'] = df_master['World']
    master_df = df_master[df_master['World'].notna() & df_master['SNP'].notna() & df_master['trait'].notna()]
    master_df = master_df[(~master_df['SNP'].str.contains('I')) & (~master_df['SNP'].str.contains('D')) & (~master_df['SNP'].str.contains('-'))]
    master_df['World'] = ('{"' + master_df['World'].str.replace(',', ',"').str.replace(':', '":') + '}').apply(json.loads)

    master_df['SNP_len'] = master_df['SNP'].str.len()

    master_df_1 = master_df[master_df['SNP_len'] == 1]
    if not (master_df_1.shape[0]==0):
        master_df_1['Total_dist'] = master_df_1.apply(lambda x: x['World'].get(x['SNP']), axis=1)

    master_df_2 = master_df[master_df['SNP_len'] == 2]
    master_df_2['coef'] = master_df_2.apply(lambda x: 0.01 if (x['SNP'][0] == x['SNP'][1]) else 0.02, axis=1)

    master_df_2['Total_dist'] = master_df_2['coef'] * (master_df_2.apply(lambda x: x['World'].get(x['SNP'][0]), axis=1) * master_df_2.apply(lambda x: x['World'].get(x['SNP'][1]), axis=1))

    master_df_2 = master_df_2.drop(['coef'], axis=1)

    master_df_freq = pd.concat([master_df_2, master_df_1])
    del master_df_2
    del master_df_1

    master_df_freq['Total_dist'] = round((master_df_freq['Total_dist']), 2)

    master_df_freq = master_df_freq.sort_values(by=['Total_dist', 'Count'], ascending=[True,False])
    master_df_freq = master_df_freq.head(50)
    master_df_freq['Reference'] = master_df_freq['Reference'].astype(str).apply(lambda x: dict(subString.split(":") for subString in x.split(",")))
    master_df_freq['Reference'] = master_df_freq['Reference'].apply(lambda x: {k:float(v) for k,v in x.items()})
    master_df_freq['Reference'] = master_df_freq['Reference'].apply(lambda x: max(x, key=x.get))
    master_df_freq.loc[master_df_freq['SNP'].str.len()==2,'Reference'] = master_df_freq['Reference'].apply(lambda x: 2*str(x))
    master_df_freq = master_df_freq[['rsid', 'Reference', 'SNP', 'trait', 'pvalue', 'Total_dist', 'Count']]
    master_df_freq['pvalue'] = master_df_freq['pvalue'].apply(lambda x: "{:.0e}".format(x)).replace('0e+00','0')
    master_df_freq['Count'] = master_df_freq['Count'].apply(lambda x: "{:,.0f}".format(x))
    master_df_freq['Total_dist'] = master_df_freq['Total_dist'].astype(str) + '%'

    master_df_freq = master_df_freq.fillna('')
    if ('numSuccessUploads' in request.session.keys()):
        if (request.session['numSuccessUploads'] == 2):
            if (not os.path.isfile(Rare_file_user_path)):
                master_df_freq.to_csv(Rare_file_user_path)
    if (os.environ.get('SETUP_DATABASE_FLAG')=='True'):
        master_df_freq.to_csv(Rare_file_default_path)
        request.session['Rare_default_created_flag'] = True
    df_json = master_df_freq.to_json(orient = 'records')
    del master_df_freq
    return JsonResponse({"data":json.loads(df_json)})
