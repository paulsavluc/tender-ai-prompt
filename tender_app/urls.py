# tender_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('create/', views.ProjectCreateView.as_view(), name='create_project'),
    path('project/<uuid:project_id>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/<uuid:project_id>/upload/', views.DocumentUploadView.as_view(), name='upload_documents'),
    path('project/<uuid:project_id>/process/', views.ProcessDocumentView.as_view(), name='process_document'),
    path('project/<uuid:project_id>/download/', views.DownloadDocumentsView.as_view(), name='download_documents'),
    path('download/<int:document_id>/', views.DownloadFileView.as_view(), name='download_file'),
    path('ajax/update-field/', views.AjaxFieldUpdateView.as_view(), name='ajax_update_field'),
    path('project/<uuid:project_id>/download/bulk/', views.BulkDownloadView.as_view(), name='bulk_download'),
    path('document/<int:document_id>/preview/', views.DocumentPreviewView.as_view(), name='document_preview'),
    path('ajax/share-document/', views.ShareDocumentView.as_view(), name='share_document'),
]
