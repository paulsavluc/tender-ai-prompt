# tender_app/forms.py
from django import forms
from .models import TenderProject, TenderTemplate, ReferenceDocument

class TenderProjectForm(forms.ModelForm):
    class Meta:
        model = TenderProject
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional project description'
            })
        }

class TenderTemplateForm(forms.ModelForm):
    class Meta:
        model = TenderTemplate
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.docx,.pdf,.xlsx'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            valid_extensions = ['.docx', '.pdf', '.xlsx']
            file_extension = os.path.splitext(file.name)[[1]]#__1).lower()   
            if file_extension not in valid_extensions:
                raise forms.ValidationError(
                    'Only Word (.docx), PDF (.pdf), and Excel (.xlsx) files are allowed.'
                )
            
            # Check file size (50MB limit)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 50MB.')
        
        return file

class ReferenceDocumentForm(forms.ModelForm):
    class Meta:
        model = ReferenceDocument
        fields = ['file', 'title', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.docx,.pdf,.xlsx,.txt'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Reference document title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Brief description of this reference'
            })
        }

class FieldContentForm(forms.Form):
    def __init__(self, fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in fields:
            field_name = field.get('field_name')
            field_type = field.get('field_type', 'text')
            generated_content = field.get('generated_content', '')
            
            if field_type in ['text', 'cell']:
                self.fields[field_name] = forms.CharField(
                    label=field_name,
                    initial=generated_content,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 3
                    }),
                    required=False
                )
            else:
                self.fields[field_name] = forms.CharField(
                    label=field_name,
                    initial=generated_content,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control'
                    }),
                    required=False
                )
