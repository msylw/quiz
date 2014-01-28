'''
Created on Sep 4, 2013

@author: Michal Sylwester
'''

from django.db import models
from uuid import uuid4
from django.utils.translation import ugettext_lazy as _
import re

# Mainly for Meta classes
# pylint: disable=no-init,too-few-public-methods
# pylint: disable=missing-docstring


class User(models.Model):
    uuid = models.CharField(
            _("unique user identifier"),
            max_length=40,
            unique=True,
            default=lambda: uuid4)
    comment = models.TextField(
            _("comment"),
            blank=True)
    created = models.DateTimeField(auto_now_add=True)
    changed = models.DateTimeField(auto_now=True)
    user_agent = models.CharField(
            _("user-agent"),
            max_length=300)
    language = models.CharField(
            _("language"),
            max_length=100)
    ip = models.GenericIPAddressField(unpack_ipv4=True)

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")


class Template(models.Model):
    name = models.CharField(_("template name"), max_length=50, unique=True)
    template = models.TextField(
        "question template", max_length=500,
        help_text=_("Include parts of the question using {{question.&lt;num&gt;}} \
        syntax, where &lt;num&gt; is index of line in question (0-based)"))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("template")
        verbose_name_plural = _("templates")


class Experiment(models.Model):
    name = models.CharField(_("experiment name"), max_length=50, unique=True)
    active = models.BooleanField(_("is active"), default=False)
    template = models.ForeignKey(Template)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _("experiment")
        verbose_name_plural = _("experiments")

    def questionsFromFile(self, uploadedfile):
        data = uploadedfile.read().decode("utf-8")  # TODO: encoding detection?
        counter = 0
        for record in re.split("^={3,}$", data, flags=re.M):
            record = record.strip()
            if len(record) == 0:
                continue
            question = Question(question=record, experiment=self)
            question.save()
            counter += 1
        return counter


class UserQuestion(models.Model):
    question = models.CharField(_("question"), max_length=100,
        help_text=_("""Question about user, try to be delicate..."""))
    answers = models.TextField(_("answers"), max_length=500,
        help_text=_("""Possible answers (one per line).
            Try to make the answers self-explanatory
            (able to stand alone without knowing the question)"""))
    style = models.CharField(_("style"), max_length=100,
        help_text=_("""Width style (like Bootstraps), ex: "col-md-3 col-sm-6".
            Remember to check how it worked out on all platforms! """))
    experiment = models.ForeignKey(Experiment)
    order_index = models.IntegerField(_("order"), default=0,
        help_text=_("""Fields will be sorted by this value.
            If same value is reused, the order may be undefined"""))

    def __unicode__(self):
        return self.question

    class Meta:
        verbose_name = _("user question")
        verbose_name_plural = _("user questions")
        ordering = ["order_index"]


class UserInfo(models.Model):
    user = models.ForeignKey(User)
    userquestion = models.ForeignKey(UserQuestion)
    useranswer = models.CharField(_("useranswer"), max_length=50)


class Question(models.Model):
    question = models.TextField(_("question"), max_length=300,
        help_text=_("Each line is referenced separately in the template. Order matters."))
    experiment = models.ForeignKey(Experiment)

    def __unicode__(self):
        return self.question

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")


class Proposal(models.Model):
    template = models.ForeignKey(Template)
    description = models.CharField(_("description"), max_length=300)
    order = models.IntegerField(_("order index"))
    value = models.IntegerField(_("value"))

    def __unicode__(self):
        return self.description


class Answer(models.Model):
    answer = models.ForeignKey(Proposal)
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User)
    time = models.IntegerField("time")
    created = models.DateTimeField(auto_now_add=True)
