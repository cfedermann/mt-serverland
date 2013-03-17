"""
Project: MT Server Land
 Author: Christian Federmann <cfedermann@dfki.de>
"""
from django.contrib import admin
from serverland.dashboard.models import WorkerServer, TranslationRequest

admin.site.register(WorkerServer)
admin.site.register(TranslationRequest)