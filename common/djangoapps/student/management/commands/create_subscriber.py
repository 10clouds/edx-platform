"""Management command to create subscriber records for registered users"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from student.models import Subscriber


class Command(BaseCommand):
    """Management command to create subscriber records for registered users"""
    help = """
    This command will create subscriber record for registered users.
    If optional params (username, email) are not empty it will create
    subscriber record for that user.
    """

    def add_arguments(self, parser):
        parser.add_argument('-u', '--user',
                            action='store',
                            dest='user',
                            default=False,
                            help='username or email')

    def handle(self, *args, **options):
        user = options['user']
        if user:
            try:
                if '@' in user:
                    userobj = User.objects.get(email=user)
                else:
                    userobj = User.objects.get(username=user)
                Subscriber.objects.create(user=userobj)
                print 'Subscriber record has been created for user ' \
                      'with identifier {}'.format(user)
            except Exception as err:  # pylint: disable=broad-except
                print "Error creating subscriber record for user with " \
                      "identifier {}: [{}: {}]".format(user,
                                                       type(err).__name__,
                                                       err.message)
        else:
            for userobj in User.objects.all():
                try:
                    subscriber = Subscriber.objects.create(user=userobj)
                    print "Subscriber record has been created for user with " \
                          "identifier {}".format(subscriber)
                except Exception as err:
                    print "Error creating subscriber record for user with " \
                          "identifier {}: [{}: {}]".format(userobj,
                                                           type(err).__name__,
                                                           err.message)
