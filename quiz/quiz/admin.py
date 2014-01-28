'''
Created on Sep 9, 2013

@author: Michal Sylwester
'''

#pylint: disable=no-member,super-on-old-class

from quiz.models import Experiment, Template, Proposal, Question, Answer,\
    UserQuestion
from django.contrib import admin, messages
from django.forms.widgets import TextInput, Textarea
import django.db.models
from django.conf.urls import patterns, url
from django.shortcuts import render_to_response, render
from django.template.context import RequestContext
from django.core import urlresolvers
from django.db.models.aggregates import Count
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.http.response import HttpResponse, HttpResponseRedirect
from django import forms


class MyAdminSite(admin.AdminSite):
    pass


class QuestionInLine(admin.StackedInline):
    model = Question
    extra = 2
    formfield_overrides = {
        django.db.models.TextField: {'widget': Textarea(attrs={'cols': '80',
                                                               'rows': '4'})}
    }


class UserQuestionInLine(admin.TabularInline):
    model = UserQuestion
    extra = 2
    formfield_overrides = {
        django.db.models.TextField: {'widget': Textarea(attrs={'cols': '40',
                                                               'rows': '8'})},
        django.db.models.CharField: {'widget': TextInput(attrs={'size': '40'})}
    }


class ImportQuestionsForm(forms.Form):
    template = forms.ModelChoiceField(queryset=Template.objects.all())
    file = forms.FileField()


class ExperimentAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "show_results")
    list_display_links = ("name", )
    list_editable = ("active", )
    inlines = [QuestionInLine, UserQuestionInLine]

    def get_urls(self):
        urls = super(ExperimentAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^(?P<exp>\d+)/answers/$',
                self.admin_site.admin_view(self.answers),
                name="quiz_experiment_answers"),
            url(r'^(?P<exp>\d+)/import/$',
                self.admin_site.admin_view(self.import_questions),
                name="quiz_experiment_import")
        )
        return my_urls + urls

    def show_results(self, obj):
        answers = Answer.objects.filter(question__experiment=obj)
        url = urlresolvers.reverse("admin:quiz_experiment_answers",
                                   kwargs={'exp': obj.id})
        if len(answers) == 0:
            reply = _("No answers yet")
        else:
            reply = ungettext(
                    '<a href="%(url)s">Show report for %(count)d answer</a>',
                    '<a href="%(url)s">Show report for %(count)d answers</a>',
                len(answers)) % {
                    'url': url,
                    'count': len(answers)
                }
        return reply
    show_results.allow_tags = True

    def answers(self, request, exp):
        opts = self.model._meta  # pylint: disable=protected-access
        has_perm = request.user.has_perm(opts.app_label + '.' \
                                     + opts.get_change_permission())

        experiment = Experiment.objects.get(id=exp)
        questions = Question.objects.filter(experiment=experiment)
        proposals = Proposal.objects.filter(template__experiment=experiment).order_by("order")
        for question in questions:
            question.answers = {i.id: i.count for i in
                         Proposal.objects
                         .filter(template__experiment=experiment)
                         .filter(answer__question=question)
                         .annotate(count=Count("answer"))}
        context = {
                   'admin_site': self.admin_site.name,
                   'title': _("Answers report for experiment \"%s\"") % experiment.name,
                   'opts': opts,
#                   'root_path': '/%s' % admin_site.root_path,
                   'app_label': opts.app_label,
                   'has_change_permission': has_perm,
                   'current_app': self.admin_site.name,
                   'original': _("Answers"),
                   'exp': exp,
                   'questions': questions,
                   'proposals': proposals,
                   }
        template = "admin/answers.html"
        return render_to_response(template, context,
                                  context_instance=RequestContext(request))

    actions = ['action_export_questions', 'action_import_questions']

    def action_export_questions(self, request, queryset):
        rows_updated = len(queryset)
        if rows_updated != 1:
            self.message_user(request, "Please select exactly 1 experiment")
            return

        questions = queryset[0].question_set.all()

        self.message_user(request, "%s questions to be exported." % len(questions))

        response = HttpResponse(content_type="text/plain")
        for question in questions:
            response.write("%s\n#######################\n" % question)
        return response
    action_export_questions.short_description = "Export questions"

    def action_import_questions(self, request, queryset):
        rows_updated = len(queryset)
        if rows_updated != 1:
            self.message_user(request, "Please select exactly 1 experiment, questions will be added to it.")
            return

        url = urlresolvers.reverse("admin:quiz_experiment_import",
                                   kwargs={'exp': queryset[0].id})
        return HttpResponseRedirect(url)
    action_import_questions.short_description = "Import questions"

    def import_questions(self, request, exp):
        opts = self.model._meta  # pylint: disable=protected-access
        has_perm = request.user.has_perm(opts.app_label + '.' \
                                     + opts.get_change_permission())

        experiment = Experiment.objects.get(id=exp)
        success_url = urlresolvers.reverse("admin:quiz_experiment_change",
                                   args=(exp,))
        if request.method == 'POST':  # If the form has been submitted...
            form = ImportQuestionsForm(request.POST, request.FILES)
            if form.is_valid():  # All validation rules pass
                # Process the data in form.cleaned_data

                counter = experiment.questionsFromFile(form.files['file'])

                if counter > 0:
                    messages.success(request, '%s questions added' % counter)
                    return HttpResponseRedirect(success_url)  # Redirect after POST

                messages.error(request, 'Failed to import any questions from %s' % form.files['file'].name)
        else:
            form = ImportQuestionsForm()

        context = {
                   'admin_site': self.admin_site.name,
                   'title': _("Data import for experiment \"%s\"") % experiment.name,
                   'opts': opts,
#                   'root_path': '/%s' % admin_site.root_path,
                   'app_label': opts.app_label,
                   'has_change_permission': has_perm,
                   'current_app': self.admin_site.name,
                   'original': _("Answers"),
                   'exp': exp,
                   #'questions': questions,
                   #'proposals': proposals,
                   'form': form,
                   }

        return render(request, 'admin/import.html', context)


