"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test accounts".
"""
__author__ = 'mark'

from django.test import TestCase
from testutils import login_to_hive,Test_Start, Test_End, Test_Msg, test_for_200_with_get
import inspect
from datetime import  datetime

# User full name = Harvey Ive
USERNAME_FOR_TEST='harvey'
PASSWORD_FOR_TEST='password'
SMSCODE_FOR_TEST='9999'
VALID_LAST_4_SSN="1234"
VALID_PATIENT_ID="ARFT1234"
VALID_PATIENT_LASTNAME="First"
VALID_PATIENT_FIRSTNAME="Arthur"

USERNAME_NOT_TEST='nottester'
PASSWORD_NOT_TEST='password'
SMSCODE_NOT_TEST='9999'
INVALID_LAST_4_SSN='9876'
INVALID_PATIENT_ID='ZEBR9876'
INVALID_PATIENT_LASTNAME="Wrong"
INVALID_PATIENT_FIRSTNAME="Al"
PERMISSION_DENIED="Permission Denied.  Your account credentials                             are valid but you do not have the permission                             required to access this function."

USERNAME_NO_ACCOUNT_TEST="badusername"
PASSWORD_NO_ACCOUNT_TEST='password'
SMSCODE_NO_ACCOUNT_TEST='9999'

class Accounts_SimpleTest(TestCase):
    """Background to this test harness
    and prove the test harness works
    """

    # fixtures = ['intake_test_data.json','accounts_test_data.json']

    def test_basic_addition_Accounts(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        Test_Start("1+1=2")
        answer = self.assertEqual(1 + 1, 2)
        Test_Msg("hive.apps.accounts.tests.py")
        print "     Test Runtime: "+str(datetime.now())
        if answer == None:
            print "     Test Harness ready"
        else:
            print "     This Test Harness has a problem"
        Test_End("hive.apps.accounts.tests.py")

        return

# Tests to run:
# login:
    # invalid userid
    # valid userid

    # Completed: 1/3/2012
# smscode:
    # exercised via login_to_hive in apps.intake.testutils
    # Used in Login test

    # Completed: 1/3/2012

# logout:
    # just test it works

    # Completed: 1/3/2012

# password-reset-request:
# reset-password/(?P<reset_password_key>
    # test together using Reset Request call then Reset password then login with revised password.



class Login_TestCase(TestCase):
    """
    Test with invalid and valid user id.
    Use account with mobile of 999-999-9999 so that we can use 9999 smscode.
    """
    fixtures = ['apps/accounts/fixtures/accounts_test_data.json']

    def test_login_invalid_user(self):
        Test_Start()
        result = login_to_hive(USERNAME_NO_ACCOUNT_TEST,PASSWORD_NO_ACCOUNT_TEST,SMSCODE_NO_ACCOUNT_TEST)
        if result==401:
            Test_Msg("     Successful result for: "+USERNAME_NO_ACCOUNT_TEST+"/"+PASSWORD_NO_ACCOUNT_TEST+"("+SMSCODE_NO_ACCOUNT_TEST+"):"+ str(result))
        else:
            Test_Msg("     Failed Result - "+str(result)+" using: "+USERNAME_NO_ACCOUNT_TEST+"/"+PASSWORD_NO_ACCOUNT_TEST+"("+SMSCODE_NO_ACCOUNT_TEST+")")

        Test_End()
        return

    def test_login_valid_user(self):
        Test_Start()
        result = login_to_hive(USERNAME_FOR_TEST, PASSWORD_FOR_TEST, SMSCODE_FOR_TEST)
        if result==200:
            Test_Msg("     Successful login result for: "+USERNAME_FOR_TEST+"/"+PASSWORD_FOR_TEST+"("+SMSCODE_FOR_TEST+"):"+ str(result))
        else:
            Test_Msg("     Failed Result - "+str(result)+" using: "+USERNAME_FOR_TEST+"/"+PASSWORD_FOR_TEST+"("+SMSCODE_FOR_TEST+")")

        Test_End()


        return

class Logout_TestCase(TestCase):
    """
    Test Logout works
    Login with valid account then logout
    """

    fixtures = ['apps/accounts/fixtures/accounts_test_data.json']

    def test_logout_for_valid_user(self):
        Test_Start()

        LOGOUT_TEST_TEXT = 'You have been logged out'

        uname = USERNAME_FOR_TEST
        pw = PASSWORD_FOR_TEST
        smc = SMSCODE_FOR_TEST
        output = []
        post_url = '/accounts/logout/'
        post_parameters = {}

        look_for_this = LOGOUT_TEST_TEXT
        calling_test_function = inspect.getframeinfo(inspect.currentframe().f_back)[2]

        result = login_to_hive(uname, pw, smc)
        if result==200:
            Test_Msg("     Successful login result for: "+uname+"/"+pw+"("+smc+"):"+ str(result))
        else:
            Test_Msg("     Failed login Result - "+str(result)+" using: "+uname+"/"+pw+"("+smc+")")

        Test_Msg("Now Test Logout: "+post_url)
        outcome = test_for_200_with_get(self, uname, pw, output, post_url,post_parameters, look_for_this, calling_test_function )

        if outcome==None:
            Test_Msg("Successful Logout to "+post_url)
        Test_End()

        return

class Password_Admin_TestCase(TestCase):
    """
    Use a logged in user to issue a password reset
    Access Reset Password
    Then Login with updated password.
    """
    fixtures = ['apps/accounts/fixtures/accounts_test_data.json']

    def test_password_reset_process(self):
        """
        First make a password reset request
        """




