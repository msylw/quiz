from django.conf.urls import patterns, include, url
#from django.contrib import admin
from quiz.admin import admin_site

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
# pylint: disable=C0301,invalid-name

#admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'quiz.views.home', name="home"),
    url(r'^start/(?P<exp>\d+)/(?P<uuid>.*)/$', 'quiz.views.start', name="start"),
    url(r'^userinfo/(?P<exp>\d+)/(?P<uuid>.*)/$', 'quiz.views.userinfo', name="userinfo"),
    url(r'^quiz/(?P<exp>\d+)/(?P<uuid>.*)/$', 'quiz.views.quiz', name="quiz"),
    url(r'^answer/(?P<exp>\d+)/(?P<uuid>.*)/$', 'quiz.views.answer', name="answer"),
    url(r'^comment/(?P<exp>\d+)/(?P<uuid>.*)/$', 'quiz.views.comment', name="comment"),
    url(r'^finished/(?P<exp>\d+)/(?P<uuid>.*)/$', 'quiz.views.finished', name="finished"),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin_site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),


)
