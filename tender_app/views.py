# tender_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.conf import settings
import os
import json
from .models import TenderProject, TenderTemplate, ReferenceDocument, ExtractedField, ProcessedDocument
from .forms import TenderProjectForm, TenderTemplateForm, ReferenceDocumentForm, FieldContentForm
from .utils.document_processor import DocumentProcessor
from .utils.ai_generator import AIContentGenerator
from .utils.form_filler import FormFiller
import zipfile
import tempfile
import mimetypes

class ProjectCreateView(View):
    def get(self, request):
        form = TenderProjectForm()
        return render(request, 'create_project.html', {'form': form})
    
    def post(self, request):
        form = TenderProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, 'Project created successfully!')
            return redirect('upload_documents', project_id=project.id)
        return render(request, 'create_project.html', {'form': form})

class DocumentUploadView(View):
    def get(self, request, project_id):
        """Display upload form with existing documents"""
        project = get_object_or_404(TenderProject, id=project_id)
        templates = project.tendertemplate_set.all()
        references = project.referencedocument_set.all()
        
        context = {
            'project': project,
            'templates': templates,
            'references': references,
        }
        
        return render(request, 'upload_documents.html', context)
    
    def post(self, request, project_id):
        """Handle file uploads - Critical: Must handle request.FILES properly"""
        project = get_object_or_404(TenderProject, id=project_id)
        upload_type = request.POST.get('upload_type')
        
        # Critical: Check for files in request.FILES, not request.POST
        if 'files' not in request.FILES:
            return JsonResponse({
                'success': False, 
                'error': 'No files were uploaded'
            })
        
        files = request.FILES.getlist('files')  # Critical: Use getlist for multiple files
        
        if not files:
            return JsonResponse({
                'success': False, 
                'error': 'No files selected'
            })
        
        try:
            uploaded_files = []
            
            for uploaded_file in files:
                # Validate file type
                if not self.is_valid_file_type(uploaded_file.name):
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid file type: {uploaded_file.name}. Only PDF, DOC, DOCX, TXT are allowed.'
                    })
                
                # Validate file size (10MB limit)
                if uploaded_file.size > 10 * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'error': f'File too large: {uploaded_file.name}. Maximum size is 10MB.'
                    })
                
                if upload_type == 'template':
                    saved_file = self.save_template(project, uploaded_file, request.POST)
                elif upload_type == 'reference':
                    saved_file = self.save_reference(project, uploaded_file, request.POST)
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid upload type'
                    })
                
                uploaded_files.append(saved_file)
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
                'files': [{'id': f.id, 'name': getattr(f, 'original_filename', f.title)} for f in uploaded_files]
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Upload failed: {str(e)}'
            })
    
    def save_template(self, project, uploaded_file, post_data):
        """Save uploaded template file"""
        # Generate unique filename
        filename = self.generate_unique_filename(uploaded_file.name, 'templates')
        
        # Save file to storage
        file_path = default_storage.save(f'templates/{filename}', uploaded_file)
        
        file_type = os.path.splitext(uploaded_file.name)[1].lower()
        # Create database record
        template = TenderTemplate.objects.create(
            project=project,
            original_filename=uploaded_file.name,
            file=uploaded_file,
            file_type=file_type,
            title='',
        )
        
        return template
    
    def save_reference(self, project, uploaded_file, post_data):
        """Save uploaded reference file"""
        # Generate unique filename
        filename = self.generate_unique_filename(uploaded_file.name, 'references')
        
        # Save file to storage
        file_path = default_storage.save(f'references/{filename}', uploaded_file)
        
        # Create database record
        reference = ReferenceDocument.objects.create(
            project=project,
            file=uploaded_file,
            title=post_data.get('title', uploaded_file.name),
            description=post_data.get('description', ''),
        )
        
        return reference
    
    def is_valid_file_type(self, filename):
        """Check if file type is allowed"""
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in allowed_extensions
    
    def generate_unique_filename(self, original_filename, folder):
        """Generate unique filename to prevent conflicts"""
        import uuid
        name, ext = os.path.splitext(original_filename)
        unique_id = str(uuid.uuid4())[:8]
        return f"{name}_{unique_id}{ext}"

