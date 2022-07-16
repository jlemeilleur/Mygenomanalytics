from django.db import models
import pandas as pd
import numpy as np
import time
import gzip
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.conf import settings as conf_settings
import os
import csv
#import glob
from .validators import validate_csv_size, validate_txt_size
#import uuid

class Csv(models.Model):
    upload_ancestry_file = models.FileField(upload_to='csvs/', validators=[FileExtensionValidator(allowed_extensions=['csv']),validate_csv_size])
    uploaded = models.DateTimeField(auto_now_add=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return f"File id: {self.id}"

class Txt(models.Model):
    upload_genome_file = models.FileField(upload_to='txts/', validators=[FileExtensionValidator(allowed_extensions=['txt']),validate_txt_size])
    #upload_ancestry_file = models.FileField(upload_to='txts')
    uploaded = models.DateTimeField(auto_now_add=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return f"File id: {self.id}"

class Ancestry(models.Model):
    rsid = models.CharField(max_length=20, primary_key=True)
    SNP = models.CharField(max_length=2, blank=True)
    Ancestry_copy1 = models.CharField(max_length=50, blank=True)
    Ancestry_copy2 = models.CharField(max_length=50, blank=True)
    Ancestry_df = pd.DataFrame()

    def __str__(self):
        return self.rsid

    @classmethod
    def get_region_mapping(cls, path = os.path.join(conf_settings.BASE_DIR.parent, 'static/input/regions_mapping_23andme.csv')):
        # Segments regions according to their granularity level
        region_mapping = pd.read_csv(path)
        df_split = lambda x: x.split(" | ")
        region_mapping['Population'] = region_mapping['Population'].apply(df_split)
        population_df = pd.DataFrame([item for sublist in region_mapping['Population'] for item in sublist],
                                     columns=['Ancestry'])
        population_df['level'] = 3
        global_population_df = pd.DataFrame(list(region_mapping['Global Population']), columns=['Ancestry'])
        global_population_df['level'] = 1
        #cls.region_level_df = pd.concat([population_df, global_population_df])
        return pd.concat([population_df, global_population_df])

    @classmethod
    def get_ancestryComp_file(cls,ancestry_file_path):
        ancestry_df = pd.read_csv(ancestry_file_path)
        ancestry_df = ancestry_df.rename(columns={"Start Point": "Start_Point", "End Point": "End_Point"})
        return ancestry_df

    @classmethod
    def mod_ancestry_df(cls,ancestry_file_path):
        # Cleans 23andme ancestry file by removing overlapping regions and keeping the most precise one.
        # Example, segment A of Chromosome 1 is assigned both Northwestern Europe and British: keep British only.

        ancestry_df = cls.get_ancestryComp_file(ancestry_file_path)
        region_level_df = cls.get_region_mapping()

        ancestry_df['Chromosome'] = ancestry_df['Chromosome'].str.strip('chr')
        ancestry_df_mod = pd.merge(ancestry_df, region_level_df, how='left', left_on='Ancestry', right_on='Ancestry')
        ancestry_df_mod.loc[ancestry_df_mod['Ancestry'] == 'Unassigned', 'level'] = 1
        ancestry_df_mod.loc[ancestry_df_mod['Ancestry'].str.startswith('Broadly '), 'level'] = 2
        ancestry_df_mod.loc[ancestry_df_mod['level'].isna(), 'level'] = 4
        ancestry_df_clean = ancestry_df_mod.copy(deep=True)[0:0]
        for chromosome in ancestry_df_mod['Chromosome'].unique():
            for copy in ancestry_df_mod[ancestry_df_mod['Chromosome'] == chromosome]['Copy'].unique():
                sub_df = ancestry_df_mod[(ancestry_df_mod['Chromosome'] == chromosome) & (ancestry_df_mod['Copy'] == int(copy))]
                list_pos = list(dict.fromkeys(list(sub_df['Start_Point']) + list(sub_df['End_Point'])))
                list_pos.sort()
                for i in range(len(list_pos) - 1):
                    temp_row = sub_df[
                        (sub_df['Start_Point'] <= list_pos[i]) & (list_pos[i + 1] <= sub_df['End_Point'])].sort_values(
                        by=['level'], ascending=False).head(1)
                    temp_row['Start_Point'], temp_row['End_Point'] = list_pos[i], list_pos[i + 1]
                    ancestry_df_clean = ancestry_df_clean.append(temp_row)
        ancestry_df_clean = ancestry_df_clean.drop(['level'], axis=1)
        #cls.ancestry_df_mod = ancestry_df_clean.sort_values(by=['Chromosome', 'Copy', 'Start_Point', 'End_Point'])
        return ancestry_df_clean.sort_values(by=['Chromosome', 'Copy', 'Start_Point', 'End_Point'])

    @staticmethod
    def parse_genome_file(file):
        data = {}
        with open(file) as fin:
            for line in fin:
                if line[0] == '#':
                    continue
                else:
                    line_split = line.split()
                data[line_split[0]] = [line_split[3], line_split[1], line_split[2]]
        return pd.DataFrame.from_dict(data, orient='index')

    @classmethod
    def get_master_23andme(cls,request,ancestry_path,genome_path):
        df_23andme_raw = pd.DataFrame(Ancestry.parse_genome_file(genome_path)).rename(columns={0: "SNP", 1: "Chromosome_23andme", 2: "Position_23andme"})
        ancestry_df_mod = cls.mod_ancestry_df(ancestry_path)
        df_23andme = df_23andme_raw.astype({'Position_23andme': 'int32'})
        df_23andme = df_23andme.sort_values(by=['Chromosome_23andme','Position_23andme'])
        df_23andme['Ancestry_copy1'] = 'Unknown'
        df_23andme['Ancestry_copy2'] = 'Unknown'
        for index, row in ancestry_df_mod.iterrows():
            if (row['Copy'] == 1):
                ancestry_field = 'Ancestry_copy1'
            elif (row['Copy'] == 2):
                ancestry_field = 'Ancestry_copy2'
            else:
                print('Error: unknown copy')
            df_23andme.loc[(df_23andme['Position_23andme'] >= row['Start_Point']) & (df_23andme['Position_23andme'] < row['End_Point']) & (df_23andme['Chromosome_23andme'] == row['Chromosome']), ancestry_field] = row['Ancestry']

        df_23andme = df_23andme[['SNP','Ancestry_copy1','Ancestry_copy2']]
        df_23andme['rsid'] = df_23andme.index

        if (os.environ.get('SETUP_DATABASE_FLAG')=='False'):
            df_23andme.to_csv(conf_settings.MEDIA_ROOT + '/temp_ancestry_' + str(request.session.session_key) + '.csv')
        else:
            Ancestry.objects.all().delete()
            df_records = df_23andme.to_dict('records')
            model_instances = [cls(rsid=record['rsid'], SNP=record['SNP'], Ancestry_copy1=record['Ancestry_copy1'], Ancestry_copy2=record['Ancestry_copy2']) for record in df_records]
            cls.objects.bulk_create(model_instances)
            
class GWAS(models.Model):
    rsid = models.CharField(max_length=20,primary_key=True)
    trait = models.CharField(max_length=500,blank=True)
    pvalue = models.DecimalField(max_digits=20, decimal_places=20,blank=True)

    def __str__(self):
        return self.rsid

    @classmethod
    def parseTraits(cls, path):
        gwas_associations = pd.read_csv(path)
        gwas_associations_monogenic = gwas_associations[gwas_associations['SNPS'].str.match("^rs[0-9]+$", case=False)]
        gwas_associations_monogenic = gwas_associations_monogenic[['SNPS', 'MAPPED_TRAIT', 'CHR_ID', 'CHR_POS', 'P-VALUE']]
        gwas_associations_monogenic['P-VALUE'] = gwas_associations_monogenic['P-VALUE'].astype(float)
        gwas_associations_monogenic['CHR_POS'] = pd.to_numeric(gwas_associations_monogenic['CHR_POS'],errors='coerce')
        gwas_associations_monogenic = gwas_associations_monogenic[~np.isinf(gwas_associations_monogenic['CHR_POS']) & ~gwas_associations_monogenic['CHR_POS'].isnull()]
        gwas_associations_monogenic['CHR_POS'] = gwas_associations_monogenic['CHR_POS'].astype(int)
        gwas_associations_monogenic['CHR_ID'] = gwas_associations_monogenic['CHR_ID'].astype(str)
        gwas_associations_monogenic = gwas_associations_monogenic.groupby(['SNPS', 'MAPPED_TRAIT', 'CHR_ID', 'CHR_POS','P-VALUE']).size()  # duplicates have more importance because verified by multiple studies.
        gwas_associations_monogenic = gwas_associations_monogenic.reset_index().rename(columns={0: "count"})
        gwas_associations_monogenic = gwas_associations_monogenic.groupby(['SNPS', 'MAPPED_TRAIT', 'CHR_ID', 'CHR_POS']).agg({'P-VALUE': 'mean','count': 'sum'})  # for same trait, keep the mean p-value to be representative
        gwas_associations_monogenic = gwas_associations_monogenic.reset_index()
        gwas_associations_monogenic = gwas_associations_monogenic.sort_values(by=['count', 'P-VALUE'], ascending=(False, True))  # for different traits, keep the min p-value to be more significant
        gwas_associations_monogenic = gwas_associations_monogenic.drop_duplicates(subset=['SNPS', 'CHR_ID', 'CHR_POS'], keep='first')
        gwas_associations_monogenic = gwas_associations_monogenic.drop_duplicates(subset=['SNPS'], keep='first')
        gwas_associations_monogenic = gwas_associations_monogenic.set_index('SNPS')
        gwas_associations_monogenic = gwas_associations_monogenic[['CHR_ID', 'CHR_POS', 'MAPPED_TRAIT', 'P-VALUE']]
        gwas_associations_monogenic = gwas_associations_monogenic.rename(columns={"MAPPED_TRAIT": "trait_gwas", "P-VALUE": "pvalue_gwas"})
        gwas_associations_monogenic['rsid'] = gwas_associations_monogenic.index
        df_records = gwas_associations_monogenic.to_dict('records')
        model_instances = [cls(rsid=record['rsid'],trait=record['trait_gwas'],pvalue=record['pvalue_gwas'],) for record in df_records]
        cls.objects.bulk_create(model_instances)

class PHEGENI(models.Model):
    rsid = models.CharField(max_length=20, primary_key=True)
    trait = models.CharField(max_length=500, blank=True)
    pvalue = models.DecimalField(max_digits=20, decimal_places=20,blank=True)

    def __str__(self):
        return self.rsid

    @classmethod
    def parseTraits(cls, file):
        data = {}
        with open(file) as fin:
            for line in fin:
                if line[0] == '#':
                    continue
                else:
                    line_split = line.split('\t')
                data[line_split[0]] = [line_split[2], line_split[1], line_split[8], line_split[9], line_split[10]]
        traits_tab = pd.DataFrame.from_dict(data, orient='index').rename(
            columns={0: 'SNP', 1: 'trait_PheGenI', 2: 'Chromosome', 3: 'Position', 4: 'pvalue_PheGenI'}).astype(
            {'Position': 'int32', 'pvalue_PheGenI': 'float'})
        traits_tab = traits_tab.groupby(['SNP', 'trait_PheGenI', 'Chromosome', 'Position',
                                         'pvalue_PheGenI']).size()  # duplicates have more importance because verified by multiple studies.
        traits_tab = traits_tab.reset_index().rename(columns={0: "count"})
        traits_tab = traits_tab.groupby(['SNP', 'trait_PheGenI', 'Chromosome', 'Position']).agg(
            {'pvalue_PheGenI': 'max', 'count': 'sum'})  # for same trait, keep the max p-value to be conservative
        traits_tab = traits_tab.reset_index()
        traits_tab = traits_tab.sort_values(by=['SNP', 'count', 'pvalue_PheGenI'], ascending=(
        True, False, True))  # for different traits, keep the min p-value to be more significant
        traits_tab = traits_tab.drop_duplicates(subset=['SNP', 'Chromosome', 'Position'], keep='first')
        traits_tab['SNP'] = 'rs' + traits_tab['SNP']
        traits_tab = traits_tab.set_index('SNP').drop(['count'], axis=1)
        traits_tab = traits_tab[['trait_PheGenI','pvalue_PheGenI']]
        traits_tab['rsid'] = traits_tab.index
        df_records = traits_tab.to_dict('records')
        model_instances = [cls(rsid=record['rsid'], trait=record['trait_PheGenI'], pvalue=record['pvalue_PheGenI'], ) for
                           record in df_records]
        cls.objects.bulk_create(model_instances)


class Genome(models.Model):
    rsid = models.CharField(max_length=20, primary_key=True)
    SNP = models.CharField(max_length=2, blank=True)
    Chromosome = models.CharField(max_length=5)
    Position = models.IntegerField(validators=[MaxValueValidator(999999999)], blank=True)#,db_column='Start Point')

    def __str__(self):
        return self.rsid

class TraitChoice(models.Model):
    trait = models.CharField(max_length=500, blank=True)
    count = models.CharField(max_length=10, blank=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return self.trait + ' (' + str(self.count) + ')'

class PvalueChoice(models.Model):
    pvalue = models.FloatField()
    #pvalue = models.DecimalField(max_digits=20, decimal_places=20,blank=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return str(self.pvalue)

class RefPopulationChoice(models.Model):
    population = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.population

class AncestryChoice(models.Model):
    ancestry = models.CharField(max_length=500, blank=True, unique=True)
    activated = models.BooleanField(default=False)

    def __str__(self):
        return self.ancestry


class FREQUENCY(models.Model):
    rsid = models.CharField(max_length=20, primary_key=True)
    European = models.CharField(max_length=300, blank=True)
    AfroCaribbean = models.CharField(max_length=300, blank=True)
    LatinAmerican = models.CharField(max_length=300, blank=True)
    Other = models.CharField(max_length=300, blank=True)
    African = models.CharField(max_length=300, blank=True)
    AfroAmerican = models.CharField(max_length=300, blank=True)
    Asian = models.CharField(max_length=300, blank=True)
    SouthAsian = models.CharField(max_length=300, blank=True)
    EastAsian = models.CharField(max_length=300, blank=True)
    OtherAsian = models.CharField(max_length=300, blank=True)
    World = models.CharField(max_length=300, blank=True)
    Count = models.IntegerField(validators=[MaxValueValidator(1000000)], blank=True)

    def __str__(self):
        return self.rsid

    @classmethod
    def master_frequency(cls,genome_file_path):
        import time
        import gzip
        import json
        freq_csv_mod = os.path.join(conf_settings.BASE_DIR.parent, 'static/input/NCBI_freq_mod.csv')
        if os.path.isfile(freq_csv_mod):
            freq_df = pd.read_csv(freq_csv_mod, index_col=0)
        else:
            path_NCBI_refPopulation = os.path.join(conf_settings.BASE_DIR.parent, 'static/input/NCBI_refPopulations')
            cls.NCBI_populations = cls.read_NCBI_file(path_NCBI_refPopulation)

            freq_file = os.path.join(conf_settings.BASE_DIR.parent, 'frequency/freq.vcf.gz')
            freq_csv = os.path.join(conf_settings.BASE_DIR.parent, 'frequency/NCBI_freq.csv')
            batch_size = 100000
            df_23andme_raw = pd.DataFrame(Ancestry.parse_genome_file(file=genome_file_path)).rename(
                columns={0: "SNP", 1: "Chromosome_23andme", 2: "Position_23andme"})
            freq_temp_df = cls.parse_frequency_file(freq_file, freq_csv, df_23andme_raw, batch_size)

            freq_df = cls.calculate_frequency(freq_csv_mod, freq_temp_df)
            del freq_temp_df
            del freq_csv_mod
        cls.objects.all().delete()
        freq_df['rsid'] = freq_df.index
        df_records = freq_df.to_dict('records')
        model_instances = [cls(rsid=record['rsid'], European=record['European'], AfroCaribbean=record['Latin American 1'],
                               AfroAmerican=record['African American'], LatinAmerican=record['Latin American 2'],
                               Other=record['Other'], African=record['African'],
                               Asian=record['Asian'], SouthAsian=record['South Asian'], EastAsian=record['East Asian'], OtherAsian=record['Other Asian'],
                               World=record['Total'], Count=record['Count'],) for record in df_records]
        cls.objects.bulk_create(model_instances,batch_size=1000)

    @classmethod
    def read_NCBI_file(cls, path):
        import json
        with open(path, 'r') as ncbi_file:
            NCBI_populations = ncbi_file.read().replace('\n', '')
        return json.loads(NCBI_populations)

    @classmethod
    def rename_df(cls, test_dic, column_list):
        df_1 = pd.DataFrame.from_dict(test_dic).T
        df_1 = df_1.rename(columns=column_list)
        df_1 = df_1.rename(columns=cls.NCBI_populations)
        df_1 = df_1.drop(['QUAL', 'FILTER', 'INFO', 'African Others'],
                         axis=1)
        return df_1

    @classmethod
    def parse_frequency_file(cls, freq_file, freq_csv, df_23andme_raw, batch_size):
        # Parse frequency info of NCBI SNPs that are available in 23andme.
        # file has 904,000,000 rows
        # 481sec per 10,000,000 rows
        try:
            freq_temp_df = pd.read_csv(freq_csv, index_col=0)
        except FileNotFoundError:
            t0 = time.time()
            counter = 0
            batchFlag = False
            freq_dic = {}
            freq_temp_df = pd.DataFrame()
            with gzip.open(freq_file, "rt") as ifile:
                for line in ifile:
                    if line.startswith("#"):
                        if line.startswith("#CHROM"):
                            header = line.strip('\n').split('\t')
                            column_list = dict(zip(list(range(0, len(header))), header))
                        continue
                    line_mod = line.strip('\n').split('\t')
                    freq_dic[line_mod[2]] = line_mod
                    counter += 1
                    if ((counter % batch_size) == 0):
                        print('Total number of rows processed: ' + str(counter))
                        batchFlag = True
                    if batchFlag:
                        freq_df_temp = cls.rename_df(freq_dic, column_list, )
                        freq_df = pd.merge(df_23andme_raw, freq_df_temp, how='inner', left_index=True, right_index=True)
                        freq_temp_df = pd.concat([freq_df, freq_temp_df])
                        del freq_df
                        del freq_df_temp
                        del freq_dic
                        freq_dic = {}
                        batchFlag = False
                    #if (counter >= 1000000):
                    #    break
                ifile.close()
                freq_temp_df.to_csv(freq_csv)
            t1 = time.time()
            elapsed_sec = round(t1 - t0)
            print('Elapsed time to parse NCBI frequency file: ' + str(elapsed_sec) + ' seconds.')
        return freq_temp_df

    @classmethod
    def calculate_frequency(cls, freq_csv_mod, freq_temp_df):
        try:
            freq_df = pd.read_csv(freq_csv_mod, index_col=0)
        except FileNotFoundError:
            t0 = time.time()
            freq_df = pd.DataFrame(columns=(list(freq_temp_df.columns)[9:]) + ['Count'])
            freq_df.to_csv(freq_csv_mod, mode='w', header=True)
            counter = 0
            for SNP in freq_temp_df.index:
                counter += 1
                for ethnicity in freq_temp_df.columns[9:]:
                    variant_list = (str(freq_temp_df.loc[SNP, 'REF']) + ',' + freq_temp_df.loc[SNP, 'ALT']).split(",")
                    total = int(freq_temp_df.loc[SNP, ethnicity].split(':')[0])
                    ethnicity_num = list(map(int, freq_temp_df.loc[SNP, ethnicity].split(':')[1].split(',')))
                    ethnicity_num = [total - sum(ethnicity_num)] + ethnicity_num
                    if (total != 0):
                        ethnicity_freq = [round((int(x) / total) * 100, 4) for x in ethnicity_num]
                    else:
                        ethnicity_freq = [round((int(x)) * 100, 4) for x in ethnicity_num]
                    freq_df.loc[SNP, ethnicity] = str(dict(zip(variant_list, ethnicity_freq))).strip('{').strip(
                        '}').replace('\'', '').replace(' ', '')
                    # this line not tested yet
                    freq_df.loc[SNP, 'Count'] = int(freq_temp_df.loc[SNP, 'Total'].split(':')[0])
                if ((counter % 100) == 0):
                    print('Number of rows processed: ' + str(counter))
                    freq_df.to_csv(freq_csv_mod, mode='a', header=False)
                    freq_df = pd.DataFrame(columns=list(freq_temp_df.columns)[9:])
            #            if (counter > 2000):
            #                break
            t1 = time.time()
            elapsed_sec = round(t1 - t0)
            print('Elapsed time to calculate NCBI SNP frequency : ' + str(elapsed_sec) + ' seconds.')
            freq_df = pd.read_csv(freq_csv_mod, index_col=0)
        return freq_df
