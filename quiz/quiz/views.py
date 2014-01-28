'''
Created on Sep 4, 2013

@author: Michal Sylwester
'''

# pylint: disable=E1101
from django.shortcuts import render, redirect
from uuid import uuid4
from quiz.models import User, Experiment, Proposal, Question, Answer, \
    UserQuestion, UserInfo
from django.template.context import Context
from django.http import HttpResponse
import json
from django.template.base import Template
from time import time
from django.utils.text import slugify


def home(request):
    experiments = Experiment.objects.filter(active=True)
    return render(request, "main.html", {
                                         "experiments": experiments
                                         })


def start(request, exp, uuid=None):
    if not uuid or uuid == "None":
        uuid = uuid4()
        returning_user = User(uuid=uuid)
        returning_user.user_agent = request.META.get("HTTP_USER_AGENT")
        returning_user.language = request.META.get("HTTP_ACCEPT_LANGUAGE")
        returning_user.ip = request.META.get('REMOTE_ADDR')
        returning_user.save()
        return redirect(start, exp=exp, uuid=uuid)

    try:
        returning_user = User.objects.get(uuid=uuid)
    except:
        start(request, exp, None)

    experiment = Experiment.objects.get(id=exp)
    if not experiment.active:
        return redirect(home)
    title = experiment.name

    return render(request, "start.html", {"returning_user": returning_user,
                                          "exp": exp,
                                          "uuid": uuid,
                                          "title": title})


def userinfo(request, exp, uuid=None):
    if not uuid:
        return redirect(start, exp=exp, uuid=None)

    try:
        returning_user = User.objects.get(uuid=uuid)
    except:
        return redirect(start, exp=exp, uuid=None)

    experiment = Experiment.objects.get(id=exp)
    if not experiment.active:
        return redirect(home)
    title = experiment.name

    userquestionset = UserQuestion.objects.filter(experiment=experiment)
    userquestions = []

    for q in userquestionset:
        question = {
            "missing": len(request.POST) > 0,  # no answers->nothing missing
            "question": q.question,
            "name": slugify(q.question),
            "choices": q.answers.strip().split("\n"),
            "style": q.style,
            "userquestion": q
        }

        if question["name"] in request.POST:
            try:
                ans = int(request.POST[question["name"]])
                if ans >= 0 and ans < len(question["choices"]):
                    question["missing"] = False
                    question["selected"] = ans
            except:
                pass

        userquestions.append(question)

    all_answered = reduce(lambda a, b: a and not b["missing"],
                          userquestions,
                          len(request.POST) > 0)

    if all_answered:
        for question in userquestions:
            tmp_question = question["userquestion"]
            tmp_answer = question["choices"][question["selected"]]
            try:
                record = UserInfo.objects.get(user=returning_user,
                                              userquestion=tmp_question)
            except:
                record = UserInfo(user=returning_user,
                                  userquestion=tmp_question)
            record.useranswer = tmp_answer
            record.save()

        return redirect(quiz, exp=exp, uuid=uuid)

    return render(request, "userinfo.html", {
              "returning_user": returning_user,
              "exp": exp,
              "uuid": uuid,
              "title": title,
              "userquestions": userquestions
              })


def comment(request, exp, uuid=None):
    if not uuid or uuid == u"None":
        return redirect(home)

    try:
        returning_user = User.objects.get(uuid=uuid)
    except:
        return redirect(home)

    experiment = Experiment.objects.get(id=exp)
    if not experiment.active:
        return redirect(home)
    title = experiment.name

    return render(request, "comment.html", {"returning_user": returning_user,
                                          "exp": exp,
                                          "uuid": uuid,
                                          "title": title})


def get_random_question(exp, uuid):
    experiment = Experiment.objects.get(id=exp)

    questions = Question.objects.filter(experiment=experiment)
    question_template = Template(experiment.template.template)

    all_questions = len(questions)

    try:
        user = User.objects.get(uuid=uuid)
        questions = questions.exclude(answer__user=user)
    except:
        pass

    questions = questions.order_by('?')

    if len(questions) > 0:
        question = questions[0]

        question_data = question.question.split("\n")
        question_id = question.id

        question_text = question_template.render(
                            Context({"question": question_data}))
    else:
        question_id = -1
        question_text = "Finished!"

    return {"id": question_id,
            "text": question_text,
            "left": len(questions),
            "all": all_questions,
            "percent": (all_questions - len(questions)) * 100 / all_questions,
            "time": time()}


def quiz(request, exp, uuid=None):
    # Make sure we have uuid of valid user
    try:
        returning_user = User.objects.get(uuid=uuid)
    except:
        # start will redirect to right URL,
        # redirecting now would double-redirect
        return start(request, exp, None)

    experiment = Experiment.objects.get(id=exp)
    if not experiment.active:
        return redirect(home)
    title = experiment.name
    proposals = Proposal.objects.filter(template=experiment.template).order_by('order')
    question = get_random_question(exp, uuid)

    if question["id"] == -1:
        return redirect(finished, exp, uuid)

    return render(request, "quiz.html", {"title": title,
                                         "proposals": proposals,
                                         "exp": exp,
                                         "uuid": uuid,
                                         "question": question})


def answer(request, exp, uuid):
    question_id = Question.objects.get(id=request.POST["question"])
    answer_id = Proposal.objects.get(id=request.POST["answer"])
    delay = time() - float(request.POST["time"])

    try:
        user = User.objects.get(uuid=uuid)
    except:
        return redirect(start, exp=exp, uuid=None)

    new_answer = Answer(answer=answer_id,
                        question=question_id,
                        user=user,
                        time=delay)
    new_answer.save()

    new_question = get_random_question(exp, uuid)
    return HttpResponse(json.dumps({"question": new_question}),
                        content_type="application/json")


def finished(request, exp, uuid):
    experiment = Experiment.objects.get(id=exp)
    title = experiment.name
    user = User.objects.get(uuid=uuid)

    commentstring = request.POST["comment"]
    user.comment = commentstring
    user.save()

    return render(request, "finished.html", {"title": title,
                                     "exp": exp,
                                     "uuid": uuid,
                                     "comment": commentstring})
