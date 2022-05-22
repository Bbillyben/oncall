# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

from falcon import HTTPNotFound, HTTPBadRequest, HTTPUnauthorized, HTTP_201
from ... import db
from ...auth import login_required, check_user_auth, auth_manager
# from ...auth.modules import ldap_pass
from ...utils import load_json_body
import logging

logger = logging.getLogger(__name__)

columns = {'team': '`team_id` = (SELECT `id` FROM `team` WHERE `name` = %s)',
           'mode': '`mode_id` = (SELECT `id` FROM `contact_mode` WHERE `name` = %s)',
           'type': '`type_id` = (SELECT `id` FROM `notification_type` WHERE `name` = %s)',
           'time_before': '`time_before` = %s',
           'only_if_involved': '`only_if_involved` = %s'}


@login_required
def on_put(req, resp, user_name):
    logger.info(' Password change asked for user name %s', user_name)
    data = load_json_body(req)
    auth_pass = auth_manager.changePassword(user_name, data['old'], data['new'])
    if auth_pass:
        logger.info('Password change success')
    else:
        logger.warning("Failed to authenticate user : %s", user_name)
        raise HTTPUnauthorized('Authentication failure', 'bad login credentials', '')
    resp.status = HTTP_201


@login_required
def on_get(req, resp, user_name):
    print("get on password")