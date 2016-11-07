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
        self.cursor.execute("""SELECT id
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
                            """.format(openedx_course_id))
        course_ptr_id = self.cursor.fetchone()
        return course_ptr_id[0] if course_ptr_id else None

    def course_user_exists(self, course_ptr_id, student_id):
        self.cursor.execute("""SELECT id
                               FROM courses_courseuser
                               WHERE course_ptr_id = '{}'
                                 AND student_id = '{}';
                            """.format(course_ptr_id, student_id))
        return self.cursor.fetchone()

    def update_users_course_list(self, openedx_course_id, user):
        student_id = self.get_edevate_user_id(user)
        course_ptr_id = self.get_course(openedx_course_id)

        # if there is no corresponding course in edevate db - do nothing
        if not course_ptr_id:
            return

        if not self.course_user_exists(course_ptr_id, student_id):
            self.cursor.execute("""INSERT INTO courses_courseuser
                                   (state, removed, course_ptr_id, student_id)
                                   VALUES ('undergoing', '0', '{}', '{}');
                                """.format(course_ptr_id, student_id))
            self.connection.commit()
        else:
            self.cursor.execute("""UPDATE courses_courseuser SET removed='0'
                                   WHERE course_ptr_id='{}' AND student_id='{}';
                                """.format(course_ptr_id, student_id))
            self.connection.commit()

    def delete_users_course(self, openedx_course_id, user):
        student_id = self.get_edevate_user_id(user)
        course_ptr_id = self.get_course(openedx_course_id)

        # if there is no corresponding course in edevate db - do nothing
        if not course_ptr_id:
            return

        if self.course_user_exists(course_ptr_id, student_id):
            self.cursor.execute("""DELETE FROM courses_courseuser
                                   WHERE course_ptr_id='{}' AND student_id='{}';
                                """.format(course_ptr_id, student_id))
            self.connection.commit()
