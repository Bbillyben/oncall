# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.
import ldap
from oncall import db
import os
import logging
from oncall.user_sync.ldap_sync import user_exists, import_user, update_user
import sys
logger = logging.getLogger(__name__)


class Authenticator:
    def __init__(self, config):
        if config.get('debug'):
            self.authenticate = self.debug_auth
            return
        self.authenticate = self.ldap_auth
        self.changePassword = self.ldap_change_passwd
        self.updateuserdata = self.update_user_data

        if 'ldap_cert_path' in config:
            self.cert_path = config['ldap_cert_path']
            if not os.access(self.cert_path, os.R_OK):
                logger.error("Failed to read ldap_cert_path certificate")
                raise IOError
        else:
            self.cert_path = None

        self.bind_user = config.get('ldap_bind_user')
        self.bind_password = config.get('ldap_bind_password')
        self.search_filter = config.get('ldap_search_filter')

        self.ldap_url = config.get('ldap_url')
        self.base_dn = config.get('ldap_base_dn')

        self.user_suffix = config.get('ldap_user_suffix')
        self.import_user = config.get('import_user', False)
        self.attrs = config.get('attrs')

    def ldap_auth(self, username, password):
        if self.cert_path:
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.cert_path)

        connection = ldap.initialize(self.ldap_url)
        connection.set_option(ldap.OPT_REFERRALS, 0)
        attrs = ['dn'] + list(self.attrs.values())
        ldap_contacts = {}

        if not password:
            return False

        auth_user = username + self.user_suffix
        try:
            if self.bind_user:
                # use search filter to find DN of username
                connection.simple_bind_s(self.bind_user, self.bind_password)
                sfilter = self.search_filter % username
                result = connection.search_s(self.base_dn, ldap.SCOPE_SUBTREE, sfilter, attrs)
                if len(result) < 1:
                    return False
                print('auth, ldate res 1:', result)
                auth_user = result[0][0]
                ldap_attrs = result[0][1]
                for key, val in self.attrs.items():
                    if ldap_attrs.get(val):
                        if type(ldap_attrs.get(val)) == list:
                            ldap_contacts[key] = ldap_attrs.get(val)[0]
                        else:
                            ldap_contacts[key] = ldap_attrs.get(val)
                    else:
                        ldap_contacts[key] = val
            connection.simple_bind_s(auth_user, password)

        except ldap.INVALID_CREDENTIALS:
            return False
        except (ldap.SERVER_DOWN, ldap.INVALID_DN_SYNTAX) as err:
            logger.warn("%s", err)
            return None
        if self.import_user:
            connection = db.connect()
            cursor = connection.cursor(db.DictCursor)
            if user_exists(username, cursor):
                logger.info("user %s already exists, updating from ldap", username)
                update_user(username, ldap_contacts, cursor)
            else:
                logger.info("user %s does not exists. importing.", username)
                import_user(username, ldap_contacts, cursor)
            connection.commit()
            cursor.close()
            connection.close()

        return True

    def ldap_change_passwd(self, username, oldpass, newpass):
        if self.cert_path:
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.cert_path)

        connection = ldap.initialize(self.ldap_url)
        connection.set_option(ldap.OPT_REFERRALS, 0)
        attrs = ['dn'] + list(self.attrs.values())
        ldap_contacts = {}

        if not oldpass:
            return False

        auth_user = username + self.user_suffix
        try:
            if self.bind_user:
                # use search filter to find DN of username
                connection.simple_bind_s(self.bind_user, self.bind_password)
                sfilter = self.search_filter % username
                result = connection.search_s(self.base_dn, ldap.SCOPE_SUBTREE, sfilter, attrs)
                if len(result) < 1:
                    return False
                print('auth, ldate res 1:', result)
                auth_user = result[0][0]
            connection.simple_bind_s(auth_user, oldpass)

        except ldap.INVALID_CREDENTIALS:
            return False
        except (ldap.SERVER_DOWN, ldap.INVALID_DN_SYNTAX) as err:
            logger.warn("%s", err)
            return None

        try:
            connection.passwd_s(auth_user, oldpass, newpass)        
        except :
            logger.warn("%s", sys.exc_info()[0])
            return None

        return True

    def update_user_data(self, username, datas):
         logger.info("Update User %s is called", username)
         if self.cert_path:
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.cert_path)

         connection = ldap.initialize(self.ldap_url)
         connection.set_option(ldap.OPT_REFERRALS, 0)
         attrs = ['dn'] + list(self.attrs.values())
         ldap_contacts = {}

         auth_user = username + self.user_suffix
         try:
            if self.bind_user:
                # use search filter to find DN of username
                connection.simple_bind_s(self.bind_user, self.bind_password)

         except ldap.INVALID_CREDENTIALS:
            return False
         except (ldap.SERVER_DOWN, ldap.INVALID_DN_SYNTAX) as err:
            logger.warn("%s", err)
            return None
         ldap_user="uid="+username+",ou=people,"+self.base_dn
         mod_attrs=[]
         for cont in datas:
             ldap_dest = self.attrs.get(cont["mode"])
             logger.info("contact : mode - %s   |    Dest : %s    |    user : %s  |    in %s  ", cont["mode"], cont["destination"], cont["user"], ldap_dest)
             if ldap_dest == cont["destination"]:
                 logger.info("mode %s not updated, ldap %s remain not changes",cont["mode"],  ldap_dest)
                 continue
             mod_attrs.append((ldap.MOD_REPLACE, ldap_dest, [cont["destination"].encode("utf-8")]))
         if len(mod_attrs)>0:
             try:
                 connection.modify_s(ldap_user, mod_attrs)
             except :
                 logger.warn("Error in LDAP update : %s", sys.exc_info())
                 return None
         return True


    def debug_auth(self, username, password):
        return True
