"""my_snp_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from snps.views import upload_file_view
#from snps.views import download
#from snps.views import getMaster_view
from snps.views import filterMaster
from snps.views import ancestryMaster
from snps.views import frequencyMaster
from snps.views import rareMaster
from snps.views import loadMaster
from snps.views import loadAncestry
from snps.views import loadFrequency
from snps.views import loadRare
from snps.views import displayFAQ
#from snps.views import loadMaster2

urlpatterns = [
    path('site_admin/', admin.site.urls),
    path('',upload_file_view,name='upload-view'),
    #path('posts-master/',getMaster_view,name='post-view'),
    path('filter/', filterMaster, name='filter-view'),
    path('ancestry/', ancestryMaster, name='ancestry-view'),
    path('frequency/', frequencyMaster, name='frequency-view'),
    path('rare/', rareMaster, name='rare-view'),
    path('load/', loadMaster, name='load-view'),
    path('load-ancestry/', loadAncestry, name='loadAncestry-view'),
    path('load-frequency/', loadFrequency, name='loadFrequency-view'),
    path('load-rare/', loadRare, name='loadRare-view'),
    path('faq/', displayFAQ, name='faq-view')
    #path('download',download,name='download-view'),#output_csv_file
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT,)

#if settings.DEBUG:
#    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT,)