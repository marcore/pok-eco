# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import UTC
from social.apps.django_app.default.models import UserSocialAuth
# from courseware import grades
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.models import StudentModule, OfflineComputedGrade
from courseware.courses import get_course_by_id
from oai.models import OaiRecord
from xapi.models import XapiBackendConfig
from ecoapi.models import Teacher, CourseStructureCache
from ecoapi.tasks import offline_calc, update_course_structure


def heartbeat(request):  # pylint: disable=unused-argument
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    risposta = {
        "alive_at": now
    }

    return JsonResponse(risposta)


def teacher_view(request, id_teacher):  # pylint: disable=unused-argument
    try:
        teacher = get_object_or_404(Teacher, id_teacher=id_teacher)
    except Http404:
        emptyresponse = {}
        return JsonResponse(emptyresponse)
    name = u'%s %s' % (teacher.first_name, teacher.last_name)
    if teacher.image:
        imageurl = teacher.image
    else:
        imageurl = ''

    descriptions = []
    for d in teacher.teacherdescription_set.all():
        descriptions.append(
            {"language": d.language,
             "label": d.label}
        )
    risposta = {
        "name": name,
        "imageUrl": imageurl,
        "desc": descriptions
    }
    return JsonResponse(risposta, safe=False)


def user_courses(request, eco_user_id):
    risposta = []
    try:
        usa = get_object_or_404(UserSocialAuth, uid=eco_user_id)
    except Http404:
        return JsonResponse(risposta, safe=False)
    # The pre-fetching of groups is done to make auth checks not require an
    # additional DB lookup (this kills the Progress page in particular).
    student = User.objects.prefetch_related("groups").get(id=usa.user.id)

    course_enrollements = student.courseenrollment_set.all()
    now = datetime.now(UTC())
    for ce in course_enrollements:
        course_key = ce.course_id
        course_key_str = u'%s' % course_key
        try:
            course = get_course_by_id(course_key)
        except Http404:
            # This souldn't be happen if course is delete correctly (deleting also enrollments)
            continue
        # grades.grade(student, request, course)
        grade_summary = optimized_grade(student, request, course_key)

        modules = StudentModule.objects.filter(student=student, course_id=course_key)
        viewCount = modules.count()
        if viewCount > 0:
            firstViewDate = modules.order_by('created')[0].created.strftime("%Y-%m-%dT%H:%M:%S")
            lastViewDate = modules.order_by('-modified')[0].modified.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            firstViewDate = ""
            lastViewDate = ""

        # If cutoff is reached, and today > course.end_date -> course.end_date else ""
        nonzero_cutoffs = [cutoff for cutoff in course.grade_cutoffs.values() if cutoff > 0]
        success_cutoff = min(nonzero_cutoffs) if nonzero_cutoffs else None
        completedDate = ""
        if success_cutoff and grade_summary['percent'] > success_cutoff:
            if course.end < now:
                completedDate = course.end.strftime("%Y-%m-%dT%H:%M:%S")

        # Sum of difference between created and modified StudentModule for this course
        spentTime = timedelta()
        for m in modules:
            spentTime += m.modified - m.created

        risposta.append(
            {
                "id": course_key_str,  # it is a representation like u'edX/DemoX/Demo_Course'
                "viewCount": viewCount,
                "progressPercentage": int(grade_summary['percent'] * 100),
                # "currentPill": 3,  NOT USED because we provide progressPercentage
                "firstViewDate": firstViewDate,  # First StudentModule created
                "lastViewDate": lastViewDate,  # Last StudentModule modified
                "completedDate": completedDate,
                # Total time the user spent in this course in milliseconds
                "spentTime": str(spentTime.seconds * 1000)
            }
        )
    return JsonResponse(risposta, safe=False)


def optimized_grade(student, request, course_key):   # pylint: disable=unused-argument
    '''
    Similar to instructor offline_gradecal.student_grades the offline_gradecalc but we need
    to set a periodic task to update those data with a day(?) retention.
    Update need the django command compute_grades in background
    '''
    now = datetime.now(UTC())
    task_args = [course_key.to_deprecated_string()]
    try:
        ocg = OfflineComputedGrade.objects.get(user=student, course_id=course_key)
        if (ocg.updated + timedelta(days=1)) < now:
            offline_calc.apply_async(task_args)
        return json.loads(ocg.gradeset)
    except OfflineComputedGrade.DoesNotExist:
        grade_summary = dict(percent=0)  # assume this and run task for calculate
        offline_calc.apply_async(task_args)
        return grade_summary


def tasks(request, course_id):  # pylint: disable=unused-argument
    '''
    Retrieve course structure for Learning Analytics integration
    https://docs.google.com/document/d/1pTcAm9o9XrHXgiXkm7YzFWHqusvPQN4xRnVuMDjg-lA
    '''
    course_key = ""
    oai_prefix = XapiBackendConfig.current().oai_prefix
    course_id = course_id.replace(oai_prefix, "")
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    try:
        oai_course = OaiRecord.objects.get(identifier=oai_prefix + course_id)  # pylint: disable=unused-variable
    except OaiRecord.DoesNotExist:
        return JsonResponse({}, status=404)
    try:
        structure = CourseStructureCache.objects.get(course_id=course_key)
        return JsonResponse(json.loads(structure.structure_json))
    except CourseStructureCache.DoesNotExist:
        update_course_structure.delay(unicode(course_key))
        return JsonResponse({}, status=503)
