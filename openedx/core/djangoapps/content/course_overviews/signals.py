"""
Signal handler for invalidating cached course overviews
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.dispatch.dispatcher import receiver

from .models import CourseOverview
from .connector import EdevateDbConnector
from xmodule.modulestore.django import SignalHandler, modulestore
from edxmako.shortcuts import render_to_string


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    updates the corresponding CourseOverview cache entry.
    """
    CourseOverview.objects.filter(id=course_key).delete()
    CourseOverview.load_from_module_store(course_key)


@receiver(SignalHandler.course_deleted)
def _listen_for_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from Studio and
    invalidates the corresponding CourseOverview cache entry if one exists.
    """
    CourseOverview.objects.filter(id=course_key).delete()
    # import CourseAboutSearchIndexer inline due to cyclic import
    from cms.djangoapps.contentstore.courseware_index import CourseAboutSearchIndexer
    # Delete course entry from Course About Search_index
    CourseAboutSearchIndexer.remove_deleted_items(course_key)


@receiver(SignalHandler.course_published)
def _create_edevate_course_for_verification(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    create course on the edevate for verification.
    """
    from cms.djangoapps.contentstore.courseware_index import CourseAboutSearchIndexer
    from student.models import CourseAccessRole, get_user

    try:
        course_access_role = CourseAccessRole.objects.get(course_id=course_key,
                                                          role='instructor')
        course_author = course_access_role.user
        edevate_db = EdevateDbConnector()
        edevate_db.update_or_create_verification_course(course_key,
                                                        course_author.email)
        edevate_db.close()
        CourseAboutSearchIndexer.remove_deleted_items(course_key)

        admin_emails_list = settings.ADMIN_VERIFICATION_EMAILS
        for admin_email in admin_emails_list:
            user, user_profile = get_user(admin_email)
            if user:
                context = {
                    'course_key': course_key
                }
                subject = "Openedx course verification"
                message = render_to_string('emails/edevate_course_verification_email.txt',
                                           context)
                from_address = settings.DEFAULT_FROM_EMAIL
                user.email_user(subject, message, from_address)
    except CourseAccessRole.DoesNotExist:
        pass
