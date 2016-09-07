import MySQLdb
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class EdevateDbConnector:
    host = settings.EDEVATE_MYSQL_HOST
    port = settings.EDEVATE_MYSQL_PORT
    user = settings.EDEVATE_MYSQL_USER
    passwd = settings.EDEVATE_MYSQL_PASSWD
    db = settings.EDEVATE_MYSQL_DB_NAME

    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        self.connection = MySQLdb.connect(host=self.host,
                                          port=self.port,
                                          user=self.user,
                                          passwd=self.passwd,
                                          db=self.db)
        self.cursor = self.connection.cursor()

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()

    def get_edevate_user_id(self, user_email):
        self.cursor.execute("""SELECT *
                               FROM users_customuser
                               WHERE email='{}';""".format(user_email)
                            )
        edevate_user = self.cursor.fetchone()
        logger.debug("Get edevate user: {!r}".format(edevate_user))
        return edevate_user[0]

    def get_verification_course(self, openedx_course_id, published_by):
        self.cursor.execute("""SELECT *
                               FROM openedx_edxcourseverification
                               WHERE openedx_course_id = '{}'
                               AND published_by_id='{}';
                               """.format(openedx_course_id,
                                          published_by)
                            )
        verification_course = self.cursor.fetchone()
        logger.debug("Get verification course: {!r}".format(
            verification_course)
        )
        return verification_course

    def create_verification_course(self, openedx_course_id, published_by_id):
        self.cursor.execute("""INSERT INTO openedx_edxcourseverification
                               (openedx_course_id, status, published_by_id)
                               VALUES ('{}', 'reviewable', '{}');
                            """.format(openedx_course_id, published_by_id)
                            )
        self.connection.commit()
        return self.cursor.lastrowid

    def update_verification_course(self, openedx_course_id, published_by_id):
        self.cursor.execute("""UPDATE openedx_edxcourseverification
                               SET status='reviewable'
                               WHERE openedx_course_id='{}'
                               AND published_by_id='{}';
                            """.format(openedx_course_id, published_by_id)
                            )
        affected_rows = self.connection.affected_rows()
        self.connection.commit()
        return affected_rows

    def update_or_create_verification_course(self,
                                             openedx_course_id,
                                             course_author):
        published_by_id = self.get_edevate_user_id(course_author)
        verification_course = self.get_verification_course(openedx_course_id,
                                                           published_by_id)
        if verification_course:
            affected_rows = self.update_verification_course(openedx_course_id,
                                                            published_by_id)
            logger.debug("Update verification course: {}".format(
                affected_rows)
            )
        else:
            affected_rows = self.create_verification_course(openedx_course_id,
                                                            published_by_id)
            logger.debug("Create verification course: {}".format(
                affected_rows)
            )
        return affected_rows

    def get_course(self, openedx_course_id):
        self.cursor.execute("""SELECT id
                               FROM courses_course
                               WHERE url LIKE '%{}%';
                               """.format(openedx_course_id)
                            )
        course_ptr_id = self.cursor.fetchone()
        logger.debug("Get edevate course_ptr_id: {!r}".format(course_ptr_id))
        return course_ptr_id[0]

    def check_user_course(self, course_ptr_id):
        self.cursor.execute("""SELECT id
                               FROM courses_courseuser
                               WHERE course_ptr_id = '{}';
                               """.format(course_ptr_id)
                            )
        course = self.cursor.fetchone()
        if course:
            return False
        else:
            return True

    def update_users_course_list(self, openedx_course_id, user):
        edevate_user = self.get_edevate_user_id(user)
        course_ptr_id = self.get_course(openedx_course_id)
        if self.check_user_course(course_ptr_id):
            self.cursor.execute("""INSERT INTO courses_courseuser
                                   (state, removed, course_ptr_id, student_id)
                                   VALUES ('undergoing', '0', '{}', '{}');
                                """.format(course_ptr_id, edevate_user)
                                )
            self.connection.commit()
            return True
        return False
