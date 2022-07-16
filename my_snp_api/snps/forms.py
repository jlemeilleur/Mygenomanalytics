from django import forms
from .models import Csv
from .models import Txt
from .models import TraitChoice
from .models import PvalueChoice
from .models import AncestryChoice
from .models import RefPopulationChoice

class AncestryModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset')
        super(AncestryModelForm, self).__init__(*args, **kwargs)
        self.fields['ancestry'] = forms.ModelChoiceField(queryset=queryset,label = 'Select Ancestry')
    class Meta:
        model = AncestryChoice
        fields = ('ancestry',)

class TraitModelForm(forms.ModelForm):
    trait = forms.ModelChoiceField(queryset=TraitChoice.objects.all(),label = 'Select Trait',empty_label = 'nose morphology (11)')
    class Meta:
        model = TraitChoice
        fields = ('trait',)
        #fields = '__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['trait'].queryset = TraitChoice.objects.all()

class CsvModelForm(forms.ModelForm):
    class Meta:
        model = Csv
        fields = ('upload_ancestry_file',)

class TxtModelForm(forms.ModelForm):
    class Meta:
        model = Txt
        fields = ('upload_genome_file',)

class PvalueModelForm(forms.ModelForm):
    pvalue = forms.ModelChoiceField(queryset=PvalueChoice.objects.all(),label = 'Select Pvalue')
    class Meta:
        model = PvalueChoice
        fields = ('pvalue',)

class RefPopulationModelForm(forms.ModelForm):
    population = forms.ModelChoiceField(queryset=RefPopulationChoice.objects.all(),label = 'Select your Reference Population')
    class Meta:
        model = RefPopulationChoice
        fields = ('population',)