class ProcessDocumentView(View):
    def get(self, request, project_id):
        project = get_object_or_404(TenderProject, id=project_id)
        templates = project.tendertemplate_set.all()
        
        if not templates.exists():
            messages.error(request, 'Please upload at least one template first.')
            return redirect('upload_documents', project_id=project_id)
        
        # Get all extracted fields
        all_fields = []
        for template in templates:
            fields = template.extractedfield_set.all()
            for field in fields:
                all_fields.append({
                    'id': field.id,
                    'field_name': field.field_name,
                    'field_type': field.field_type,
                    'template_name': template.original_filename,
                    'generated_content': field.generated_content
                })
        
        context = {
            'project': project,
            'fields': all_fields,
            'templates': templates
        }
        return render(request, 'process_document.html', context)
    
    def post(self, request, project_id):
        project = get_object_or_404(TenderProject, id=project_id)
        action = request.POST.get('action')
        
        if action == 'generate_content':
            return self._generate_ai_content(request, project)
        elif action == 'save_and_fill':
            return self._save_and_fill_documents(request, project)
        
        return redirect('process_document', project_id=project_id)
    
    def _generate_ai_content(self, request, project):
      """Generate AI content for all fields"""
      try:
          project.status = 'processing'
          project.save()
          
          # First extract fields if not already done
          self._extract_fields_from_templates(project)
          
          # Collect reference content
          reference_content = self._collect_reference_content(project)
          
          # Get all fields
          all_fields = []
          for template in project.tendertemplate_set.all():
              print(f"Template: {template.extractedfield_set.all()}")
              for field in template.extractedfield_set.all():
                  print(f"Field: {field}")
                  all_fields.append({
                      'id': field.id,
                      'field_name': field.field_name,
                      'field_type': field.field_type,
                  })
          
          print(f"All fields: {all_fields}")
          if not all_fields:
              messages.warning(request, 'No fields found in templates. Please check your template files.')
              return redirect('process_document', project_id=project.id)
          
          # Generate content using AI
          ai_generator = AIContentGenerator()
          project_context = f"Project: {project.name}\nDescription: {project.description}"
          
          generated_content = ai_generator.generate_bulk_content(
              all_fields, reference_content, project_context
          )
          
          # Save generated content
          for field_data in all_fields:
              field_id = str(field_data['id'])
              if field_id in generated_content:
                  field = ExtractedField.objects.get(id=field_data['id'])
                  field.generated_content = generated_content[field_id]
                  field.save()
          
          project.status = 'completed'
          project.save()
          
          messages.success(request, f'AI content generated for {len(generated_content)} fields!')
          
      except Exception as e:
          project.status = 'error'
          project.save()
          messages.error(request, f'Error generating content: {str(e)}')
      
      return redirect('process_document', project_id=project.id)

    def _extract_fields_from_templates(self, project):
      """Extract fields from templates if not already done"""
      from .utils.document_processor import DocumentProcessor
      
      processor = DocumentProcessor()
      
      for template in project.tendertemplate_set.all():
          # Skip if fields already extracted
          if template.extractedfield_set.exists():
              print(f"Fields already extracted for {template.original_filename}")
              continue
              
          try:
              # Determine file type
              file_extension = os.path.splitext(template.file.name)[1].lower()
              file_type = file_extension[1:]  # Remove the dot
              
              # Extract fields
              fields = processor.extract_fields(template.file.path, file_type)
              print(f"Fields: {fields}")
              # Save extracted fields
              for field_data in fields:
                  ExtractedField.objects.create(
                      template=template,
                      field_name=field_data.get('field_name', 'Unknown Field'),
                      field_type=field_data.get('field_type', 'text'),
                      position_info=field_data.get('position_info', {})
                  )
          except Exception as e:
              print(f"Error extracting fields from {template.original_filename}: {e}")
    
    def _collect_reference_content(self, project):
        """Collect content from all reference documents"""
        processor = DocumentProcessor()
        all_content = []
        
        for reference in project.referencedocument_set.all():
            try:
                file_extension = os.path.splitext(reference.file.name)[1].lower()
                file_type = file_extension[1:]  # Remove the dot
                
                content = processor.extract_reference_content(reference.file.path, file_type)
                all_content.append(f"=== {reference.title} ===\n{content}\n")
            except Exception as e:
                print(f"Error processing reference {reference.title}: {e}")
        
        return '\n'.join(all_content)
    
    def _save_and_fill_documents(self, request, project):
        """Save manual edits and fill documents"""
        try:
            # Update fields with manual edits
            for key, value in request.POST.items():
                if key.startswith('field_'):
                    field_id = key.replace('field_', '')
                    try:
                        field = ExtractedField.objects.get(id=field_id)
                        field.generated_content = value
                        field.is_filled = True
                        field.save()
                    except ExtractedField.DoesNotExist:
                        continue
            
            # Fill documents
            self._fill_all_documents(project)
            
            messages.success(request, 'Documents filled successfully!')
            return redirect('download_documents', project_id=project.id)
            
        except Exception as e:
            messages.error(request, f'Error filling documents: {str(e)}')
            return redirect('process_document', project_id=project.id)
    
    def _fill_all_documents(self, project):
        """Fill all template documents with generated content"""
        form_filler = FormFiller()
        
        for template in project.tendertemplate_set.all():
            # Collect field content for this template
            field_content = {}
            for field in template.extractedfield_set.all():
                if field.generated_content:
                    field_content[field.field_name] = field.generated_content
            
            if field_content:
                # Generate output filename
                base_name = os.path.splitext(template.original_filename)[0]
                output_filename = f"{base_name}_filled.{template.file_type}"
                output_path = os.path.join(settings.MEDIA_ROOT, 'processed', output_filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Fill the document
                success = form_filler.fill_document(
                    template.file.path,
                    output_path,
                    field_content,
                    template.file_type
                )
                
                if success:
                    # Save processed document record
                    ProcessedDocument.objects.create(
                        project=project,
                        file=f'processed/{output_filename}'
                    )

class DownloadDocumentsView(View):
    def get(self, request, project_id):
        project = get_object_or_404(TenderProject, id=project_id)
        processed_docs = project.processeddocument_set.all()
        
        context = {
            'project': project,
            'processed_documents': processed_docs
        }
        return render(request, 'download_documents.html', context)

class DownloadFileView(View):
    def get(self, request, document_id):
        try:
            document = get_object_or_404(ProcessedDocument, id=document_id)
            file_path = document.file.path
            
            if os.path.exists(file_path):
                response = FileResponse(
                    open(file_path, 'rb'),
                    as_attachment=True,
                    filename=os.path.basename(file_path)
                )
                return response
            else:
                raise Http404("File not found")
                
        except Exception as e:
            messages.error(request, f'Error downloading file: {str(e)}')
            return redirect('project_list')

class BulkDownloadView(View):
    def get(self, request, project_id):
        project = get_object_or_404(TenderProject, id=project_id)
        processed_docs = project.processeddocument_set.all()
        
        if not processed_docs.exists():
            messages.error(request, 'No documents available for download.')
            return redirect('download_documents', project_id=project_id)
        
        # Create ZIP file
        response = HttpResponse(content_type='application/zip')
        zip_filename = f"{project.name}_documents_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
        
        with zipfile.ZipFile(response, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc in processed_docs:
                if os.path.exists(doc.file.path):
                    zip_file.write(doc.file.path, os.path.basename(doc.file.name))
        
        return response

class DocumentPreviewView(View):
    def get(self, request, document_id):
        document = get_object_or_404(ProcessedDocument, id=document_id)
        
        # Return basic file info for preview
        file_info = {
            'name': os.path.basename(document.file.name),
            'size': document.file.size,
            'type': mimetypes.guess_type(document.file.name)[0],
            'created': document.created_at.isoformat(),
            'download_url': reverse('download_file', args=[document.id])
        }
        
        return JsonResponse(file_info)

class ShareDocumentView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            document_id = data.get('document_id')
            email = data.get('email')
            message = data.get('message', '')
            notify = data.get('notify', False)
            
            document = get_object_or_404(ProcessedDocument, id=document_id)
            
            # Here you would implement actual email sharing
            # For now, we'll just simulate success
            
            return JsonResponse({
                'success': True,
                'message': f'Document shared with {email} successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class AjaxFieldUpdateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            field_id = data.get('field_id')
            content = data.get('content')
            
            field = get_object_or_404(ExtractedField, id=field_id)
            field.generated_content = content
            field.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class ProjectListView(View):
    def get(self, request):
        # Get all projects
        projects = TenderProject.objects.all()
        
        # Apply search filter
        search_query = request.GET.get('search', '')
        if search_query:
            projects = projects.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Apply status filter
        status_filter = request.GET.get('status', '')
        if status_filter:
            projects = projects.filter(status=status_filter)
        
        # Apply sorting
        sort_by = request.GET.get('sort', '-created_at')
        projects = projects.order_by(sort_by)
        
        # Pagination
        # paginator = Paginator(projects, 12)  # 12 projects per page
        # page_number = request.GET.get('page')
        # projects = paginator.get_page(page_number)
        
        context = {
            'projects': projects,
            'search_query': search_query,
            'status_filter': status_filter,
            'sort_by': sort_by,
        }
        return render(request, 'project_list.html', context)

class ProjectDetailView(View):
    def get(self, request, project_id):
        project = get_object_or_404(TenderProject, id=project_id)
        templates = project.tendertemplate_set.all()
        references = project.referencedocument_set.all()
        processed_documents = project.processeddocument_set.all()
        
        context = {
            'project': project,
            'templates': templates,
            'references': references,
            'processed_documents': processed_documents,
        }
        
        return render(request, 'project_detail.html', context)