class ProposalInLine(admin.TabularInline):
    model = Proposal
    extra = 1
    formfield_overrides = {
        django.db.models.CharField: {'widget': TextInput(attrs={'size': '120'})}
    }


class TemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "template")
    list_display_links = ("name", )
    list_editable = ("template", )
    inlines = [ProposalInLine]


class ProposalAdmin(admin.ModelAdmin):
    list_display = ("template", "order", "value", "description")
    list_display_links = ("template",)
    list_editable = ("order", "value", "description", )
    list_filter = ("template__name",)
    ordering = ("template", "order")
    formfield_overrides = {
        django.db.models.CharField: {'widget': TextInput(attrs={'size': '120'})}
    }


class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "experiment", "question")
    list_editable = ("question",)
    list_filter = ("experiment__name",)
    ordering = ("id", )
    formfield_overrides = {
        django.db.models.TextField: {'widget': Textarea(attrs={'cols': '80', 'rows': '4'})}
    }


#==============================================================================
#     def get_urls(self):
#         urls = super(QuestionAdmin, self).get_urls()
#         my_urls = patterns('',
#             url(r'^add_many/$', self.admin_site.admin_view(self.add_many))
#         )
#         return my_urls + urls
#
#     def add_many(self, request):
#         opts = self.model._meta
#         admin_site = self.admin_site
#         has_perm = request.user.has_perm(opts.app_label + '.' \
#                                      + opts.get_change_permission())
#         context = {
#                    'admin_site': admin_site.name,
#                    'title': "My Custom View",
#                    'opts': opts,
#                    'root_path': '/%s' % admin_site.root_path,
#                    'app_label': opts.app_label,
#                    'has_change_permission': has_perm,
#                    'current_app': self.admin_site.name
#                    }
#         template = "admin/quiz/question/add_many.html"
#         return render_to_response(template, context,
#                                   context_instance=RequestContext(request))
#==============================================================================

admin_site = MyAdminSite()
admin_site.register(Experiment, ExperimentAdmin)
admin_site.register(Template, TemplateAdmin)
#admin_site.register(Proposal, ProposalAdmin)
#admin_site.register(Question, QuestionAdmin)
